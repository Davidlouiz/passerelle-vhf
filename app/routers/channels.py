"""API Router pour la gestion des canaux."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel
from typing import Optional
import datetime
import json

from app.database import get_db
from app.models import Channel, ChannelRuntime, AuditLog
from app.dependencies import get_current_user
from app.routers.providers import resolve_station, StationResolutionRequest

router = APIRouter()


class ChannelCreate(BaseModel):
    """Création d'un canal."""

    name: str
    station_visual_url: str
    frequency_mhz: float = 0.0  # Pas utilisé, mais gardé pour compatibilité DB
    template_text: str
    engine_id: str = "piper"
    voice_id: str = "fr_FR-siwis-medium"
    voice_params_json: Optional[str] = "{}"
    offsets_seconds_json: str = "[0]"
    measurement_period_seconds: int = 3600
    min_interval_between_tx_seconds: int = 600
    lead_ms: int = 500
    tail_ms: int = 500


class ChannelUpdate(BaseModel):
    """Mise à jour d'un canal."""

    name: Optional[str] = None
    frequency_mhz: Optional[float] = None
    template_text: Optional[str] = None
    voice_id: Optional[str] = None
    voice_params_json: Optional[str] = None
    offsets_seconds_json: Optional[str] = None
    measurement_period_seconds: Optional[int] = None
    min_interval_between_tx_seconds: Optional[int] = None
    lead_ms: Optional[int] = None
    tail_ms: Optional[int] = None


class ChannelResponse(BaseModel):
    """Réponse détaillée d'un canal."""

    id: int
    name: str
    provider_id: str
    station_id: int
    station_visual_url_cache: str
    frequency_mhz: float
    template_text: str
    engine_id: str
    voice_id: str
    voice_params_json: str
    offsets_seconds_json: str
    measurement_period_seconds: int
    min_interval_between_tx_seconds: int
    lead_ms: int
    tail_ms: int
    is_enabled: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        from_attributes = True


@router.get("/", response_model=list[ChannelResponse])
def list_channels(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """Liste tous les canaux."""
    channels = db.query(Channel).all()
    return channels


@router.get("/{channel_id}", response_model=ChannelResponse)
def get_channel(
    channel_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Récupère un canal spécifique."""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()

    if not channel:
        raise HTTPException(status_code=404, detail="Canal non trouvé")

    return channel


@router.post("/", response_model=ChannelResponse)
def create_channel(
    data: ChannelCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Crée un nouveau canal."""

    # Résoudre la station depuis l'URL
    from app.providers.ffvl import FFVLProvider
    from app.providers.openwindmap import OpenWindMapProvider

    url = data.station_visual_url.strip()

    try:
        if "balisemeteo.com" in url or "ffvl" in url.lower():
            provider = FFVLProvider()
            station_info = provider.resolve_station_from_url(url)
            provider_id = station_info.provider_id
            station_id = station_info.station_id
            station_name = station_info.station_name
        elif "openwindmap.org" in url or "pioupiou" in url.lower():
            provider = OpenWindMapProvider()
            station_info = provider.resolve_station_from_url(url)
            provider_id = station_info.provider_id
            station_id = station_info.station_id
            station_name = station_info.station_name
        else:
            raise ValueError("URL non reconnue")
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Impossible de résoudre la station: {str(e)}"
        )

    # Créer le canal
    channel = Channel(
        name=data.name,
        provider_id=provider_id,
        station_id=station_id,
        station_visual_url_cache=url,
        frequency_mhz=data.frequency_mhz,
        template_text=data.template_text,
        engine_id=data.engine_id,
        voice_id=data.voice_id,
        voice_params_json=data.voice_params_json,
        offsets_seconds_json=data.offsets_seconds_json,
        measurement_period_seconds=data.measurement_period_seconds,
        min_interval_between_tx_seconds=data.min_interval_between_tx_seconds,
        lead_ms=data.lead_ms,
        tail_ms=data.tail_ms,
        is_enabled=False,  # Désactivé par défaut
    )
    db.add(channel)
    db.flush()

    # Créer le runtime associé
    runtime = ChannelRuntime(
        channel_id=channel.id,
        last_measurement_at=None,
        next_tx_at=None,
        last_error=None,
    )
    db.add(runtime)

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="CREATE_CHANNEL",
        details_json=f"Canal '{data.name}' créé (provider: {provider_id}, station: {station_id})",
        ip_address="127.0.0.1",
    )
    db.add(audit)

    db.commit()
    db.refresh(channel)

    return channel


