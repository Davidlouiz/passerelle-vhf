"""
Tests pour le router d'historique des transmissions.
"""

import pytest
from datetime import datetime, timedelta, timezone
from app.database import get_db_session
from app.models import TxHistory, Channel, User
from app.routers.tx_history import get_tx_history, get_tx_stats


def test_get_empty_history():
    """Teste la récupération d'un historique vide."""
    with get_db_session() as db:
        # Nettoyer
        db.query(TxHistory).delete()
        db.commit()

        # Créer un utilisateur factice
        user = {"id": 1, "username": "test"}

        # Récupérer l'historique
        result = get_tx_history(db=db, current_user=user)

        assert result["total"] == 0
        assert len(result["results"]) == 0


def test_get_history_with_data():
    """Teste la récupération d'un historique avec données."""
    with get_db_session() as db:
        # Nettoyer
        db.query(TxHistory).delete()
        db.query(Channel).delete()
        db.commit()

        # Créer un canal
        channel = Channel(
            name="Test Channel",
            provider_id="ffvl",
            station_id=123,
            template_text="Test {wind_avg_kmh}",
            measurement_period_seconds=3600,
            offsets_seconds_json="[0]",
        )
        db.add(channel)
        db.commit()

        # Créer une TX
        now = datetime.now(timezone.utc)
        tx = TxHistory(
            tx_id="test_123",
            channel_id=channel.id,
            mode="SCHEDULED",
            status="SENT",
            created_at=now,
            sent_at=now,
            measurement_at=now - timedelta(minutes=5),
            planned_at=now,
            offset_seconds=0,
            station_id="123",
            rendered_text="Test transmission",
        )
        db.add(tx)
        db.commit()

        # Créer un utilisateur factice
        user = {"id": 1, "username": "test"}

        # Récupérer l'historique
        result = get_tx_history(db=db, current_user=user)

        assert result["total"] == 1
        assert len(result["results"]) == 1
        assert result["results"][0]["channel_name"] == "Test Channel"
        assert result["results"][0]["status"] == "SENT"


def test_filter_by_status():
    """Teste le filtrage par statut."""
    with get_db_session() as db:
        # Nettoyer
        db.query(TxHistory).delete()
        db.query(Channel).delete()
        db.commit()

        # Créer un canal
        channel = Channel(
            name="Test Channel",
            provider_id="ffvl",
            station_id=123,
            template_text="Test",
            measurement_period_seconds=3600,
            offsets_seconds_json="[0]",
        )
        db.add(channel)
        db.commit()

        # Créer plusieurs TX avec différents statuts
        now = datetime.now(timezone.utc)
        for status in ["SENT", "SENT", "FAILED"]:
            tx = TxHistory(
                tx_id=f"test_{status}_{now.timestamp()}",
                channel_id=channel.id,
                mode="SCHEDULED",
                status=status,
                created_at=now,
                measurement_at=now,
                planned_at=now,
                offset_seconds=0,
                station_id="123",
                rendered_text="Test",
            )
            db.add(tx)
        db.commit()

        user = {"id": 1, "username": "test"}

        # Filtrer par SENT
        result = get_tx_history(db=db, current_user=user, status="SENT")
        assert result["total"] == 2

        # Filtrer par FAILED
        result = get_tx_history(db=db, current_user=user, status="FAILED")
        assert result["total"] == 1


def test_pagination():
    """Teste la pagination."""
    with get_db_session() as db:
        # Nettoyer
        db.query(TxHistory).delete()
        db.query(Channel).delete()
        db.commit()

        # Créer un canal
        channel = Channel(
            name="Test Channel",
            provider_id="ffvl",
            station_id=123,
            template_text="Test",
            measurement_period_seconds=3600,
            offsets_seconds_json="[0]",
        )
        db.add(channel)
        db.commit()

        # Créer 25 TX
        now = datetime.now(timezone.utc)
        for i in range(25):
            tx = TxHistory(
                tx_id=f"test_{i}_{now.timestamp()}",
                channel_id=channel.id,
                mode="SCHEDULED",
                status="SENT",
                created_at=now - timedelta(hours=i),
                measurement_at=now,
                planned_at=now,
                offset_seconds=0,
                station_id="123",
                rendered_text=f"Test {i}",
            )
            db.add(tx)
        db.commit()

        user = {"id": 1, "username": "test"}

        # Page 1 (10 premiers)
        result = get_tx_history(db=db, current_user=user, limit=10, offset=0)
        assert result["total"] == 25
        assert len(result["results"]) == 10

        # Page 2 (10 suivants)
        result = get_tx_history(db=db, current_user=user, limit=10, offset=10)
        assert len(result["results"]) == 10

        # Page 3 (5 restants)
        result = get_tx_history(db=db, current_user=user, limit=10, offset=20)
        assert len(result["results"]) == 5


def test_stats():
    """Teste les statistiques."""
    with get_db_session() as db:
        # Nettoyer
        db.query(TxHistory).delete()
        db.query(Channel).delete()
        db.commit()

        # Créer un canal
        channel = Channel(
            name="Test Channel",
            provider_id="ffvl",
            station_id=123,
            template_text="Test",
            measurement_period_seconds=3600,
            offsets_seconds_json="[0]",
        )
        db.add(channel)
        db.commit()

        # Créer des TX avec différents statuts
        now = datetime.now(timezone.utc)
        statuses = ["SENT", "SENT", "SENT", "FAILED", "ABORTED"]

        for i, status in enumerate(statuses):
            tx = TxHistory(
                tx_id=f"test_{i}",
                channel_id=channel.id,
                mode="SCHEDULED",
                status=status,
                created_at=now - timedelta(hours=1),  # Dans les 24h
                measurement_at=now,
                planned_at=now,
                offset_seconds=0,
                station_id="123",
                rendered_text="Test",
            )
            db.add(tx)
        db.commit()

        user = {"id": 1, "username": "test"}

        # Récupérer les stats
        stats = get_tx_stats(hours=24, db=db, current_user=user)

        assert stats["total"] == 5
        assert stats["by_status"]["SENT"] == 3
        assert stats["by_status"]["FAILED"] == 1
        assert stats["by_status"]["ABORTED"] == 1
        assert "Test Channel" in stats["by_channel"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
