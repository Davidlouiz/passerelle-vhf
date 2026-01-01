"""Router pour le statut système."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime, timedelta
import subprocess
import os
import pytz

from app.database import get_db
from app.models import SystemSettings, Channel, ChannelRuntime, TxHistory

router = APIRouter()


def format_utc_datetime(dt) -> str:
    """
    Convertit un datetime (naïf ou aware) en ISO string avec timezone Z.

    Args:
        dt: datetime en UTC (naïf ou aware) ou None

    Returns:
        String ISO 8601 avec 'Z' ou None
    """
    if dt is None:
        return None

    # SQLite retourne des datetimes naïfs même avec timezone=True
    # Il faut forcer la timezone UTC
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)

    # Convertir en ISO et remplacer +00:00 par Z
    iso_str = dt.isoformat()
    return iso_str.replace("+00:00", "Z")


def check_runner_status() -> str:
    """
    Vérifie si le processus runner est en cours d'exécution.

    Returns:
        "running" si le runner est actif, "stopped" sinon
    """
    try:
        result = subprocess.run(
            ["pgrep", "-f", "python.*app.runner"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        return "running" if result.returncode == 0 else "stopped"
    except Exception:
        return "unknown"


@router.get("")
def get_system_status(db: Session = Depends(get_db)):
    """Retourne le statut global du système."""
    settings = db.query(SystemSettings).filter_by(id=1).first()

    # Compter les canaux actifs
    active_channels_count = db.query(Channel).filter_by(is_enabled=True).count()
    total_channels_count = db.query(Channel).count()

    # Stats TX sur 24h
    since_24h = datetime.utcnow() - timedelta(hours=24)
    tx_24h = db.query(TxHistory).filter(TxHistory.created_at >= since_24h).all()

    tx_stats = {
        "total": len(tx_24h),
        "sent": sum(1 for tx in tx_24h if tx.status == "SENT"),
        "failed": sum(1 for tx in tx_24h if tx.status == "FAILED"),
        "aborted": sum(1 for tx in tx_24h if tx.status == "ABORTED"),
        "pending": sum(1 for tx in tx_24h if tx.status == "PENDING"),
    }

    # TX par canal (dernières 24h)
    channels_stats = []
    channels = db.query(Channel).all()
    for channel in channels:
        channel_tx = [tx for tx in tx_24h if tx.channel_id == channel.id]
        runtime = db.query(ChannelRuntime).filter_by(channel_id=channel.id).first()

        channels_stats.append(
            {
                "id": channel.id,
                "name": channel.name,
                "is_enabled": channel.is_enabled,
                "tx_count_24h": len(channel_tx),
                "last_measurement_at": format_utc_datetime(runtime.last_measurement_at)
                if runtime and runtime.last_measurement_at
                else None,
                "next_tx_at": format_utc_datetime(runtime.next_tx_at)
                if runtime and runtime.next_tx_at
                else None,
                "last_error": runtime.last_error if runtime else None,
            }
        )

    # Dernières TX (10 plus récentes)
    recent_tx = db.query(TxHistory).order_by(desc(TxHistory.sent_at)).limit(10).all()

    recent_tx_list = []
    for tx in recent_tx:
        channel = db.query(Channel).filter_by(id=tx.channel_id).first()
        recent_tx_list.append(
            {
                "id": tx.id,
                "channel_name": channel.name if channel else "Canal supprimé",
                "status": tx.status,
                "mode": tx.mode,
                "created_at": format_utc_datetime(tx.created_at),
                "sent_at": format_utc_datetime(tx.sent_at),
                "error_message": tx.error_message,
            }
        )

    return {
        "master_enabled": settings.master_enabled if settings else False,
        "active_channels": active_channels_count,
        "total_channels": total_channels_count,
        "poll_interval_seconds": settings.poll_interval_seconds if settings else 60,
        "tx_lock_active": False,  # TODO: implémenter vrai état du verrou
        "runner_status": check_runner_status(),
        "tx_stats_24h": tx_stats,
        "channels_stats": channels_stats,
        "recent_tx": recent_tx_list,
    }


@router.post("/runner/start")
def start_runner():
    """Démarre le processus runner."""
    try:
        # Vérifier si déjà en cours
        status = check_runner_status()
        if status == "running":
            raise HTTPException(
                status_code=400, detail="Le runner est déjà en cours d'exécution"
            )

        # Déterminer le chemin Python à utiliser
        venv_python = "/home/david/git/Passerelle VHF/venv/bin/python"
        python_cmd = venv_python if os.path.exists(venv_python) else "python3"

        # Démarrer le runner en arrière-plan
        subprocess.Popen(
            [python_cmd, "-m", "app.runner"],
            cwd="/home/david/git/Passerelle VHF",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )

        return {"status": "success", "message": "Runner démarré"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur au démarrage du runner: {str(e)}"
        )


@router.post("/runner/stop")
def stop_runner():
    """Arrête le processus runner."""
    try:
        # Vérifier si en cours
        status = check_runner_status()
        if status == "stopped":
            raise HTTPException(
                status_code=400, detail="Le runner n'est pas en cours d'exécution"
            )

        # Arrêter le runner
        result = subprocess.run(
            ["pkill", "-f", "python.*app.runner"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode not in [0, 1]:  # 1 = pas de processus trouvé
            raise HTTPException(
                status_code=500, detail="Erreur lors de l'arrêt du runner"
            )

        return {"status": "success", "message": "Runner arrêté"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur à l'arrêt du runner: {str(e)}"
        )
