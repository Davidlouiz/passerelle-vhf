"""
Router pour l'historique des transmissions.

Endpoints pour consulter et filtrer l'historique des émissions.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_

from app.database import get_db
from app.models import TxHistory, Channel
from app.dependencies import get_current_user

router = APIRouter()


@router.get("/history")
def get_tx_history(
    channel_id: Optional[int] = Query(None, description="Filtrer par canal"),
    status: Optional[str] = Query(
        None, description="Filtrer par statut (PENDING/SENT/FAILED/ABORTED)"
    ),
    mode: Optional[str] = Query(
        None, description="Filtrer par mode (SCHEDULED/MANUAL_TEST)"
    ),
    start_date: Optional[str] = Query(None, description="Date de début (ISO format)"),
    end_date: Optional[str] = Query(None, description="Date de fin (ISO format)"),
    limit: int = Query(100, ge=1, le=500, description="Nombre de résultats"),
    offset: int = Query(0, ge=0, description="Offset pour pagination"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Récupère l'historique des transmissions avec filtres optionnels.

    Args:
        channel_id: Filtrer par ID de canal
        status: Filtrer par statut
        mode: Filtrer par mode
        start_date: Date de début (ISO)
        end_date: Date de fin (ISO)
        limit: Nombre max de résultats
        offset: Offset pour pagination

    Returns:
        Liste des transmissions avec infos canal
    """
    # Construire la requête de base
    query = db.query(TxHistory).join(Channel, TxHistory.channel_id == Channel.id)

    # Appliquer les filtres
    filters = []

    if channel_id is not None:
        filters.append(TxHistory.channel_id == channel_id)

    if status:
        filters.append(TxHistory.status == status.upper())

    if mode:
        filters.append(TxHistory.mode == mode.upper())

    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            filters.append(TxHistory.created_at >= start_dt)
        except ValueError:
            pass  # Ignorer date invalide

    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            filters.append(TxHistory.created_at <= end_dt)
        except ValueError:
            pass

    if filters:
        query = query.filter(and_(*filters))

    # Compter le total
    total = query.count()

    # Récupérer les résultats paginés
    tx_records = (
        query.order_by(desc(TxHistory.created_at)).offset(offset).limit(limit).all()
    )

    # Formater les résultats
    results = []
    for tx in tx_records:
        channel = db.query(Channel).filter_by(id=tx.channel_id).first()

        results.append(
            {
                "id": tx.id,
                "tx_id": tx.tx_id,
                "channel_id": tx.channel_id,
                "channel_name": channel.name if channel else "Canal supprimé",
                "mode": tx.mode,
                "status": tx.status,
                "created_at": tx.created_at.isoformat() if tx.created_at else None,
                "sent_at": tx.sent_at.isoformat() if tx.sent_at else None,
                "planned_at": tx.planned_at.isoformat() if tx.planned_at else None,
                "measurement_at": tx.measurement_at.isoformat()
                if tx.measurement_at
                else None,
                "rendered_text": tx.rendered_text,
                "error_message": tx.error_message,
                "station_id": tx.station_id,
                "offset_seconds": tx.offset_seconds,
            }
        )

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": results,
    }


@router.get("/stats")
def get_tx_stats(
    hours: int = Query(24, ge=1, le=168, description="Nombre d'heures à analyser"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Récupère des statistiques sur les transmissions.

    Args:
        hours: Nombre d'heures dans le passé à analyser

    Returns:
        Stats par canal et par statut
    """
    since = datetime.utcnow() - timedelta(hours=hours)

    # Récupérer toutes les TX depuis la date
    tx_records = db.query(TxHistory).filter(TxHistory.created_at >= since).all()

    # Stats globales
    stats = {
        "total": len(tx_records),
        "by_status": {},
        "by_channel": {},
        "by_mode": {},
    }

    # Compter par statut
    for status_value in ["SENT", "FAILED", "ABORTED", "PENDING"]:
        count = sum(1 for tx in tx_records if tx.status == status_value)
        stats["by_status"][status_value] = count

    # Compter par mode
    for mode_value in ["SCHEDULED", "MANUAL_TEST"]:
        count = sum(1 for tx in tx_records if tx.mode == mode_value)
        stats["by_mode"][mode_value] = count

    # Compter par canal
    channels = db.query(Channel).all()
    for channel in channels:
        count = sum(1 for tx in tx_records if tx.channel_id == channel.id)
        if count > 0:
            stats["by_channel"][channel.name] = {
                "total": count,
                "sent": sum(
                    1
                    for tx in tx_records
                    if tx.channel_id == channel.id and tx.status == "SENT"
                ),
                "failed": sum(
                    1
                    for tx in tx_records
                    if tx.channel_id == channel.id and tx.status == "FAILED"
                ),
            }

    return stats


@router.delete("/history/{tx_id}")
def delete_tx_record(
    tx_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Supprime un enregistrement de transmission.

    Args:
        tx_id: ID de l'enregistrement

    Returns:
        Message de confirmation
    """
    tx = db.query(TxHistory).filter_by(id=tx_id).first()

    if not tx:
        return {"error": "Enregistrement non trouvé"}, 404

    db.delete(tx)
    db.commit()

    return {"message": "Enregistrement supprimé"}
