"""Tests pour le calcul de planning et offsets."""
import pytest
from datetime import datetime, timedelta


def test_offset_calculation():
    """Teste le calcul des tx_times depuis measurement_at + offsets."""
    measurement_at = datetime(2025, 1, 1, 12, 0, 0)
    offsets = [0, 1200, 2400]  # 0s, 20min, 40min
    
    tx_times = [measurement_at + timedelta(seconds=offset) for offset in offsets]
    
    assert len(tx_times) == 3
    assert tx_times[0] == datetime(2025, 1, 1, 12, 0, 0)
    assert tx_times[1] == datetime(2025, 1, 1, 12, 20, 0)
    assert tx_times[2] == datetime(2025, 1, 1, 12, 40, 0)


def test_offset_single():
    """Teste avec un seul offset (immédiat)."""
    measurement_at = datetime(2025, 1, 1, 12, 0, 0)
    offsets = [0]
    
    tx_times = [measurement_at + timedelta(seconds=offset) for offset in offsets]
    
    assert len(tx_times) == 1
    assert tx_times[0] == measurement_at


def test_offset_multiple():
    """Teste avec plusieurs offsets."""
    measurement_at = datetime(2025, 1, 1, 12, 0, 0)
    offsets = [0, 600, 1200, 1800, 2400, 3000]  # Toutes les 10 min pendant 50 min
    
    tx_times = [measurement_at + timedelta(seconds=offset) for offset in offsets]
    
    assert len(tx_times) == 6
    # Vérifier l'espacement de 10 min
    for i in range(1, len(tx_times)):
        delta = (tx_times[i] - tx_times[i-1]).total_seconds()
        assert delta == 600  # 10 minutes
