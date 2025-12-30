"""
Moteur TTS Piper.

Synthèse vocale hors ligne avec Piper (https://github.com/rhasspy/piper).
"""

import subprocess
from pathlib import Path
from typing import List, Dict, Optional
import json

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
            result = subprocess.run(
                ["piper", "--version"], capture_output=True, text=True, timeout=5
            )
            # Parse "piper 1.2.0" -> "1.2.0"
            version = result.stdout.strip().split()[-1] if result.stdout else "unknown"
            return version
        except Exception:
            return "unknown"

    def _discover_voices(self) -> List[Voice]:
        """Découvre les voix disponibles dans models_dir."""
        voices = []

        # Voix françaises par défaut connues
        known_voices = [
            {
                "id": "fr_FR-siwis-medium",
                "label": "Siwis (FR) - Medium",
                "languages": ["fr"],
                "file": "fr_FR-siwis-medium.onnx",
            },
            {
                "id": "fr_FR-tom-medium",
                "label": "Tom (FR) - Medium",
                "languages": ["fr"],
                "file": "fr_FR-tom-medium.onnx",
            },
            {
                "id": "fr_FR-upmc-medium",
                "label": "UPMC (FR) - Medium",
                "languages": ["fr"],
                "file": "fr_FR-upmc-medium.onnx",
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
        Synthétise un texte avec Piper.

        Commande: echo "texte" | piper -m model.onnx -f output.wav
        """
        # Vérifier que la voix existe
        model_file = f"{voice_id}.onnx"
        model_path = self.models_dir / model_file

        if not model_path.exists():
            raise TTSError(f"Modèle Piper non trouvé: {model_path}")

        # Paramètres optionnels
        params = params or {}
        speaker_id = params.get("speaker", None)

        try:
            # Construire la commande Piper
            cmd = ["piper", "--model", str(model_path), "--output_file", output_path]

            if speaker_id is not None:
                cmd.extend(["--speaker", str(speaker_id)])

            # Exécuter Piper avec le texte en stdin
            result = subprocess.run(
                cmd,
                input=text.encode("utf-8"),
                capture_output=True,
                timeout=30,
                check=True,
            )

            # Vérifier que le fichier a été créé
            if not Path(output_path).exists():
                raise TTSError(f"Piper n'a pas généré le fichier audio: {output_path}")

            return output_path

        except subprocess.TimeoutExpired:
            raise TTSError(f"Timeout lors de la synthèse avec Piper (>30s)")
        except subprocess.CalledProcessError as e:
            raise TTSError(f"Erreur Piper: {e.stderr.decode() if e.stderr else str(e)}")
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
