"""Tests pour la normalisation des mesures."""

import pytest
from datetime import datetime
from app.providers import Measurement


def test_measurement_creation():
    """Teste la création d'une mesure."""
    now = datetime.utcnow()

    measurement = Measurement(
        measurement_at=now, wind_avg_kmh=15.5, wind_max_kmh=22.0, wind_min_kmh=10.2
    )

    assert measurement.measurement_at == now
    assert measurement.wind_avg_kmh == 15.5
    assert measurement.wind_max_kmh == 22.0
    assert measurement.wind_min_kmh == 10.2


def test_measurement_to_dict():
    """Teste la conversion en dictionnaire."""
    now = datetime.utcnow()

    measurement = Measurement(measurement_at=now, wind_avg_kmh=18.3, wind_max_kmh=27.1)

    data = measurement.to_dict()

    assert "measurement_at" in data
    assert data["wind_avg_kmh"] == 18.3
    assert data["wind_max_kmh"] == 27.1
    assert data["wind_min_kmh"] is None


def test_measurement_optional_min():
    """Teste qu'un min optionnel fonctionne."""
    measurement = Measurement(
        measurement_at=datetime.utcnow(),
        wind_avg_kmh=20.0,
        wind_max_kmh=30.0,
        # wind_min_kmh omis
    )

    assert measurement.wind_min_kmh is None
