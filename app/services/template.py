"""
Rendu de templates pour les annonces vocales.

Gère les variables {station_name}, {wind_avg_kmh}, {wind_direction_cardinal}, etc.
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime

from app.utils import round_to_int


def degrees_to_cardinal(degrees: float) -> str:
    """
    Convertit des degrés en direction cardinale.

    Args:
        degrees: Direction en degrés (0-359)

    Returns:
        Direction cardinale (N, NE, E, SE, S, SO, O, NO, etc.)
    """
    directions = [
        "N",
        "NNE",
        "NE",
        "ENE",
        "E",
        "ESE",
        "SE",
        "SSE",
        "S",
        "SSO",
        "SO",
        "OSO",
        "O",
        "ONO",
        "NO",
        "NNO",
    ]
    index = round((degrees % 360) / 22.5)
    return directions[index % 16]


def degrees_to_name(degrees: float) -> str:
    """
    Convertit des degrés en nom de direction en français.

    Args:
        degrees: Direction en degrés (0-359)

    Returns:
        Nom complet (Nord, Nord-Est, etc.)
    """
    names = [
        "Nord",
        "Nord-Nord-Est",
        "Nord-Est",
        "Est-Nord-Est",
        "Est",
        "Est-Sud-Est",
        "Sud-Est",
        "Sud-Sud-Est",
        "Sud",
        "Sud-Sud-Ouest",
        "Sud-Ouest",
        "Ouest-Sud-Ouest",
        "Ouest",
        "Ouest-Nord-Ouest",
        "Nord-Ouest",
        "Nord-Nord-Ouest",
    ]
    index = round((degrees % 360) / 22.5)
    return names[index % 16]


class TemplateRenderer:
    """Rendu de templates d'annonces."""

    def render(
        self,
        template: str,
        station_name: str,
        wind_avg_kmh: float,
        wind_max_kmh: float,
        wind_min_kmh: Optional[float] = None,
        wind_direction_deg: Optional[float] = None,
        measurement_at: Optional[datetime] = None,
    ) -> str:
        """
        Rend un template avec les variables fournies.

        Variables supportées:
        - {station_name} - Nom de la station
        - {wind_avg_kmh} - Vent moyen (arrondi)
        - {wind_max_kmh} - Rafales (arrondi)
        - {wind_min_kmh} - Vent minimum (arrondi, optionnel)
        - {wind_direction_name} - Direction complète (Nord, Nord-Est, etc.)
        - {wind_direction_deg} - Direction en degrés (arrondi)
        - {measurement_age_minutes} - Ancienneté en minutes

        Args:
            template: Template avec variables
            station_name: Nom de la station
            wind_avg_kmh: Vent moyen
            wind_max_kmh: Rafales
            wind_min_kmh: Vent minimum (optionnel)
            wind_direction_deg: Direction en degrés (optionnel)
            measurement_at: Timestamp de la mesure (pour calcul ancienneté)

        Returns:
            Texte rendu
        """
        # Construire le contexte
        context = {
            "station_name": station_name,
            "wind_avg_kmh": round_to_int(wind_avg_kmh),
            "wind_max_kmh": round_to_int(wind_max_kmh),
        }

        # Ajouter wind_min_kmh si disponible
        if wind_min_kmh is not None:
            context["wind_min_kmh"] = round_to_int(wind_min_kmh)

        # Ajouter les directions si disponibles
        if wind_direction_deg is not None:
            context["wind_direction_deg"] = round_to_int(wind_direction_deg)
            context["wind_direction_cardinal"] = degrees_to_cardinal(wind_direction_deg)
            context["wind_direction_name"] = degrees_to_name(wind_direction_deg)

        # Ajouter l'ancienneté si disponible
        if measurement_at is not None:
            age_seconds = (datetime.utcnow() - measurement_at).total_seconds()
            context["measurement_age_minutes"] = round_to_int(age_seconds / 60)

        # Rendre le template
        result = template
        for var_name, value in context.items():
            placeholder = f"{{{var_name}}}"
            result = result.replace(placeholder, str(value))

        return result

    def validate_template(self, template: str) -> tuple[bool, str]:
        """
        Valide un template.

        Vérifie que:
        - Les variables utilisées sont supportées
        - La syntaxe est correcte

        Returns:
            (is_valid, error_message)
        """
        # Variables supportées
        supported_vars = {
            "station_name",
            "wind_avg_kmh",
            "wind_max_kmh",
            "wind_min_kmh",
            "wind_direction_name",
            "wind_direction_deg",
            "measurement_age_minutes",
        }

        # Extraire les variables utilisées
        used_vars = set(re.findall(r"\{(\w+)\}", template))

        # Vérifier que toutes les variables sont supportées
        unsupported = used_vars - supported_vars
        if unsupported:
            return False, f"Variables non supportées: {', '.join(unsupported)}"

        return True, ""

    def extract_variables(self, template: str) -> set[str]:
        """
        Extrait les variables utilisées dans un template.

        Returns:
            Ensemble de noms de variables
        """
        return set(re.findall(r"\{(\w+)\}", template))
