"""
Gestionnaire de providers.

Centralise l'accès aux différents providers météo.
"""

from typing import Dict, Optional
from sqlalchemy.orm import Session

from app.providers import WeatherProvider
from app.providers.ffvl import FFVLProvider
from app.providers.openwindmap import OpenWindMapProvider
from app.models import ProviderCredential


class ProviderManager:
    """Gère les providers météo disponibles."""

    def __init__(self):
        self._providers: Dict[str, WeatherProvider] = {}
        self._register_providers()

    def _register_providers(self):
        """Enregistre tous les providers disponibles."""
        # Provider FFVL
        self._providers["ffvl"] = FFVLProvider()

        # Provider OpenWindMap
        self._providers["openwindmap"] = OpenWindMapProvider()

    def get_provider(self, provider_id: str) -> Optional[WeatherProvider]:
        """Récupère un provider par son ID."""
        return self._providers.get(provider_id)

    def list_providers(self) -> Dict[str, dict]:
        """Liste tous les providers disponibles."""
        result = {}
        for provider_id, provider in self._providers.items():
            result[provider_id] = {
                "id": provider_id,
                "requires_credentials": provider.requires_credentials(),
            }
        return result

    def load_credentials(self, db: Session):
        """
        Charge les credentials depuis la DB et les configure dans les providers.

        Args:
            db: Session de base de données
        """
        credentials = db.query(ProviderCredential).all()

        for cred in credentials:
            provider = self._providers.get(cred.provider_id)
            if provider and provider.requires_credentials():
                provider.set_credentials(cred.credentials_json)


# Instance globale du gestionnaire
provider_manager = ProviderManager()
