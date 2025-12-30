"""Tests pour l'idempotence via tx_id."""

import pytest
from app.utils import compute_hash


def test_tx_id_uniqueness_same_inputs():
    """Teste que les mêmes inputs donnent le même tx_id."""
    from datetime import datetime

    params = (
        1,  # channel_id
        "ffvl",  # provider_id
        "67",  # station_id
        datetime(2025, 1, 1, 12, 0, 0),  # measurement_at
        "Station Test, vent moyen 15 km/h",  # rendered_text
        "piper",  # engine_id
        "fr_FR-siwis-medium",  # voice_id
        {},  # voice_params
        0,  # offset_seconds
    )

    tx_id_1 = compute_hash(*params)
    tx_id_2 = compute_hash(*params)

    assert tx_id_1 == tx_id_2


def test_tx_id_different_for_different_inputs():
    """Teste que des inputs différents donnent des tx_id différents."""
    from datetime import datetime

    base_params = [
        1,
        "ffvl",
        "67",
        datetime(2025, 1, 1, 12, 0, 0),
        "Station Test, vent moyen 15 km/h",
        "piper",
        "fr_FR-siwis-medium",
        {},
        0,
    ]

    tx_id_1 = compute_hash(*base_params)

    # Changer le texte rendu
    params_2 = base_params.copy()
    params_2[4] = "Station Test, vent moyen 16 km/h"
    tx_id_2 = compute_hash(*params_2)

    assert tx_id_1 != tx_id_2

    # Changer l'offset
    params_3 = base_params.copy()
    params_3[8] = 1200
    tx_id_3 = compute_hash(*params_3)

    assert tx_id_1 != tx_id_3


def test_tx_id_different_for_different_measurement_time():
    """Teste que des measurement_at différents donnent des tx_id différents."""
    from datetime import datetime, timedelta

    base_time = datetime(2025, 1, 1, 12, 0, 0)

    params_1 = (1, "ffvl", "67", base_time, "text", "piper", "voice", {}, 0)
    params_2 = (
        1,
        "ffvl",
        "67",
        base_time + timedelta(minutes=1),
        "text",
        "piper",
        "voice",
        {},
        0,
    )

    tx_id_1 = compute_hash(*params_1)
    tx_id_2 = compute_hash(*params_2)

    assert tx_id_1 != tx_id_2


def test_tx_id_hash_is_stable():
    """Teste que le hash est stable (pas aléatoire)."""
    params = (1, 2, 3, "test")

    # Appeler plusieurs fois
    hashes = [compute_hash(*params) for _ in range(10)]

    # Tous les hashes doivent être identiques
    assert len(set(hashes)) == 1
