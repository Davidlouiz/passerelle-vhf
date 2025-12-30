"""
Provider FFVL (Fédération Française de Vol Libre).

API balisemeteo.com - requiert une clé API.
"""

import re
from typing import Optional, Dict, List
from urllib.parse import urlparse, parse_qs
import httpx

from app.providers import WeatherProvider, Measurement, StationInfo
from app.exceptions import ValidationError, ProviderError


class FFVLProvider(WeatherProvider):
    """Provider pour les balises FFVL."""

    def __init__(self):
        self._api_key: Optional[str] = None
        self._base_url = "https://www.balisemeteo.com"

    @property
    def provider_id(self) -> str:
        return "ffvl"

    def requires_credentials(self) -> bool:
        return True

    def set_credentials(self, credentials: dict):
        """Configure la clé API FFVL."""
        self._api_key = credentials.get("api_key")

    def resolve_station_from_url(self, url: str) -> StationInfo:
        """
        Extrait l'ID de station depuis une URL FFVL.

        Exemples d'URLs supportées:
        - https://www.balisemeteo.com/balise.php?idBalise=67
        - https://www.balisemeteo.com/balise_mob.php?idBalise=123

        Args:
            url: URL visuelle de la balise

        Returns:
            StationInfo avec station_id extrait

        Raises:
            ValidationError si URL invalide
        """
        try:
            parsed = urlparse(url)

            # Vérifier que c'est bien balisemeteo.com
            if "balisemeteo.com" not in parsed.netloc:
                raise ValidationError(f"URL non reconnue comme FFVL: {url}")

            # Extraire le paramètre idBalise
            params = parse_qs(parsed.query)
            id_balise = params.get("idBalise", [None])[0]

            if not id_balise:
                raise ValidationError(
                    f"Paramètre 'idBalise' manquant dans l'URL: {url}"
                )

            # Valider que c'est un entier
            try:
                station_id = str(int(id_balise))
            except ValueError:
                raise ValidationError(
                    f"idBalise invalide (doit être un entier): {id_balise}"
                )

            return StationInfo(
                provider_id=self.provider_id,
                station_id=station_id,
                station_name=f"Balise FFVL {station_id}",  # Sera mis à jour après fetch
                visual_url=url,
            )

        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Erreur lors du parsing de l'URL FFVL: {e}")

    async def fetch_measurement(self, station_id: str) -> Optional[Measurement]:
        """
        Récupère la dernière mesure pour une station FFVL.

        Utilise l'API balisemeteo.com qui nécessite une clé API.
        """
        if not self._api_key:
            raise ProviderError("Clé API FFVL non configurée")

        # L'API FFVL utilise le format: balise.php?idBalise=XX&periode=last&key=API_KEY
        url = f"{self._base_url}/balise.php?idBalise={station_id}&periode=last&key={self._api_key}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)

                if response.status_code == 404:
                    return None  # Station non trouvée

                response.raise_for_status()
                data = response.json()

                return self._parse_measurement(data, station_id)

        except httpx.HTTPError as e:
            raise ProviderError(
                f"Erreur HTTP lors de la récupération des données FFVL: {e}"
            )
        except Exception as e:
            raise ProviderError(f"Erreur lors du parsing des données FFVL: {e}")

    async def fetch_measurements_bulk(
        self, station_ids: List[str]
    ) -> Dict[str, Optional[Measurement]]:
        """
        Récupère les mesures pour plusieurs stations.

        FFVL ne semble pas avoir d'endpoint bulk, donc on fait des appels individuels.
        """
        results = {}
        for station_id in station_ids:
            try:
                results[station_id] = await self.fetch_measurement(station_id)
            except Exception as e:
                # En cas d'erreur sur une station, continuer avec les autres
                results[station_id] = None
        return results

    def _parse_measurement(self, data: dict, station_id: str) -> Optional[Measurement]:
        """
        Parse les données brutes de l'API FFVL en Measurement normalisé.

        Format API FFVL (simplifié):
        {
            "idbalise": "67",
            "nom": "Commes",
            "last_measure": {
                "date": "2024-01-15 14:30:00",
                "vitesse_moy": "15.2",
                "vitesse_max": "22.1",
                "vitesse_min": "10.5"
            }
        }
        """
        try:
            # Vérifier structure de base
            if not isinstance(data, dict):
                return None

            last_measure = data.get("last_measure") or data.get("lastMeasure")
            if not last_measure:
                return None

            # Extraire les données de vent
            wind_avg = last_measure.get("vitesse_moy") or last_measure.get("vitesseMoy")
            wind_max = last_measure.get("vitesse_max") or last_measure.get("vitesseMax")

            if wind_avg is None or wind_max is None:
                return None

            # Convertir la date (format: "YYYY-MM-DD HH:MM:SS" ou ISO)
            date_str = last_measure.get("date") or last_measure.get("timestamp")
            if date_str:
                # Essayer plusieurs formats de date
                try:
                    # Format ISO
                    measurement_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                except ValueError:
                    try:
                        # Format FFVL standard "YYYY-MM-DD HH:MM:SS"
                        measurement_at = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        # Fallback sur now
                        measurement_at = datetime.utcnow()
            else:
                measurement_at = datetime.utcnow()

            # Convertir les vitesses en float (peuvent être des strings)
            return Measurement(
                measurement_at=measurement_at,
                wind_avg_kmh=float(wind_avg),
                wind_max_kmh=float(wind_max),
                wind_min_kmh=float(last_measure.get("vitesse_min") or last_measure.get("vitesseMin"))
                if (last_measure.get("vitesse_min") or last_measure.get("vitesseMin"))
                else None,
            )

        except Exception as e:
            raise ProviderError(f"Erreur lors du parsing de la mesure FFVL: {e}")
