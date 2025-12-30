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
                raise ValidationError(f"Paramètre 'idBalise' manquant dans l'URL: {url}")
            
            # Valider que c'est un entier
            try:
                station_id = str(int(id_balise))
            except ValueError:
                raise ValidationError(f"idBalise invalide (doit être un entier): {id_balise}")
            
            return StationInfo(
                provider_id=self.provider_id,
                station_id=station_id,
                station_name=f"Balise FFVL {station_id}",  # Sera mis à jour après fetch
                visual_url=url
            )
            
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(f"Erreur lors du parsing de l'URL FFVL: {e}")
    
    async def fetch_measurement(self, station_id: str) -> Optional[Measurement]:
        """
        Récupère la dernière mesure pour une station FFVL.
        
        TODO: Implémenter l'appel API réel une fois l'endpoint connu.
        Pour l'instant, retourne None.
        """
        if not self._api_key:
            raise ProviderError("Clé API FFVL non configurée")
        
        # TODO: Implémenter l'appel API réel
        # Exemple fictif:
        # url = f"{self._base_url}/api/station/{station_id}/latest?key={self._api_key}"
        # async with httpx.AsyncClient() as client:
        #     response = await client.get(url)
        #     response.raise_for_status()
        #     data = response.json()
        #     return self._parse_measurement(data)
        
        return None
    
    async def fetch_measurements_bulk(self, station_ids: List[str]) -> Dict[str, Optional[Measurement]]:
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
    
    def _parse_measurement(self, data: dict) -> Measurement:
        """
        Parse les données brutes de l'API FFVL en Measurement normalisé.
        
        TODO: Adapter au format réel de l'API FFVL.
        """
        # Exemple fictif - à adapter
        from datetime import datetime
        
        return Measurement(
            measurement_at=datetime.fromisoformat(data["timestamp"]),
            wind_avg_kmh=float(data["wind_avg"]),
            wind_max_kmh=float(data["wind_max"]),
            wind_min_kmh=float(data.get("wind_min"))
        )
