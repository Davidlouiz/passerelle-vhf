"""
Moteur TTS Piper.

Synthèse vocale hors ligne avec Piper (https://github.com/rhasspy/piper).
"""

from pathlib import Path
from typing import List, Dict, Optional
import json
import wave

try:
    from piper import PiperVoice
except ImportError:
    PiperVoice = None

from app.tts import TTSEngine, Voice
from app.exceptions import TTSError


class PiperEngine(TTSEngine):
    """Moteur TTS utilisant Piper."""

    def __init__(self, models_dir: Optional[Path] = None):
        """
        Initialise le moteur Piper.

        Args:
            models_dir: Répertoire contenant les modèles .onnx (défaut: data/tts_models/)
        """
        if models_dir is None:
            from app.database import DATA_DIR

            models_dir = DATA_DIR / "tts_models"

        self.models_dir = Path(models_dir)
        self.models_dir.mkdir(parents=True, exist_ok=True)

        # Découvrir les voix disponibles
        self._voices = self._discover_voices()

    @property
    def engine_id(self) -> str:
        return "piper"

    @property
    def engine_version(self) -> str:
        """Récupère la version de Piper installée."""
        try:
            import piper

            return getattr(piper, "__version__", "1.3.0")
        except Exception:
            return "unknown"

    def _discover_voices(self) -> List[Voice]:
        """Découvre les voix disponibles dans models_dir."""
        voices = []

        # Voix françaises par défaut connues
        known_voices = [
            {
                "id": "fr_FR-siwis-medium",
                "label": "Siwis (Féminine, Claire) - Medium",
                "languages": ["fr"],
                "file": "fr_FR-siwis-medium.onnx",
            },
            {
                "id": "fr_FR-tom-medium",
                "label": "Tom (Masculine, Grave) - Medium",
                "languages": ["fr"],
                "file": "fr_FR-tom-medium.onnx",
            },
            {
                "id": "fr_FR-upmc-medium",
                "label": "UPMC (Neutre, Professionnelle) - Medium",
                "languages": ["fr"],
                "file": "fr_FR-upmc-medium.onnx",
            },
            {
                "id": "fr_FR-gilles-low",
                "label": "Gilles (Masculine, Rapide) - Low",
                "languages": ["fr"],
                "file": "fr_FR-gilles-low.onnx",
            },
            {
                "id": "fr_FR-siwis-low",
                "label": "Siwis (Féminine, Claire, Rapide) - Low",
                "languages": ["fr"],
                "file": "fr_FR-siwis-low.onnx",
            },
        ]

        for voice_info in known_voices:
            model_path = self.models_dir / voice_info["file"]
            if model_path.exists():
                voices.append(
                    Voice(
                        voice_id=voice_info["id"],
                        label=voice_info["label"],
                        languages=voice_info["languages"],
                        engine_id=self.engine_id,
                    )
                )

        return voices

    def list_voices(self) -> List[Voice]:
        """Liste les voix Piper disponibles."""
        return self._voices

    def synthesize(
        self, text: str, voice_id: str, output_path: str, params: Optional[Dict] = None
    ) -> str:
        """
        Synthétise un texte avec Piper (API Python).

        Utilise piper-tts avec synthesize_wav() qui nécessite un objet wave.
        """
        if PiperVoice is None:
            raise TTSError(
                "piper-tts n'est pas installé. Installez avec: pip install piper-tts"
            )

        # Vérifier que la voix existe
        model_file = f"{voice_id}.onnx"
        model_path = self.models_dir / model_file
        config_path = self.models_dir / f"{voice_id}.onnx.json"

        if not model_path.exists():
            raise TTSError(f"Modèle Piper non trouvé: {model_path}")

        if not config_path.exists():
            raise TTSError(f"Config Piper non trouvée: {config_path}")

        try:
            # Charger le modèle
            voice = PiperVoice.load(str(model_path), config_path=str(config_path))

            # Synthétiser dans un fichier WAV
            with wave.open(output_path, "wb") as wav_file:
                voice.synthesize_wav(text, wav_file)

            # Vérifier que le fichier a été créé
            if not Path(output_path).exists():
                raise TTSError(f"Piper n'a pas généré le fichier audio: {output_path}")

            return output_path

        except Exception as e:
            raise TTSError(f"Erreur lors de la synthèse Piper: {e}")

    def get_model_version(self, voice_id: str) -> str:
        """
        Retourne la version du modèle.

        Pour Piper, on utilise une combinaison de la version Piper + nom du fichier modèle.
        """
        model_file = f"{voice_id}.onnx"
        model_path = self.models_dir / model_file

        if model_path.exists():
            # Utiliser la taille du fichier + mtime comme "version"
            stat = model_path.stat()
            return f"{stat.st_size}_{int(stat.st_mtime)}"

        return "unknown"
