#!/bin/bash
#
# Script de développement local
# Lance l'API et le runner en mode développement
#

set -e

# Couleurs pour l'affichage
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Passerelle VHF - Mode Développement${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Vérifier que venv existe
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Création de l'environnement virtuel...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

# Créer les dossiers de données
mkdir -p data/{audio_cache,logs,tts_models}

# Exporter la variable d'environnement
export VHF_DATA_DIR=$(pwd)/data

# Initialiser la DB si elle n'existe pas
if [ ! -f "data/vhf-balise.db" ]; then
    echo -e "${YELLOW}Initialisation de la base de données...${NC}"
    python -m app.init_db
fi

echo ""
echo -e "${GREEN}✓ Environnement prêt${NC}"
echo ""
echo "Commandes disponibles:"
echo ""
echo "  ${YELLOW}1. Lancer l'API:${NC}"
echo "     uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "  ${YELLOW}2. Lancer le Runner:${NC}"
echo "     python -m app.runner"
echo ""
echo "  ${YELLOW}3. Lancer les tests:${NC}"
echo "     pytest tests/ -v"
echo ""
echo "  ${YELLOW}4. Interface web:${NC}"
echo "     http://localhost:8000"
echo "     Login: admin / admin"
echo ""
echo -e "${BLUE}========================================${NC}"
