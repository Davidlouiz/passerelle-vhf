"""
Routes pour la synthèse vocale (TTS).
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List
import hashlib

from app.dependencies import get_current_user
from app.tts.piper_engine import PiperEngine
from app.database import DATA_DIR

router = APIRouter(tags=["tts"])


class VoiceInfo(BaseModel):
    """Information sur une voix TTS."""
    voice_id: str
    label: str
    languages: List[str]
    engine_id: str


class SynthesizeRequest(BaseModel):
    """Requête de synthèse vocale."""
    text: str
    voice_id: str
    
    
class SynthesizeResponse(BaseModel):
    """Réponse avec le chemin du fichier audio."""
    audio_path: str
    audio_url: str


# Instance globale du moteur TTS (initialisée au démarrage de l'app)
_tts_engine: PiperEngine = None  # type: ignore

def init_tts_engine():
    """Initialise le moteur TTS au démarrage de l'application."""
    global _tts_engine
    if _tts_engine is None:
        _tts_engine = PiperEngine()

def get_tts_engine() -> PiperEngine:
    """Récupère l'instance du moteur TTS."""
    global _tts_engine
    if _tts_engine is None:
        init_tts_engine()
    return _tts_engine


@router.get("/voices", response_model=List[VoiceInfo])
async def list_voices(current_user=Depends(get_current_user)):
    """Liste les voix TTS disponibles."""
    engine = get_tts_engine()
    voices = engine.list_voices()
    
    return [
        VoiceInfo(
            voice_id=v.voice_id,
            label=v.label,
            languages=v.languages,
            engine_id=v.engine_id
        )
        for v in voices
    ]


@router.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize_text(
    request: SynthesizeRequest,
    current_user=Depends(get_current_user)
):
    """
    Synthétise un texte en audio.
    
    Génère un fichier audio et retourne l'URL pour l'écouter.
    """
    engine = get_tts_engine()
    
    # Créer un nom de fichier basé sur le hash du texte + voix
    content_hash = hashlib.md5(
        f"{request.text}_{request.voice_id}".encode()
    ).hexdigest()[:12]
    
    # Créer le dossier de cache si nécessaire
    cache_dir = DATA_DIR / "audio_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Nom du fichier
    filename = f"preview_{content_hash}.wav"
    output_path = cache_dir / filename
    
    try:
        # Synthétiser
        engine.synthesize(request.text, request.voice_id, str(output_path))
        
        return SynthesizeResponse(
            audio_path=str(output_path),
            audio_url=f"/api/tts/audio/{filename}"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur de synthèse: {str(e)}")


@router.get("/audio/{filename}")
async def serve_audio(filename: str, current_user=Depends(get_current_user)):
    """Sert un fichier audio synthétisé."""
    # Sécurité : vérifier que le filename ne contient pas de chemins
    if "/" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Nom de fichier invalide")
    
    audio_path = DATA_DIR / "audio_cache" / filename
    
    if not audio_path.exists():
        raise HTTPException(status_code=404, detail="Fichier audio non trouvé")
    
    return FileResponse(
        audio_path,
        media_type="audio/wav",
        filename=filename
    )