@router.put("/{channel_id}", response_model=ChannelResponse)
def update_channel(
    channel_id: int,
    data: ChannelUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Met à jour un canal."""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()

    if not channel:
        raise HTTPException(status_code=404, detail="Canal non trouvé")

    # Mettre à jour les champs fournis
    if data.name is not None:
        channel.name = data.name
    if data.frequency_mhz is not None:
        channel.frequency_mhz = data.frequency_mhz
    if data.template_text is not None:
        channel.template_text = data.template_text
    if data.voice_id is not None:
        channel.voice_id = data.voice_id
    if data.voice_params_json is not None:
        channel.voice_params_json = data.voice_params_json
    if data.offsets_seconds_json is not None:
        channel.offsets_seconds_json = data.offsets_seconds_json
    if data.measurement_period_seconds is not None:
        channel.measurement_period_seconds = data.measurement_period_seconds
    if data.min_interval_between_tx_seconds is not None:
        channel.min_interval_between_tx_seconds = data.min_interval_between_tx_seconds
    if data.lead_ms is not None:
        channel.lead_ms = data.lead_ms
    if data.tail_ms is not None:
        channel.tail_ms = data.tail_ms

    channel.updated_at = datetime.datetime.now(datetime.timezone.utc)

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="UPDATE_CHANNEL",
        details_json=f"Canal '{channel.name}' (ID: {channel_id}) mis à jour",
        ip_address="127.0.0.1",
    )
    db.add(audit)

    db.commit()
    db.refresh(channel)

    return channel


@router.delete("/{channel_id}")
def delete_channel(
    channel_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Supprime un canal."""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()

    if not channel:
        raise HTTPException(status_code=404, detail="Canal non trouvé")

    channel_name = channel.name

    # Supprimer le runtime associé
    runtime = (
        db.query(ChannelRuntime).filter(ChannelRuntime.channel_id == channel_id).first()
    )
    if runtime:
        db.delete(runtime)

    # Supprimer le canal
    db.delete(channel)

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="DELETE_CHANNEL",
        details_json=f"Canal '{channel_name}' (ID: {channel_id}) supprimé",
        ip_address="127.0.0.1",
    )
    db.add(audit)

    db.commit()

    return {"message": "Canal supprimé avec succès"}


@router.post("/{channel_id}/toggle")
def toggle_channel(
    channel_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Active/désactive un canal."""
    channel = db.query(Channel).filter(Channel.id == channel_id).first()

    if not channel:
        raise HTTPException(status_code=404, detail="Canal non trouvé")

    channel.is_enabled = not channel.is_enabled
    channel.updated_at = datetime.datetime.now(datetime.timezone.utc)

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="TOGGLE_CHANNEL",
        details_json=f"Canal '{channel.name}' (ID: {channel_id}) {'activé' if channel.is_enabled else 'désactivé'}",
        ip_address="127.0.0.1",
    )
    db.add(audit)

    db.commit()

    return {
        "message": f"Canal {'activé' if channel.is_enabled else 'désactivé'}",
        "is_enabled": channel.is_enabled,
    }


@router.post("/{channel_id}/preview")
async def preview_channel(
    channel_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Prévisualise une annonce avec de vraies valeurs de la station.
    
    Récupère la dernière mesure, rend le template et génère l'audio.
    """
    from app.services.template import TemplateRenderer
    from app.tts.piper_engine import PiperEngine
    from app.database import DATA_DIR
    import hashlib
    import shutil
    
    # Récupérer le canal
    channel = db.query(Channel).filter(Channel.id == channel_id).first()
    if not channel:
        raise HTTPException(status_code=404, detail="Canal non trouvé")
    
    # Récupérer les credentials du provider
    from app.models import ProviderCredential
    creds = db.query(ProviderCredential).filter(
        ProviderCredential.provider_id == channel.provider_id
    ).first()
    
    # Récupérer le provider
    if channel.provider_id == "ffvl":
        from app.providers.ffvl import FFVLProvider
        if not creds or not creds.credentials_json.get("api_key"):
            raise HTTPException(status_code=400, detail="Clé API FFVL manquante")
        provider = FFVLProvider(api_key=creds.credentials_json["api_key"])
    elif channel.provider_id == "openwindmap":
        from app.providers.openwindmap import OpenWindMapProvider
        provider = OpenWindMapProvider()
    else:
        raise HTTPException(status_code=400, detail=f"Provider inconnu: {channel.provider_id}")
    
    # Récupérer la dernière mesure
    try:
        measurement = await provider.fetch_measurement(channel.station_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur récupération mesure: {str(e)}")
    
    if not measurement:
        raise HTTPException(status_code=404, detail="Aucune mesure disponible")
    
    # Calculer l'âge de la mesure
    now = datetime.datetime.now(datetime.timezone.utc)
    measurement_age = now - measurement.measurement_at
    measurement_age_minutes = int(measurement_age.total_seconds() / 60)
    
    # Préparer les variables pour le template
    template_vars = {
        "station_name": channel.name,  # Utiliser channel.name
        "wind_avg_kmh": round(measurement.wind_avg_kmh),
        "wind_max_kmh": round(measurement.wind_max_kmh),
        "measurement_age_minutes": measurement_age_minutes,
    }
    
    # Rendre le template
    try:
        renderer = TemplateRenderer()
        rendered_text = renderer.render(channel.template_text, template_vars)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur rendu template: {str(e)}")
    
    # Générer l'audio
    try:
        # Créer le nom de fichier basé sur le hash
        content_hash = hashlib.md5(rendered_text.encode()).hexdigest()[:12]
        filename = f"preview_{content_hash}.wav"
        
        # Vérifier le cache
        cache_dir = DATA_DIR / "audio_cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        output_path = cache_dir / filename
        
        was_cached = output_path.exists()
        
        if not was_cached:
            # Générer l'audio
            engine = PiperEngine()
            engine.synthesize(rendered_text, channel.voice_id, str(output_path))
        
        return {
            "rendered_text": rendered_text,
            "audio_url": f"/api/tts/audio/{filename}",
            "measurement": {
                "wind_avg_kmh": measurement.wind_avg_kmh,
                "wind_max_kmh": measurement.wind_max_kmh,
                "measurement_at": measurement.measurement_at.isoformat(),
                "age_minutes": measurement_age_minutes,
            },
            "was_cached": was_cached,
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur génération audio: {str(e)}")
