"""Router pour les paramètres système globaux."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SystemSettings
from app.dependencies import get_current_user

router = APIRouter()


class SystemSettingsUpdate(BaseModel):
    """Schéma pour mise à jour des paramètres système."""

    master_enabled: bool = Field(..., description="Activation globale du système")
    poll_interval_seconds: int = Field(
        ..., ge=10, le=600, description="Intervalle de polling (10-600s)"
    )
    inter_announcement_pause_seconds: int = Field(
        ..., ge=0, le=60, description="Pause entre annonces (0-60s)"
    )
    ptt_gpio_pin: int | None = Field(
        None, ge=0, le=40, description="Pin GPIO pour PTT (None = mode mock)"
    )
    ptt_active_level: int = Field(
        ..., ge=0, le=1, description="Niveau actif PTT (0=LOW, 1=HIGH)"
    )
    ptt_lead_ms: int = Field(
        ..., ge=0, le=2000, description="Délai avant audio (0-2000ms)"
    )
    ptt_tail_ms: int = Field(
        ..., ge=0, le=2000, description="Délai après audio (0-2000ms)"
    )


@router.get("")
def get_system_settings(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """
    Récupère les paramètres système actuels.

    Returns:
        Paramètres système complets
    """
    settings = db.query(SystemSettings).filter_by(id=1).first()

    if not settings:
        # Créer les paramètres par défaut si inexistants
        settings = SystemSettings(
            id=1,
            master_enabled=False,
            poll_interval_seconds=60,
            inter_announcement_pause_seconds=10,
            ptt_gpio_pin=None,
            ptt_active_level=1,
            ptt_lead_ms=500,
            ptt_tail_ms=500,
            tx_timeout_seconds=30,
        )
        db.add(settings)
        try:
            db.commit()
            db.refresh(settings)
        except Exception:
            # Race condition: un autre thread a déjà créé l'entrée
            db.rollback()
            settings = db.query(SystemSettings).filter_by(id=1).first()

    return {
        "id": settings.id,
        "master_enabled": settings.master_enabled,
        "poll_interval_seconds": settings.poll_interval_seconds,
        "inter_announcement_pause_seconds": settings.inter_announcement_pause_seconds,
        "ptt_gpio_pin": settings.ptt_gpio_pin,
        "ptt_active_level": settings.ptt_active_level,
        "ptt_lead_ms": settings.ptt_lead_ms,
        "ptt_tail_ms": settings.ptt_tail_ms,
        "tx_timeout_seconds": settings.tx_timeout_seconds,
    }


@router.put("")
def update_system_settings(
    data: SystemSettingsUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Met à jour les paramètres système.

    Args:
        data: Nouveaux paramètres

    Returns:
        Paramètres mis à jour
    """
    settings = db.query(SystemSettings).filter_by(id=1).first()

    if not settings:
        # Créer les paramètres si inexistants
        settings = SystemSettings(id=1, tx_timeout_seconds=30)
        db.add(settings)

    # Mettre à jour les valeurs
    settings.master_enabled = data.master_enabled
    settings.poll_interval_seconds = data.poll_interval_seconds
    settings.inter_announcement_pause_seconds = data.inter_announcement_pause_seconds
    settings.ptt_gpio_pin = data.ptt_gpio_pin
    settings.ptt_active_level = data.ptt_active_level
    settings.ptt_lead_ms = data.ptt_lead_ms
    settings.ptt_tail_ms = data.ptt_tail_ms

    try:
        db.commit()
        db.refresh(settings)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la sauvegarde: {str(e)}"
        )

    return {
        "id": settings.id,
        "master_enabled": settings.master_enabled,
        "poll_interval_seconds": settings.poll_interval_seconds,
        "inter_announcement_pause_seconds": settings.inter_announcement_pause_seconds,
        "ptt_gpio_pin": settings.ptt_gpio_pin,
        "ptt_active_level": settings.ptt_active_level,
        "ptt_lead_ms": settings.ptt_lead_ms,
        "ptt_tail_ms": settings.ptt_tail_ms,
        "tx_timeout_seconds": settings.tx_timeout_seconds,
    }
