"""
Service de cache TTS.

Gère le cache des fichiers audio synthétisés.
"""

from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models import AudioCache
from app.utils import compute_hash


class TTSCacheService:
    """Service de gestion du cache audio."""

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialise le service de cache.

        Args:
            cache_dir: Répertoire de cache (défaut: data/audio_cache/)
        """
        if cache_dir is None:
            from app.database import DATA_DIR

            cache_dir = DATA_DIR / "audio_cache"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def compute_cache_key(
        self,
        engine_id: str,
        engine_version: str,
        model_version: str,
        voice_id: str,
        voice_params: dict,
        locale: str,
        rendered_text: str,
    ) -> str:
        """
        Calcule la clé de cache pour un audio.

        Returns:
            Hash SHA256 unique
        """
        return compute_hash(
            engine_id,
            engine_version,
            model_version,
            voice_id,
            voice_params,
            locale,
            rendered_text,
        )

    def get_cached_audio(self, db: Session, cache_key: str) -> Optional[str]:
        """
        Récupère un audio depuis le cache.

        Args:
            db: Session DB
            cache_key: Clé de cache

        Returns:
            Chemin du fichier audio si présent, None sinon
        """
        cache_entry = db.query(AudioCache).filter_by(tts_cache_key=cache_key).first()

        if cache_entry:
            # Vérifier que le fichier existe toujours
            audio_path = Path(cache_entry.audio_path)
            if audio_path.exists():
                # Mettre à jour last_used_at
                cache_entry.last_used_at = datetime.utcnow()
                db.commit()
                return str(audio_path)
            else:
                # Fichier supprimé, nettoyer l'entrée DB
                db.delete(cache_entry)
                db.commit()

        return None

    def store_audio(self, db: Session, cache_key: str, audio_path: str, meta: dict):
        """
        Stocke un audio dans le cache.

        Args:
            db: Session DB
            cache_key: Clé de cache
            audio_path: Chemin du fichier audio
            meta: Métadonnées (engine_id, voice_id, text preview, etc.)
        """
        # Vérifier que le fichier existe
        path = Path(audio_path)
        if not path.exists():
            raise FileNotFoundError(f"Fichier audio introuvable: {audio_path}")

        # Créer l'entrée de cache
        cache_entry = AudioCache(
            tts_cache_key=cache_key,
            audio_path=str(audio_path),
            size_bytes=path.stat().st_size,
            meta_json=meta,
            created_at=datetime.utcnow(),
            last_used_at=datetime.utcnow(),
        )

        db.add(cache_entry)
        db.commit()

    def generate_audio_filename(self, cache_key: str) -> Path:
        """
        Génère un nom de fichier pour le cache basé sur la clé.

        Returns:
            Chemin complet du fichier audio
        """
        return self.cache_dir / f"{cache_key}.wav"
