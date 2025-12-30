#!/bin/bash
# Script de test du Runner en mode mock

set -e

cd "/home/david/git/Passerelle VHF"
source venv/bin/activate

echo "🚀 Test du Runner VHF"
echo "===================="
echo ""

# 1. Initialiser la DB
echo "1️⃣  Initialisation de la base de données..."
python -m app.init_db 2>&1 | tail -3

# 2. Activer le système
echo ""
echo "2️⃣  Activation du master_enabled..."
sqlite3 data/vhf-balise.db "UPDATE system_settings SET master_enabled=1 WHERE id=1"
echo "✅ Système activé"

# 3. Ajouter une clé FFVL test
echo ""
echo "3️⃣  Configuration provider FFVL..."
sqlite3 data/vhf-balise.db "INSERT OR REPLACE INTO provider_credentials (provider_id, credentials_json) VALUES ('ffvl', '{\"ffvl_key\": \"test_key_123\"}')"
echo "✅ Clé FFVL configurée"

# 4. Créer un canal test
echo ""
echo "4️⃣  Création d'un canal test..."
sqlite3 data/vhf-balise.db <<EOF
INSERT INTO channels (name, is_enabled, provider_id, station_id, measurement_period_seconds, offsets_seconds_json, min_interval_between_tx_seconds, template_text, engine_id, voice_id)
VALUES ('Test Canal 1', 1, 'ffvl', 67, 3600, '[0]', 300, 'Station {station_name}, vent moyen {wind_avg_kmh} kilomètres par heure, rafales {wind_max_kmh}.', 'piper', 'fr_FR-siwis-medium');

INSERT INTO channel_runtime (channel_id)
VALUES (1);
EOF
echo "✅ Canal créé (ID=1)"

# 5. Vérifier la config
echo ""
echo "5️⃣  Vérification de la configuration..."
sqlite3 data/vhf-balise.db "SELECT id, name, is_enabled, provider_id, station_id FROM channels" -header
echo ""

# 6. Lancer le runner en arrière-plan
echo "6️⃣  Démarrage du runner (mode mock PTT)..."
python -m app.runner > data/logs/runner_test.log 2>&1 &
RUNNER_PID=$!
echo "✅ Runner démarré (PID: $RUNNER_PID)"

# 7. Surveiller les logs pendant 15 secondes
echo ""
echo "7️⃣  Surveillance des logs (15 secondes)..."
timeout 15 tail -f data/logs/runner_test.log || true

# 8. Arrêter le runner
echo ""
echo "8️⃣  Arrêt du runner..."
kill $RUNNER_PID 2>/dev/null || true
wait $RUNNER_PID 2>/dev/null || true
echo "✅ Runner arrêté"

# 9. Vérifier les TX dans la DB
echo ""
echo "9️⃣  Vérification de l'historique des TX..."
echo "----------------------------------------"
sqlite3 data/vhf-balise.db "SELECT id, tx_id, mode, status, station_id, measurement_at, planned_at FROM tx_history ORDER BY created_at DESC LIMIT 5" -header -column
echo ""

echo "✅ Test terminé !"
echo ""
echo "📊 Résumé :"
echo "  - Logs complets : data/logs/runner_test.log"
echo "  - DB : data/vhf-balise.db"
