"""
Tests de cohérence du texte d'annonce entre preview et transmission réelle.

Vérifie que prepare_announcement_text() produit le même résultat
partout pour garantir la fidélité de l'aperçu.
"""

import pytest
from datetime import datetime, timedelta

from app.models import Channel
from app.providers import Measurement
from app.services.announcement import prepare_announcement_text


def test_prepare_announcement_text_consistency():
    """Le même canal + même mesure = même texte rendu."""
    # Créer un canal mock
    channel = Channel(
        id=1,
        name="Test Balise",
        provider_id="ffvl",
        station_id="123",
        template_text="Balise de {station_name}, {wind_direction_name}, {wind_avg_kmh} kilomètres par heure, {wind_max_kmh} maximum, il y a {measurement_age_minutes} minutes.",
        engine_id="piper",
        voice_id="fr_FR-siwis-medium",
        voice_params_json="{}",
        offsets_seconds_json="[0]",
        measurement_period_seconds=3600,
        is_enabled=True,
    )

    # Créer une mesure mock
    measurement_at = datetime(2026, 1, 1, 12, 0, 0)
    measurement = Measurement(
        measurement_at=measurement_at,
        wind_avg_kmh=23.5,
        wind_max_kmh=37.2,
        wind_min_kmh=18.0,
        wind_direction=225.0,  # Sud-Ouest
    )

    # Appeler deux fois la fonction
    text1 = prepare_announcement_text(channel, measurement)
    text2 = prepare_announcement_text(channel, measurement)

    # Les textes doivent être identiques
    assert text1 == text2

    # Vérifier que le texte contient les bonnes valeurs
    assert "Test Balise" in text1
    assert "Sud-Oueste" in text1  # Direction TTS
    assert "23" in text1 or "24" in text1  # wind_avg arrondi
    assert "37" in text1 or "38" in text1  # wind_max arrondi


def test_measurement_age_calculation():
    """L'âge de la mesure doit être calculé de manière cohérente."""
    channel = Channel(
        id=1,
        name="Test",
        provider_id="ffvl",
        station_id="123",
        template_text="Mesure il y a {measurement_age_minutes} minutes",
        engine_id="piper",
        voice_id="fr_FR-siwis-medium",
        voice_params_json="{}",
        offsets_seconds_json="[0]",
        measurement_period_seconds=3600,
        is_enabled=True,
    )

    # Mesure datant de 5 minutes
    measurement_at = datetime.utcnow() - timedelta(minutes=5)
    measurement = Measurement(
        measurement_at=measurement_at,
        wind_avg_kmh=10.0,
        wind_max_kmh=15.0,
        wind_min_kmh=5.0,
        wind_direction=180.0,
    )

    text = prepare_announcement_text(channel, measurement)

    # Le texte doit contenir "5 minutes" (±1 minute pour la tolérance)
    assert "5 minutes" in text or "4 minutes" in text or "6 minutes" in text


def test_one_minute_pronunciation():
    """Vérifie que '1 minute' utilise 'une' et non 'un'."""
    channel = Channel(
        id=1,
        name="Test",
        provider_id="ffvl",
        station_id="123",
        template_text="il y a {measurement_age_minutes} minutes",
        engine_id="piper",
        voice_id="fr_FR-siwis-medium",
        voice_params_json="{}",
        offsets_seconds_json="[0]",
        measurement_period_seconds=3600,
        is_enabled=True,
    )

    # Mesure datant de ~1 minute
    measurement_at = datetime.utcnow() - timedelta(seconds=65)
    measurement = Measurement(
        measurement_at=measurement_at,
        wind_avg_kmh=10.0,
        wind_max_kmh=15.0,
        wind_min_kmh=5.0,
        wind_direction=180.0,
    )

    text = prepare_announcement_text(channel, measurement)

    # Doit contenir "une minutes" (pas "1 minutes")
    assert "une minutes" in text or "une minute" in text
    assert "1 minute" not in text
