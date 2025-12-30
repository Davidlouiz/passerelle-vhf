# Passerelle VHF - Balises Météo Vocales

Système autohébergé sur Raspberry Pi qui annonce vocalement sur radio VHF les mesures de vent provenant de stations météo.

## Caractéristiques

- 🌊 **Multi-canaux** : gestion de plusieurs balises indépendantes
- 🌐 **Multi-providers** : FFVL et OpenWindMap
- 🔊 **Synthèse vocale hors ligne** : TTS Piper avec voix françaises
- 📡 **Contrôle PTT via GPIO** : compatible Raspberry Pi
- 🔒 **Architecture fail-safe** : aucune émission en cas d'erreur
- ⏰ **Planification flexible** : offsets multiples par mesure
- 🎯 **Idempotence garantie** : protection anti-boucle

## Installation

### Prérequis
- Raspberry Pi (ou Ubuntu pour développement)
- Python 3.10+
- Carte SD avec au moins 4 Go libres

### Installation rapide
```bash
git clone <repo-url> /opt/vhf-balise
cd /opt/vhf-balise
sudo ./install.sh
```

### Configuration initiale
1. Accéder à l'interface web : `http://<ip-raspberry>:8000`
2. Se connecter avec `admin` / `admin`
3. **Changer le mot de passe obligatoirement**
4. Configurer la clé API FFVL dans "Configuration providers"
5. Activer `master_enabled` dans "Paramètres système"
6. Créer et activer vos canaux

## Architecture

```
/opt/vhf-balise/
├── app/                    # Code Python
│   ├── main.py            # FastAPI app
│   ├── models.py          # Schéma SQLAlchemy
│   ├── database.py        # Connexion DB
│   ├── auth.py            # Authentification
│   ├── runner.py          # Scheduler/poller
│   ├── providers/         # Providers météo
│   ├── tts/               # Moteurs TTS
│   ├── ptt/               # Contrôle PTT
│   ├── routers/           # Endpoints API
│   └── services/          # Logique métier
├── frontend/              # Interface web
│   ├── index.html
│   ├── css/
│   └── js/
├── tests/                 # Tests unitaires
├── data/                  # Données persistantes
│   ├── vhf-balise.db
│   ├── audio_cache/
│   └── logs/
└── install.sh             # Script d'installation
```

## Services systemd

```bash
# Démarrer les services
sudo systemctl start vhf-balise-web
sudo systemctl start vhf-balise-runner

# Activer au démarrage
sudo systemctl enable vhf-balise-web
sudo systemctl enable vhf-balise-runner

# Voir les logs
sudo journalctl -u vhf-balise-web -f
sudo journalctl -u vhf-balise-runner -f
```

## Développement

### Configuration environnement
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Lancer les tests
```bash
pytest tests/ -v
```

### Lancer en mode développement
```bash
# Terminal 1 : API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 : Runner
python -m app.runner
```

## Sécurité

⚠️ **Règles critiques** :
- Aucune émission sans journalisation PENDING + commit DB vérifié
- Aucune émission de mesure périmée (jamais)
- Fail-closed : toute erreur bloque l'émission
- Timeout PTT : 30 secondes maximum (watchdog)

## API Providers

### FFVL
- Clé API requise (saisie dans l'UI)
- URL balise : `https://www.balisemeteo.com/balise.php?idBalise=XX`

### OpenWindMap (Pioupiou)
- Pas d'authentification
- URL balise : `https://www.openwindmap.org/pioupiou-XXX`
- API : `http://api.pioupiou.fr/v1/live/{station_id}`

## Licence

À définir

## Support

Voir la documentation complète dans `.github/copilot-instructions.md`
