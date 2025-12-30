"""Utilitaires communs."""

import hashlib
import json
from datetime import datetime
from typing import Any


def compute_hash(*args) -> str:
    """
    Calcule un hash SHA256 à partir d'arguments.

    Utilisé pour tx_id et tts_cache_key.
    """
    data = json.dumps(args, sort_keys=True, default=str)
    return hashlib.sha256(data.encode()).hexdigest()


def is_measurement_expired(measurement_at: datetime, period_seconds: int) -> bool:
    """
    Vérifie si une mesure est périmée.

    Args:
        measurement_at: Timestamp de la mesure
        period_seconds: Période de validité en secondes

    Returns:
        True si périmée, False sinon
    """
    age_seconds = (datetime.utcnow() - measurement_at).total_seconds()
    return age_seconds > period_seconds


def round_to_int(value: float) -> int:
    """Arrondit un float à l'entier le plus proche."""
    return round(value)
