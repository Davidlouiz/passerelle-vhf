#!/usr/bin/env python3
"""
Script de test du Runner VHF.

Test complet : polling, planification, TX avec fail-safe.
"""

import sys
import time
import subprocess
import signal
from pathlib import Path

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.database import DATABASE_URL, init_db
from app.models import Channel, ChannelRuntime, SystemSettings, ProviderCredential

print("🚀 Test du Runner VHF")
print("=" * 40)
print()

# 1. Initialiser la DB
print("1️⃣  Initialisation de la base de données...")
init_db()

from app.init_db import create_default_data

create_default_data()
print("✅ DB initialisée")

# 2. Créer une session
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

# 3. Activer le système
print()
print("2️⃣  Activation du master_enabled...")
settings = db.query(SystemSettings).filter_by(id=1).first()
if settings:
    settings.master_enabled = True
    settings.poll_interval_seconds = 10  # 10s entre chaque poll (pour tests)
    db.commit()
    print("✅ Système activé (poll_interval=10s)")

# 4. Ajouter une clé FFVL test
print()
print("3️⃣  Configuration provider FFVL...")
cred = ProviderCredential(
    provider_id="ffvl", credentials_json={"api_key": "test_key_invalid_but_for_testing"}
)
db.merge(cred)
db.commit()
print("✅ Clé FFVL configurée")

# 5. Créer un canal test
print()
print("4️⃣  Création d'un canal test...")
channel = Channel(
    name="Test Canal Annecy",
    is_enabled=True,
    provider_id="ffvl",
    station_id=67,  # Balise Annecy
    measurement_period_seconds=3600,
    offsets_seconds_json="[0]",
    min_interval_between_tx_seconds=300,
    template_text="Station {station_name}, vent moyen {wind_avg_kmh} kilomètres par heure, rafales {wind_max_kmh}, direction {wind_direction_deg} degrés.",
    engine_id="piper",
    voice_id="fr_FR-siwis-medium",
    voice_params_json="{}",
)
db.add(channel)
db.commit()

# Créer le runtime
runtime = ChannelRuntime(channel_id=channel.id)
db.add(runtime)
db.commit()

print(f"✅ Canal créé (ID={channel.id}, station_id={channel.station_id})")

# 6. Afficher la config
print()
print("5️⃣  Configuration finale...")

# Recharger settings depuis la DB
settings = db.query(SystemSettings).filter_by(id=1).first()
channel = db.query(Channel).filter_by(id=channel.id).first()

print(f"   - master_enabled: {settings.master_enabled}")
print(f"   - Canal: {channel.name}")
print(f"   - Provider: {channel.provider_id}")
print(f"   - Station ID: {channel.station_id}")
print()

db.close()

# 7. Lancer le runner
print("6️⃣  Démarrage du runner (mode mock PTT)...")
print("   Logs : data/logs/runner_test.log")
print()

log_path = Path("data/logs/runner_test.log")
log_path.parent.mkdir(parents=True, exist_ok=True)

with open(log_path, "w") as log_file:
    runner_proc = subprocess.Popen(
        [sys.executable, "-m", "app.runner"],
        stdout=log_file,
        stderr=subprocess.STDOUT,
    )

print(f"✅ Runner démarré (PID: {runner_proc.pid})")
print()

# 8. Surveiller les logs
print("7️⃣  Surveillance des logs (45 secondes)...")
print("-" * 40)

try:
    # Suivre les logs pendant 45 secondes
    with open(log_path, "r") as log_file:
        timeout = time.time() + 45
        log_file.seek(0, 2)  # Aller à la fin

        while time.time() < timeout:
            line = log_file.readline()
            if line:
                print(line.rstrip())
            else:
                time.sleep(0.1)

except KeyboardInterrupt:
    print("\nInterrompu par l'utilisateur")

finally:
    # 9. Arrêter le runner
    print()
    print("8️⃣  Arrêt du runner...")
    runner_proc.terminate()
    try:
        runner_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        runner_proc.kill()
        runner_proc.wait()
    print("✅ Runner arrêté")

# 10. Vérifier les résultats
print()
print("9️⃣  Vérification de l'historique des TX...")
print("-" * 40)

db = Session()

from app.models import TxHistory

txs = db.query(TxHistory).order_by(TxHistory.created_at.desc()).limit(5).all()

if txs:
    for tx in txs:
        print(
            f"TX #{tx.id}: {tx.mode} | {tx.status} | Station {tx.station_id} | {tx.measurement_at}"
        )
else:
    print("Aucune TX enregistrée")

print()

# Vérifier les runtimes
from app.models import ChannelRuntime

runtime = db.query(ChannelRuntime).filter_by(channel_id=channel.id).first()

if runtime:
    print("Runtime du canal :")
    print(f"   - last_measurement_at: {runtime.last_measurement_at}")
    print(f"   - next_tx_at: {runtime.next_tx_at}")
    print(f"   - last_tx_at: {runtime.last_tx_at}")
    print(f"   - last_error: {runtime.last_error}")

db.close()

print()
print("✅ Test terminé !")
print()
print("📊 Résumé :")
print("  - Logs complets : data/logs/runner_test.log")
print("  - DB : data/vhf-balise.db")
