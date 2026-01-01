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
    wind_direction: Optional[float] = None  # Degrés (0-359)

    def to_dict(self) -> dict:
        """Convertit en dictionnaire."""
        return {
            "measurement_at": self.measurement_at.isoformat(),
            "wind_avg_kmh": self.wind_avg_kmh,
            "wind_max_kmh": self.wind_max_kmh,
            "wind_min_kmh": self.wind_min_kmh,
            "wind_direction": self.wind_direction,
        }

    @property
    def wind_direction_cardinal(self) -> str:
        """Direction cardinale (16 directions) - version affichage."""
        if self.wind_direction is None:
            return "N/A"
        directions = [
            "N",
            "NNE",
            "NE",
            "ENE",
            "E",
            "ESE",
            "SE",
            "SSE",
            "S",
            "SSO",
            "SO",
            "OSO",
            "O",
            "ONO",
            "NO",
            "NNO",
        ]
        index = round(self.wind_direction / 22.5) % 16
        return directions[index]

    @property
    def wind_direction_name(self) -> str:
        """Direction en toutes lettres - version affichage visuel."""
        if self.wind_direction is None:
            return "variable"
        names = [
            "Nord",
            "Nord-Nord-Est",
            "Nord-Est",
            "Est-Nord-Est",
            "Est",
            "Est-Sud-Est",
            "Sud-Est",
            "Sud-Sud-Est",
            "Sud",
            "Sud-Sud-Ouest",
            "Sud-Ouest",
            "Ouest-Sud-Ouest",
            "Ouest",
            "Ouest-Nord-Ouest",
            "Nord-Ouest",
            "Nord-Nord-Ouest",
        ]
        index = round(self.wind_direction / 22.5) % 16
        return names[index]

    @property
    def wind_direction_tts(self) -> str:
        """Direction en toutes lettres - version optimisée pour TTS."""
        if self.wind_direction is None:
            return "variable"
        # Utilise "Este" et "Oueste" pour meilleure prononciation TTS
        names = [
            "Nord",
            "Nord-Nord-Este",
            "Nord-Este",
            "Este-Nord-Este",
            "Este",
            "Este-Sud-Este",
            "Sud-Este",
            "Sud-Sud-Este",
            "Sud",
            "Sud-Sud-Oueste",
            "Sud-Oueste",
            "Oueste-Sud-Oueste",
            "Oueste",
            "Oueste-Nord-Oueste",
            "Nord-Oueste",
            "Nord-Nord-Oueste",
        ]
        index = round(self.wind_direction / 22.5) % 16
        return names[index]


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
    async def fetch_measurements_bulk(
        self, station_ids: List[str]
    ) -> Dict[str, Optional[Measurement]]:
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
