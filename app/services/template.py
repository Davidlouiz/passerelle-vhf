"""
Rendu de templates pour les annonces vocales.

Gère les variables {station_name}, {wind_avg_kmh}, etc.
"""
import re
from typing import Dict, Any
from datetime import datetime

from app.utils import round_to_int


class TemplateRenderer:
    """Rendu de templates d'annonces."""
    
    def render(self, template: str, context: Dict[str, Any]) -> str:
        """
        Rend un template avec les variables fournies.
        
        Variables supportées V1:
        - {station_name}
        - {wind_avg_kmh}
        - {wind_max_kmh}
        - {measurement_age_minutes}
        
        Args:
            template: Template avec variables (ex: "Station {station_name}, vent moyen {wind_avg_kmh}")
            context: Dictionnaire de variables
        
        Returns:
            Texte rendu
        """
        result = template
        
        # Remplacer les variables
        for var_name, value in context.items():
            placeholder = f"{{{var_name}}}"
            
            # Formater la valeur selon le type
            if isinstance(value, float):
                # Arrondir à l'entier pour les nombres
                formatted_value = str(round_to_int(value))
            elif isinstance(value, int):
                formatted_value = str(value)
            else:
                formatted_value = str(value)
            
            result = result.replace(placeholder, formatted_value)
        
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
        # Variables supportées V1
        supported_vars = {
            "station_name",
            "wind_avg_kmh",
            "wind_max_kmh",
            "measurement_age_minutes"
        }
        
        # Extraire les variables utilisées
        used_vars = set(re.findall(r'\{(\w+)\}', template))
        
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
        return set(re.findall(r'\{(\w+)\}', template))
    
    def build_context_from_measurement(
        self,
        station_name: str,
        measurement: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Construit un contexte depuis une mesure.
        
        Args:
            station_name: Nom de la station
            measurement: Dictionnaire de mesure (measurement_at, wind_avg_kmh, wind_max_kmh)
        
        Returns:
            Contexte prêt pour le rendu
        """
        context = {
            "station_name": station_name,
            "wind_avg_kmh": measurement.get("wind_avg_kmh", 0),
            "wind_max_kmh": measurement.get("wind_max_kmh", 0)
        }
        
        # Calculer l'âge de la mesure si measurement_at présent
        if "measurement_at" in measurement:
            age_seconds = (datetime.utcnow() - measurement["measurement_at"]).total_seconds()
            context["measurement_age_minutes"] = round_to_int(age_seconds / 60)
        
        return context
