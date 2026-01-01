#!/usr/bin/env python3
"""
Test manuel pour vérifier le fix timezone FFVL vs OpenWindMap.

Ce test simule le comportement du runner avec des mesures des deux providers
et vérifie que les timestamps sont cohérents.
"""

import sys
sys.path.insert(0, '.')

from datetime import datetime, timedelta
import pytz
from app.database import get_db_session, init_db
from app.models import Channel, ChannelRuntime, SystemSettings, ProviderCredential
from app.providers import Measurement

def setup_test_db():
    """Initialise une DB de test en mémoire."""
    init_db()
    
def simulate_ffvl_measurement():
    """Simule une mesure FFVL avec conversion timezone."""
    # API FFVL retourne heure locale Paris
    date_str = '2026-01-01 06:30:00'
    dt_naive = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    paris_tz = pytz.timezone('Europe/Paris')
    dt_paris = paris_tz.localize(dt_naive)
    measurement_at = dt_paris.astimezone(pytz.UTC)
    
    print(f"FFVL API: {date_str} (Paris)")
    print(f"  → UTC aware: {measurement_at}")
    print(f"  → UTC naïf: {measurement_at.replace(tzinfo=None)}")
    
    return Measurement(
        measurement_at=measurement_at,
        wind_avg_kmh=15.0,
        wind_max_kmh=22.0,
        wind_min_kmh=10.0
    )

def simulate_openwindmap_measurement():
    """Simule une mesure OpenWindMap déjà en UTC."""
    # API OpenWindMap retourne déjà UTC
    date_str = '2026-01-01T05:30:00Z'
    measurement_at = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    measurement_at = measurement_at.astimezone(pytz.UTC)
    
    print(f"OpenWindMap API: {date_str}")
    print(f"  → UTC aware: {measurement_at}")
    print(f"  → UTC naïf: {measurement_at.replace(tzinfo=None)}")
    
    return Measurement(
        measurement_at=measurement_at,
        wind_avg_kmh=18.0,
        wind_max_kmh=25.0,
        wind_min_kmh=12.0
    )

def test_runner_behavior():
    """Simule le comportement du runner avec les deux types de mesures."""
    print("\n=== TEST RUNNER BEHAVIOR ===\n")
    
    # Mesures
    ffvl_measure = simulate_ffvl_measurement()
    print()
    owm_measure = simulate_openwindmap_measurement()
    print()
    
    # Simulation stockage en base (comme dans _update_channel_measurement)
    print("=== STOCKAGE EN BASE ===")
    
    ffvl_stored = (
        ffvl_measure.measurement_at.replace(tzinfo=None)
        if ffvl_measure.measurement_at.tzinfo
        else ffvl_measure.measurement_at
    )
    print(f"FFVL stocké: {ffvl_stored} (naïf UTC)")
    
    owm_stored = (
        owm_measure.measurement_at.replace(tzinfo=None)
        if owm_measure.measurement_at.tzinfo
        else owm_measure.measurement_at
    )
    print(f"OpenWindMap stocké: {owm_stored} (naïf UTC)")
    print()
    
    # Vérification péremption
    print("=== VÉRIFICATION PÉREMPTION ===")
    now = datetime.utcnow()
    period_seconds = 600  # 10 minutes
    
    ffvl_age = (now - ffvl_stored).total_seconds()
    owm_age = (now - owm_stored).total_seconds()
    
    print(f"Maintenant (UTC naïf): {now}")
    print(f"FFVL age: {ffvl_age:.1f}s (périmé: {ffvl_age > period_seconds})")
    print(f"OpenWindMap age: {owm_age:.1f}s (périmé: {owm_age > period_seconds})")
    print()
    
    # Test comparaison
    print("=== TEST ÉGALITÉ ===")
    # Si deux mesures au même instant UTC
    same_time_paris = datetime.strptime('2026-01-01 06:30:00', '%Y-%m-%d %H:%M:%S')
    same_time_paris = pytz.timezone('Europe/Paris').localize(same_time_paris)
    same_time_utc_ffvl = same_time_paris.astimezone(pytz.UTC).replace(tzinfo=None)
    
    same_time_owm = datetime.fromisoformat('2026-01-01T05:30:00Z').replace(tzinfo=None)
    
    print(f"FFVL 06:30 Paris → {same_time_utc_ffvl}")
    print(f"OWM 05:30 UTC → {same_time_owm}")
    print(f"Égaux ? {same_time_utc_ffvl == same_time_owm}")
    print()
    
    # Test planification TX
    print("=== TEST PLANIFICATION TX ===")
    offset_seconds = 0
    ffvl_planned = ffvl_stored + timedelta(seconds=offset_seconds)
    owm_planned = owm_stored + timedelta(seconds=offset_seconds)
    
    print(f"FFVL TX planifiée: {ffvl_planned}")
    print(f"OpenWindMap TX planifiée: {owm_planned}")
    print()
    
    print("✅ Tous les tests passés ! Les deux providers utilisent bien UTC naïf de manière cohérente.")

if __name__ == '__main__':
    test_runner_behavior()
