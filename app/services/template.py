"""
Rendu de templates pour les annonces vocales.

Gère les variables {station_name}, {wind_avg_kmh}, {wind_direction_cardinal}, etc.
"""

import re
from typing import Dict, Any, Optional
from datetime import datetime
import pytz

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
    Convertit des degrés en nom de direction en français optimisé pour TTS.

    Les noms sont adaptés pour une meilleure prononciation par les moteurs TTS :
    - "Este" au lieu de "Est" quand il est suivi d'un tiret (meilleure liaison)
    - Vous pouvez modifier ces valeurs ci-dessous pour ajuster la prononciation

    Args:
        degrees: Direction en degrés (0-359)

    Returns:
        Nom complet optimisé pour TTS (Nord, Nord-Este, etc.)
    """
    # 🔊 PERSONNALISATION PRONONCIATION TTS
    # Modifiez ces valeurs pour ajuster la prononciation vocale.
    # Exemples de modifications possibles :
    #   - "Este" → meilleure liaison que "Est" avec tiret
    #   - "Oueste" → si "Ouest" est mal prononcé
    #   - Ajouter des espaces pour ralentir : "Nord - Este"
    names = [
        "Nord",  # 0° (360°)
        "Nord-Nord-Este",  # 22.5°
        "Nord-Este",  # 45°
        "Este-Nord-Este",  # 67.5°
        "Este",  # 90°
        "Este-Sud-Este",  # 112.5°
        "Sud-Este",  # 135°
        "Sud-Sud-Este",  # 157.5°
        "Sud",  # 180°
        "Sud-Sud-Oueste",  # 202.5°
        "Sud-Oueste",  # 225°
        "Oueste-Sud-Oueste",  # 247.5°
        "Oueste",  # 270°
        "Oueste-Nord-Oueste",  # 292.5°
        "Nord-Oueste",  # 315°
        "Nord-Nord-Oueste",  # 337.5°
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
            age_seconds = (datetime.now(pytz.UTC) - measurement_at).total_seconds()
            age_minutes = round_to_int(age_seconds / 60)
            # Remplacer "1" par "une" pour meilleure prononciation
            context["measurement_age_minutes"] = (
                "une" if age_minutes == 1 else str(age_minutes)
            )

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
