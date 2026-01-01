"""
Provider OpenWindMap (API Pioupiou).

API publique sans authentification.
"""

import re
from typing import Optional, Dict, List
from urllib.parse import urlparse
from datetime import datetime
import httpx

from app.providers import WeatherProvider, Measurement, StationInfo
from app.exceptions import ValidationError, ProviderError


class OpenWindMapProvider(WeatherProvider):
    """Provider pour OpenWindMap via l'API Pioupiou."""

    def __init__(self):
        self._api_base = "http://api.pioupiou.fr/v1"

    @property
    def provider_id(self) -> str:
        return "openwindmap"

    def resolve_station_from_url(self, url: str) -> StationInfo:
        """
        Extrait l'ID de station depuis une URL OpenWindMap.

        Exemples d'URLs supportées:
        - https://www.openwindmap.org/pioupiou-385
        - https://www.openwindmap.org/windbird-1500
        - https://www.openwindmap.org/PP603
        - https://www.openwindmap.org/WB1234

        Args:
            url: URL visuelle de la balise

        Returns:
            StationInfo avec station_id extrait

        Raises:
            ValidationError si URL invalide
        """
        try:
            parsed = urlparse(url)

            # Vérifier que c'est bien openwindmap.org
            if "openwindmap.org" not in parsed.netloc:
                raise ValidationError(f"URL non reconnue comme OpenWindMap: {url}")

            # Extraire le chemin (ex: /pioupiou-385, /PP603)
            path = parsed.path.strip("/")

            # Pattern 1: xxx-NNNN (ex: pioupiou-385, windbird-1500)
            match = re.match(r"^[a-z]+-(\d+)$", path, re.IGNORECASE)
            if match:
                station_id = match.group(1)
                return StationInfo(
                    provider_id=self.provider_id,
                    station_id=station_id,
                    station_name=f"Station {station_id}",
                    visual_url=url,
                )

            # Pattern 2: PPNNN, WBNNN, MWNNN (ex: PP603, WB1234)
            match = re.match(r"^(PP|WB|MW)(\d+)$", path, re.IGNORECASE)
            if match:
                station_id = match.group(2)
                return StationInfo(
                    provider_id=self.provider_id,
                    station_id=station_id,
                    station_name=f"Station {station_id}",
                    visual_url=url,
                )

            raise ValidationError(f"Format d'URL OpenWindMap non reconnu: {url}")

        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Erreur lors du parsing de l'URL OpenWindMap: {e}")

    async def fetch_measurement(self, station_id: str) -> Optional[Measurement]:
        """
        Récupère la dernière mesure pour une station via l'API Pioupiou.

        Endpoint: GET http://api.pioupiou.fr/v1/live/{station_id}
        """
        url = f"{self._api_base}/live/{station_id}"

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)

                if response.status_code == 404:
                    return None  # Station non trouvée

                response.raise_for_status()
                data = response.json()

                return self._parse_measurement(data)

        except httpx.HTTPError as e:
            raise ProviderError(
                f"Erreur HTTP lors de la récupération des données Pioupiou: {e}"
            )
        except Exception as e:
            raise ProviderError(f"Erreur lors du parsing des données Pioupiou: {e}")

    async def fetch_measurements_bulk(
        self, station_ids: List[str]
    ) -> Dict[str, Optional[Measurement]]:
        """
        Récupère les mesures pour plusieurs stations.

        Utilise l'endpoint /live/all pour récupérer toutes les stations d'un coup,
        puis filtre sur les IDs demandés.
        """
        url = f"{self._api_base}/live/all"

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()

                # Construire un dict station_id -> measurement
                all_measurements = {}
                if isinstance(data, dict) and "data" in data:
                    for station_data in data["data"]:
                        station_id = str(station_data.get("id", ""))
                        try:
                            all_measurements[station_id] = self._parse_measurement(
                                station_data
                            )
                        except:
                            all_measurements[station_id] = None

                # Filtrer sur les IDs demandés
                results = {}
                for station_id in station_ids:
                    results[station_id] = all_measurements.get(station_id)

                return results

        except Exception as e:
            # En cas d'erreur bulk, fallback sur des appels individuels
            results = {}
            for station_id in station_ids:
                try:
                    results[station_id] = await self.fetch_measurement(station_id)
                except:
                    results[station_id] = None
            return results

    def _parse_measurement(self, data: dict) -> Optional[Measurement]:
        """
        Parse les données brutes de l'API Pioupiou en Measurement normalisé.

        Format API Pioupiou v1:
        {
            "data": {
                "id": 385,
                "meta": {...},
                "measurements": {
                    "wind_speed_avg": 15.2,
                    "wind_speed_max": 22.1,
                    "wind_speed_min": 10.5
                },
                "status": {...}
            }
        }

        Ou format bulk:
        {
            "id": 385,
            "measurements": {...},
            "date": "2024-01-15T14:30:00Z"
        }
        """
        try:
            # L'API peut retourner {"data": {...}} pour un seul station
            if "data" in data and isinstance(data["data"], dict):
                data = data["data"]

            measurements = data.get("measurements", {})

            # Vérifier que les données sont présentes
            if not measurements:
                return None

            wind_avg = measurements.get("wind_speed_avg")
            wind_max = measurements.get("wind_speed_max")

            if wind_avg is None or wind_max is None:
                return None

            # Convertir la date (peut être dans data ou measurements)
            date_str = (
                data.get("date") or measurements.get("date") or data.get("measured_at")
            )
            if date_str:
                # Gérer différents formats ISO - convertir en naive UTC
                dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                measurement_at = dt.replace(
                    tzinfo=None
                )  # Retirer la timezone pour cohérence
            else:
                measurement_at = datetime.utcnow()

            return Measurement(
                measurement_at=measurement_at,
                wind_avg_kmh=float(wind_avg),
                wind_max_kmh=float(wind_max),
                wind_min_kmh=float(measurements.get("wind_speed_min"))
                if measurements.get("wind_speed_min")
                else None,
                wind_direction=float(measurements.get("wind_heading"))
                if measurements.get("wind_heading") is not None
                else None,
            )

        except Exception as e:
            raise ProviderError(f"Erreur lors du parsing de la mesure Pioupiou: {e}")
