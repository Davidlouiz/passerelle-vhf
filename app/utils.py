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
        measurement_at: Timestamp de la mesure (naïf UTC ou aware UTC)
        period_seconds: Période de validité en secondes

    Returns:
        True si périmée, False sinon
    """
    # Normaliser en UTC naïf pour comparaison avec utcnow()
    if measurement_at.tzinfo is not None:
        # Convertir aware UTC → naïf UTC
        measurement_at = measurement_at.replace(tzinfo=None)

    age_seconds = (datetime.utcnow() - measurement_at).total_seconds()
    return age_seconds > period_seconds


def round_to_int(value: float) -> int:
    """Arrondit un float à l'entier le plus proche."""
    return round(value)


def compute_tx_id(
    channel_id: int,
    provider_id: str,
    station_id: int,
    measurement_at: datetime,
    rendered_text: str,
    engine_id: str,
    voice_id: str,
    voice_params: dict,
    offset_seconds: int,
) -> str:
    """
    Calcule un tx_id unique pour une transmission.

    Utilisé pour l'idempotence (empêche les duplications).

    Args:
        channel_id: ID du canal
        provider_id: ID du provider (ffvl, openwindmap)
        station_id: ID de la station
        measurement_at: Timestamp de la mesure
        rendered_text: Texte rendu depuis le template
        engine_id: ID du moteur TTS
        voice_id: ID de la voix
        voice_params: Paramètres de la voix
        offset_seconds: Offset de planification

    Returns:
        Hash SHA256 unique
    """
    return compute_hash(
        channel_id,
        provider_id,
        station_id,
        measurement_at,
        rendered_text,
        engine_id,
        voice_id,
        voice_params,
        offset_seconds,
    )
