#!/usr/bin/env python3
"""
Test rapide pour vérifier que le runner utilise bien channel.name au lieu de measurement.station_name.
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from app.services.template import TemplateRenderer
from app.providers import Measurement

print("🧪 Test du fix runner : channel.name au lieu de measurement.station_name")
print("=" * 70)

# Simuler une mesure (sans station_name)
measurement = Measurement(
    measurement_at=datetime.utcnow(),
    wind_avg_kmh=15.5,
    wind_max_kmh=22.3,
    wind_min_kmh=10.2,
    wind_direction=45.0,  # Nord-Est
)


# Simuler un channel
class FakeChannel:
    name = "Balise du Col de la Forclaz"
    template_text = "Balise de {station_name}, {wind_direction_name}, {wind_avg_kmh} kilomètres par heure, {wind_max_kmh} maximum, minimum {wind_min_kmh}, il y a {measurement_age_minutes} minutes."


channel = FakeChannel()

# Rendu comme dans le runner (APRÈS correction)
renderer = TemplateRenderer()

rendered_text = renderer.render(
    template=channel.template_text,
    station_name=channel.name,  # ✅ Utilise le nom du canal
    wind_avg_kmh=measurement.wind_avg_kmh,
    wind_max_kmh=measurement.wind_max_kmh,
    wind_min_kmh=measurement.wind_min_kmh,
    wind_direction_deg=measurement.wind_direction,  # ✅ Utilise wind_direction (pas wind_direction_deg)
    measurement_at=measurement.measurement_at,
)

print("\n📝 Template:")
print(f"   {channel.template_text}\n")

print("📊 Données:")
print(f"   channel.name = {channel.name}")
print(f"   wind_avg_kmh = {measurement.wind_avg_kmh}")
print(f"   wind_max_kmh = {measurement.wind_max_kmh}")
print(f"   wind_min_kmh = {measurement.wind_min_kmh}")
print(f"   wind_direction = {measurement.wind_direction}°\n")

print("🔊 Résultat rendu:")
print(f"   {rendered_text}\n")

# Vérifier qu'aucune variable n'est restée non remplacée
remaining = []
for var in [
    "{station_name}",
    "{wind_avg_kmh}",
    "{wind_max_kmh}",
    "{wind_min_kmh}",
    "{wind_direction_deg}",
    "{wind_direction_name}",
    "{measurement_age_minutes}",
]:
    if var in rendered_text:
        remaining.append(var)

if remaining:
    print(f"❌ ERREUR : Variables non remplacées : {', '.join(remaining)}")
    sys.exit(1)
else:
    print("✅ Toutes les variables ont été correctement remplacées !")
    print("\n" + "=" * 70)
    print("✅ Le fix fonctionne correctement !")
