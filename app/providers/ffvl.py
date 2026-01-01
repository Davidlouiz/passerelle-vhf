"""
Provider FFVL (Fédération Française de Vol Libre).

API balisemeteo.com - requiert une clé API.
"""

import re
from datetime import datetime
from typing import Optional, Dict, List
from urllib.parse import urlparse, parse_qs
import httpx
import pytz

from app.providers import WeatherProvider, Measurement, StationInfo
from app.exceptions import ValidationError, ProviderError


class FFVLProvider(WeatherProvider):
    """Provider pour les balises FFVL."""

    def __init__(self):
        self._api_key: Optional[str] = None
        self._base_url = "https://data.ffvl.fr/api"

    @property
    def provider_id(self) -> str:
        return "ffvl"

    def requires_credentials(self) -> bool:
        return True

    def set_credentials(self, credentials: dict):
        """Configure la clé API FFVL."""
        self._api_key = credentials.get("api_key")

    @staticmethod
    async def validate_api_key(api_key: str) -> bool:
        """
        Valide une clé API FFVL en testant un appel à l'endpoint /list.

        Args:
            api_key: Clé API à valider

        Returns:
            True si la clé est valide, False sinon

        Note:
            L'API FFVL retourne toujours un code HTTP 200, même avec une clé invalide.
            Une clé valide retourne un JSON (liste de balises).
            Une clé invalide retourne du HTML avec des messages d'erreur (error#1, error#2, error#3).
        """
        test_url = (
            f"https://data.ffvl.fr/api/?base=balises&r=list&mode=json&key={api_key}"
        )

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(test_url)

                # Tenter de parser en JSON
                try:
                    data = response.json()
                    # Une clé valide retourne une liste de balises
                    return isinstance(data, list) and len(data) > 0
                except Exception:
                    # Si on ne peut pas parser le JSON, c'est du HTML donc clé invalide
                    return False

        except Exception:
            # En cas d'erreur réseau, on considère la clé comme invalide
            return False

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

        Utilise l'API data.ffvl.fr qui retourne du JSON.
        """
        if not self._api_key:
            raise ProviderError("Clé API FFVL non configurée")

        # L'API FFVL: https://data.ffvl.fr/api?base=balises&r=histo&idbalise=XXX&mode=json&key=...
        url = f"{self._base_url}?base=balises&r=histo&idbalise={station_id}&mode=json&key={self._api_key}"

        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(url)

                if response.status_code == 404:
                    return None  # Station non trouvée

                response.raise_for_status()
                data = response.json()

                # Si pas de données, retourner None (station sans mesures récentes)
                if not isinstance(data, list) or len(data) == 0:
                    return None

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

    def _parse_measurement(self, data: list, station_id: str) -> Optional[Measurement]:
        """
        Parse les données JSON de l'API FFVL.

        Format API FFVL:
        [
            {
                "idbalise": "158",
                "date": "2025-12-30 19:31:56",
                "vitesseVentMoy": "25",
                "vitesseVentMax": "35",
                "vitesseVentMin": "15",
                "directVentMoy": "66",
                "temperature": "6",
                ...
            }
        ]
        """
        try:
            # L'API retourne une liste, on prend le premier élément (le plus récent)
            if not isinstance(data, list) or len(data) == 0:
                return None

            last_measure = data[0]

            # Extraire les données de vent
            wind_avg = last_measure.get("vitesseVentMoy")
            wind_max = last_measure.get("vitesseVentMax")

            if wind_avg is None or wind_max is None:
                return None

            # Convertir la date (format: "YYYY-MM-DD HH:MM:SS" en heure locale française)
            date_str = last_measure.get("date")
            if date_str:
                try:
                    # Parser comme datetime naïf puis localiser en Europe/Paris
                    dt_naive = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
                    paris_tz = pytz.timezone("Europe/Paris")
                    dt_paris = paris_tz.localize(dt_naive)
                    # Convertir en UTC
                    measurement_at = dt_paris.astimezone(pytz.UTC)
                except ValueError:
                    measurement_at = datetime.now(pytz.UTC)
            else:
                measurement_at = datetime.now(pytz.UTC)

            # Convertir les vitesses en float (peuvent être des strings)
            return Measurement(
                measurement_at=measurement_at,
                wind_avg_kmh=float(wind_avg),
                wind_max_kmh=float(wind_max),
                wind_min_kmh=float(last_measure.get("vitesseVentMin"))
                if last_measure.get("vitesseVentMin")
                else None,
                wind_direction=float(last_measure.get("directVentMoy"))
                if last_measure.get("directVentMoy")
                else None,
            )

        except Exception as e:
            raise ProviderError(f"Erreur lors du parsing de la mesure FFVL: {e}")
