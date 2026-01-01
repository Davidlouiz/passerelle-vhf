#!/bin/bash
#
# Script de déblocage manuel du runner VHF
# Utiliser UNIQUEMENT si le runner refuse de démarrer alors qu'aucun processus ne tourne
#

set -e

cd "$(dirname "$0")"

# Déterminer chemin du fichier PID
if [ -n "$VHF_DATA_DIR" ]; then
    PID_FILE="$VHF_DATA_DIR/runner.pid"
else
    PID_FILE="./data/runner.pid"
fi

echo "=== Déblocage du runner VHF ==="
echo ""

# Vérifier si des runners tournent
if pgrep -f "python.*app.runner" > /dev/null; then
    echo "⚠️  ATTENTION : Des processus runner tournent encore !"
    echo ""
    echo "Processus détectés :"
    pgrep -fa "python.*app.runner"
    echo ""
    read -p "Voulez-vous les arrêter ? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Arrêt des runners..."
        pkill -TERM -f "python.*app.runner" || true
        sleep 2
        # Force kill si toujours présents
        pkill -KILL -f "python.*app.runner" 2>/dev/null || true
        echo "✓ Runners arrêtés"
    else
        echo "Abandon."
        exit 1
    fi
fi

# Supprimer le fichier PID
if [ -f "$PID_FILE" ]; then
    OLD_PID=$(cat "$PID_FILE")
    rm -f "$PID_FILE"
    echo "✓ Fichier PID supprimé (ancien PID: $OLD_PID)"
else
    echo "ℹ️  Aucun fichier PID trouvé ($PID_FILE)"
fi

echo ""
echo "✅ Déblocage terminé !"
echo ""
echo "Vous pouvez maintenant démarrer le runner :"
echo "  python -m app.runner"
echo ""
