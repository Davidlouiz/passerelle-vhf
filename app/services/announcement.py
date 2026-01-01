"""
Service de préparation des annonces.

Centralise la logique de rendu des templates pour garantir la cohérence
entre les aperçus TTS et les vraies transmissions.
"""

from datetime import datetime
from typing import Optional

from app.models import Channel
from app.providers import Measurement
from app.services.template import TemplateRenderer


def prepare_announcement_text(channel: Channel, measurement: Measurement) -> str:
    """
    Prépare le texte d'annonce pour un canal et une mesure donnés.

    Cette fonction centralise la logique de rendu du template pour garantir
    que l'aperçu TTS affiche exactement le même texte que celui qui sera
    transmis lors de la vraie annonce.

    Args:
        channel: Canal configuré avec son template
        measurement: Mesure météo à annoncer

    Returns:
        Texte rendu prêt pour la synthèse vocale

    Note:
        Le calcul de measurement_age_minutes utilise le timestamp de la mesure
        comme référence, garantissant que le texte sera cohérent au moment
        de la planification ET de l'exécution de la TX.
    """
    renderer = TemplateRenderer()

    return renderer.render(
        template=channel.template_text,
        station_name=channel.name,
        wind_avg_kmh=measurement.wind_avg_kmh,
        wind_max_kmh=measurement.wind_max_kmh,
        wind_min_kmh=measurement.wind_min_kmh,
        wind_direction_deg=measurement.wind_direction,
        measurement_at=measurement.measurement_at,
    )
