#!/usr/bin/env python3
"""
Test du template renderer - vérifie que toutes les variables sont bien remplacées.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.services.template import TemplateRenderer, degrees_to_name
from datetime import datetime, timedelta

print("🧪 Test du Template Renderer")
print("=" * 60)

# Test 1 : Conversions de direction
print("\n1️⃣  Test conversions de direction")
print("-" * 60)
test_degrees = [0, 22.5, 45, 90, 135, 180, 225, 270, 315]
for deg in test_degrees:
    name = degrees_to_name(deg)
    print(f"   {deg:>5.1f}° → {name}")

# Test 2 : Template avec toutes les variables
print("\n2️⃣  Test template complet avec toutes les variables")
print("-" * 60)

renderer = TemplateRenderer()

template = """Balise {station_name}, {wind_direction_name}, vent moyen {wind_avg_kmh} kilomètres par heure, rafales {wind_max_kmh}, minimum {wind_min_kmh}, direction {wind_direction_deg} degrés, mesure il y a {measurement_age_minutes} minutes."""

measurement_at = datetime.utcnow() - timedelta(minutes=15)

result = renderer.render(
    template=template,
    station_name="Annecy",
    wind_avg_kmh=12.3,
    wind_max_kmh=18.7,
    wind_min_kmh=8.2,
    wind_direction_deg=22.5,
    measurement_at=measurement_at,
)

print(f"📝 Template:")
print(f"   {template}")
print()
print(f"🔊 Résultat:")
print(f"   {result}")

# Test 3 : Vérifier qu'il ne reste aucune variable non remplacée
print("\n3️⃣  Vérification : toutes les variables sont-elles remplacées ?")
print("-" * 60)

remaining_vars = []
for var in [
    "{station_name}",
    "{wind_avg_kmh}",
    "{wind_max_kmh}",
    "{wind_min_kmh}",
    "{wind_direction_name}",
    "{wind_direction_deg}",
    "{measurement_age_minutes}",
]:
    if var in result:
        remaining_vars.append(var)
        print(f"   ❌ {var} n'a PAS été remplacé")

if not remaining_vars:
    print(f"   ✅ Toutes les variables ont été correctement remplacées")
else:
    print(f"\n   ⚠️  ERREUR : {len(remaining_vars)} variable(s) non remplacée(s)")
    sys.exit(1)

# Test 4 : Template par défaut recommandé
print("\n4️⃣  Test template par défaut recommandé")
print("-" * 60)

default_template = "Balise de {station_name}, {wind_direction_name}, {wind_avg_kmh} kilomètres par heure, {wind_max_kmh} maximum, il y a {measurement_age_minutes} minutes."

result_default = renderer.render(
    template=default_template,
    station_name="Col de la Forclaz",
    wind_avg_kmh=25.8,
    wind_max_kmh=35.2,
    wind_direction_deg=180,
    measurement_at=datetime.utcnow() - timedelta(minutes=8),
)

print(f"📝 Template:")
print(f"   {default_template}")
print()
print(f"🔊 Résultat:")
print(f"   {result_default}")

print("\n" + "=" * 60)
print("✅ Tous les tests sont passés avec succès !")
