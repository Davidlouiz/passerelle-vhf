"""
Abstraction pour les providers de données météo.

Tous les providers doivent implémenter cette interface.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from datetime import datetime
from dataclasses import dataclass


@dataclass
class Measurement:
    """Mesure météo normalisée."""
    measurement_at: datetime  # UTC
    wind_avg_kmh: float
    wind_max_kmh: float
    wind_min_kmh: Optional[float] = None
    
    def to_dict(self) -> dict:
        """Convertit en dictionnaire."""
        return {
            "measurement_at": self.measurement_at.isoformat(),
            "wind_avg_kmh": self.wind_avg_kmh,
            "wind_max_kmh": self.wind_max_kmh,
            "wind_min_kmh": self.wind_min_kmh
        }


@dataclass
class StationInfo:
    """Informations sur une station."""
    provider_id: str
    station_id: str
    station_name: str
    visual_url: Optional[str] = None


class WeatherProvider(ABC):
    """Interface abstraite pour tous les providers météo."""
    
    @property
    @abstractmethod
    def provider_id(self) -> str:
        """Identifiant unique du provider (ex: 'ffvl', 'openwindmap')."""
        pass
    
    @abstractmethod
    def resolve_station_from_url(self, url: str) -> StationInfo:
        """
        Extrait l'ID de station depuis une URL visuelle.
        
        Args:
            url: URL visuelle de la balise (ex: https://www.balisemeteo.com/balise.php?idBalise=67)
        
        Returns:
            StationInfo avec provider_id, station_id et station_name
        
        Raises:
            ValidationError si l'URL ne peut pas être parsée
        """
        pass
    
    @abstractmethod
    async def fetch_measurement(self, station_id: str) -> Optional[Measurement]:
        """
        Récupère la dernière mesure pour une station.
        
        Args:
            station_id: ID de la station
        
        Returns:
            Measurement ou None si indisponible
        
        Raises:
            ProviderError en cas d'erreur API
        """
        pass
    
    @abstractmethod
    async def fetch_measurements_bulk(self, station_ids: List[str]) -> Dict[str, Optional[Measurement]]:
        """
        Récupère les mesures pour plusieurs stations en une seule requête.
        
        Args:
            station_ids: Liste des IDs de stations
        
        Returns:
            Dictionnaire {station_id: Measurement ou None}
        
        Raises:
            ProviderError en cas d'erreur API
        """
        pass
    
    def requires_credentials(self) -> bool:
        """Indique si le provider requiert des identifiants."""
        return False
    
    def set_credentials(self, credentials: dict):
        """
        Configure les identifiants du provider.
        
        Args:
            credentials: Dictionnaire d'identifiants (ex: {"api_key": "..."})
        """
        pass
