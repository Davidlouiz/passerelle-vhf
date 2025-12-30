"""
Abstraction pour les moteurs TTS (Text-to-Speech).

Permet de changer de moteur facilement.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class Voice:
    """Informations sur une voix TTS."""
    voice_id: str
    label: str
    languages: List[str]
    engine_id: str


class TTSEngine(ABC):
    """Interface abstraite pour les moteurs TTS."""
    
    @property
    @abstractmethod
    def engine_id(self) -> str:
        """Identifiant unique du moteur (ex: 'piper', 'coqui')."""
        pass
    
    @property
    @abstractmethod
    def engine_version(self) -> str:
        """Version du moteur."""
        pass
    
    @abstractmethod
    def list_voices(self) -> List[Voice]:
        """
        Liste les voix disponibles.
        
        Returns:
            Liste de Voice disponibles
        """
        pass
    
    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice_id: str,
        output_path: str,
        params: Optional[Dict] = None
    ) -> str:
        """
        Synthétise un texte en audio.
        
        Args:
            text: Texte à synthétiser
            voice_id: ID de la voix à utiliser
            output_path: Chemin où sauver le fichier audio
            params: Paramètres optionnels spécifiques au moteur
        
        Returns:
            Chemin du fichier audio généré
        
        Raises:
            TTSError si la synthèse échoue
        """
        pass
    
    @abstractmethod
    def get_model_version(self, voice_id: str) -> str:
        """
        Retourne la version du modèle pour une voix donnée.
        
        Args:
            voice_id: ID de la voix
        
        Returns:
            Version du modèle (pour le cache)
        """
        pass
