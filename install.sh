#!/bin/bash
#
# Script d'installation de Passerelle VHF
#
# Usage: sudo ./install.sh
#

set -e

echo "========================================="
echo "Installation Passerelle VHF"
echo "========================================="

# Vérifier que le script est exécuté en root
if [ "$EUID" -ne 0 ]; then
  echo "❌ Ce script doit être exécuté en root (sudo ./install.sh)"
  exit 1
fi

# Détecter l'utilisateur qui a lancé sudo
REAL_USER=${SUDO_USER:-$USER}

echo ""
echo "1. Création de l'utilisateur système vhf-balise..."
if ! id -u vhf-balise > /dev/null 2>&1; then
    useradd -r -s /bin/false -d /opt/vhf-balise vhf-balise
    echo "✓ Utilisateur créé"
else
    echo "✓ Utilisateur existe déjà"
fi

echo ""
echo "2. Création des répertoires..."
mkdir -p /opt/vhf-balise
mkdir -p /opt/vhf-balise/data/{audio_cache,logs,tts_models}

echo ""
echo "3. Copie des fichiers du projet..."
cp -r app /opt/vhf-balise/
cp -r frontend /opt/vhf-balise/ 2>/dev/null || mkdir -p /opt/vhf-balise/frontend
cp requirements.txt /opt/vhf-balise/

echo ""
echo "4. Installation des dépendances système..."
apt-get update
apt-get install -y \
    python3 \
    python3-venv \
    python3-pip \
    python3-dev \
    build-essential \
    alsa-utils \
    wget

echo ""
echo "5. Création de l'environnement virtuel Python..."
cd /opt/vhf-balise
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Environnement virtuel créé"
else
    echo "✓ Environnement virtuel existe déjà"
fi

echo ""
echo "6. Installation des dépendances Python..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "7. Installation de Piper TTS..."
pip install piper-tts

echo ""
echo "8. Téléchargement des voix françaises Piper..."
VOICE_DIR="/opt/vhf-balise/data/tts_models"

# Voix Siwis (recommandée)
if [ ! -f "$VOICE_DIR/fr_FR-siwis-medium.onnx" ]; then
    echo "Téléchargement de la voix fr_FR-siwis-medium..."
    wget -O "$VOICE_DIR/fr_FR-siwis-medium.onnx" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx" \
        || echo "⚠️  Échec du téléchargement de la voix Siwis"
    
    wget -O "$VOICE_DIR/fr_FR-siwis-medium.onnx.json" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx.json" \
        || echo "⚠️  Échec du téléchargement du fichier config Siwis"
else
    echo "✓ Voix Siwis déjà présente"
fi

# Voix Tom (alternative)
if [ ! -f "$VOICE_DIR/fr_FR-tom-medium.onnx" ]; then
    echo "Téléchargement de la voix fr_FR-tom-medium..."
    wget -O "$VOICE_DIR/fr_FR-tom-medium.onnx" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr_FR/tom/medium/fr_FR-tom-medium.onnx" \
        || echo "⚠️  Échec du téléchargement de la voix Tom"
    
    wget -O "$VOICE_DIR/fr_FR-tom-medium.onnx.json" \
        "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/fr/fr_FR/tom/medium/fr_FR-tom-medium.onnx.json" \
        || echo "⚠️  Échec du téléchargement du fichier config Tom"
else
    echo "✓ Voix Tom déjà présente"
fi

echo ""
echo "9. Initialisation de la base de données..."
python -m app.init_db

echo ""
echo "10. Configuration des permissions..."
chown -R vhf-balise:vhf-balise /opt/vhf-balise

echo ""
echo "11. Installation des services systemd..."
cp vhf-balise-web.service /etc/systemd/system/
cp vhf-balise-runner.service /etc/systemd/system/
systemctl daemon-reload

echo ""
echo "========================================="
echo "✓ Installation terminée !"
echo "========================================="
echo ""
echo "Prochaines étapes :"
echo ""
echo "1. Démarrer les services :"
echo "   sudo systemctl start vhf-balise-web"
echo "   sudo systemctl start vhf-balise-runner"
echo ""
echo "2. Activer au démarrage :"
echo "   sudo systemctl enable vhf-balise-web"
echo "   sudo systemctl enable vhf-balise-runner"
echo ""
echo "3. Vérifier les logs :"
echo "   sudo journalctl -u vhf-balise-web -f"
echo "   sudo journalctl -u vhf-balise-runner -f"
echo ""
echo "4. Accéder à l'interface web :"
echo "   http://$(hostname -I | awk '{print $1}'):8000"
echo "   Login : admin / admin (à changer au premier login)"
echo ""
echo "========================================="
