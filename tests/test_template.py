"""Tests pour le rendu de templates."""
import pytest
from app.services.template import TemplateRenderer
from datetime import datetime, timedelta


def test_template_rendering_simple():
    """Teste le rendu basique de variables."""
    renderer = TemplateRenderer()
    
    template = "Station {station_name}, vent moyen {wind_avg_kmh} km/h"
    context = {
        "station_name": "Col du Lautaret",
        "wind_avg_kmh": 25.7
    }
    
    result = renderer.render(template, context)
    
    # Les floats doivent être arrondis à l'entier
    assert result == "Station Col du Lautaret, vent moyen 26 km/h"


def test_template_rendering_all_variables():
    """Teste le rendu avec toutes les variables."""
    renderer = TemplateRenderer()
    
    template = "Station {station_name}, vent moyen {wind_avg_kmh}, rafales {wind_max_kmh}, mesure de {measurement_age_minutes} minutes"
    context = {
        "station_name": "Test",
        "wind_avg_kmh": 15.2,
        "wind_max_kmh": 22.8,
        "measurement_age_minutes": 3
    }
    
    result = renderer.render(template, context)
    assert "vent moyen 15" in result
    assert "rafales 23" in result
    assert "3 minutes" in result


def test_template_validation_valid():
    """Teste la validation d'un template valide."""
    renderer = TemplateRenderer()
    
    template = "Station {station_name}, vent {wind_avg_kmh}"
    is_valid, error = renderer.validate_template(template)
    
    assert is_valid
    assert error == ""


def test_template_validation_invalid_variable():
    """Teste la validation avec une variable non supportée."""
    renderer = TemplateRenderer()
    
    template = "Station {station_name}, température {temperature}"
    is_valid, error = renderer.validate_template(template)
    
    assert not is_valid
    assert "temperature" in error


def test_template_extract_variables():
    """Teste l'extraction des variables utilisées."""
    renderer = TemplateRenderer()
    
    template = "Vent {wind_avg_kmh}, rafales {wind_max_kmh}"
    variables = renderer.extract_variables(template)
    
    assert variables == {"wind_avg_kmh", "wind_max_kmh"}


def test_build_context_from_measurement():
    """Teste la construction du contexte depuis une mesure."""
    renderer = TemplateRenderer()
    
    measurement_at = datetime.utcnow() - timedelta(minutes=5)
    measurement = {
        "measurement_at": measurement_at,
        "wind_avg_kmh": 18.3,
        "wind_max_kmh": 27.1
    }
    
    context = renderer.build_context_from_measurement("Test Station", measurement)
    
    assert context["station_name"] == "Test Station"
    assert context["wind_avg_kmh"] == 18.3
    assert context["wind_max_kmh"] == 27.1
    assert context["measurement_age_minutes"] == 5
