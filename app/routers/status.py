"""Router pour le statut système."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import SystemSettings, Channel

router = APIRouter()


@router.get("")
def get_system_status(db: Session = Depends(get_db)):
    """Retourne le statut global du système."""
    settings = db.query(SystemSettings).filter_by(id=1).first()

    # Compter les canaux actifs
    active_channels_count = db.query(Channel).filter_by(is_enabled=True).count()
    total_channels_count = db.query(Channel).count()

    return {
        "master_enabled": settings.master_enabled if settings else False,
        "active_channels": active_channels_count,
        "total_channels": total_channels_count,
        "poll_interval_seconds": settings.poll_interval_seconds if settings else 60,
        "tx_lock_active": False,  # TODO: implémenter vrai état du verrou
        "runner_status": "unknown",  # TODO: implémenter vrai statut du runner
    }
