# Instructions Copilot - Passerelle VHF

## Vue d'ensemble du projet
Passerelle radio VHF multi-canaux qui annonce vocalement les mesures de vent provenant de stations météo. Auto-hébergée sur Raspberry Pi (compatible Raspbian/Ubuntu), utilisant la synthèse vocale hors ligne et le contrôle PTT via GPIO.

**Plateforme cible** : Raspberry Pi avec carte SD (doit aussi fonctionner sur Ubuntu pour le développement)  
**Langage** : Python avec backend FastAPI, frontend HTML/CSS/JS vanilla  
**Base de données** : SQLite  
**Installation** : `/opt/vhf-balise/` + dossier `data/` persistant

## Règle absolue de sécurité

**⚠️ AUCUNE émission ne doit avoir lieu sans avoir d'abord journalisé dans la DB avec status="PENDING" et vérifié le commit.**

**⚠️ AUCUNE émission si la mesure est périmée ou en cas de doute (fail-closed).**

Si une opération échoue (DB, commit, mesure invalide, audio manquant, exception), **aucune émission ne part**.

## Exigences de sécurité critiques (TOUJOURS appliquer)

### Architecture fail-safe (fail-closed)
**AUCUNE transmission ne doit avoir lieu si UNE SEULE de ces conditions est fausse :**
- `master_enabled=true` dans system_settings
- Canal activé
- Identifiants provider présents (ex : clé API FFVL)
- Base de données accessible ET commit réussi
- Mesure présente, valide ET **non périmée**
- Fichier audio présent OU synthèse réussie
- Aucune exception runtime non gérée

### Règle de péremption (absolue)
```python
# Une mesure est périmée après measurement_period_seconds du canal
is_expired = (now - measurement_at) > measurement_period_seconds
if is_expired:
    # BLOQUER toutes actions : TX planifiée, tests manuels, prévisualisation
    raise MeasurementExpiredError()
```

### Idempotence via tx_id
```python
# Identifiant unique empêchant les transmissions dupliquées
tx_id = hash(channel_id, provider_id, station_id, measurement_at, 
             rendered_text, engine_id, voice_id, voice_params, offset_seconds)
# tx_id doit être UNIQUE dans la table tx_history (contrainte DB)
```

### Ordre de TX : journaliser-avant-émettre (OBLIGATOIRE)
```python
# 1. Récupérer la mesure + vérifier non périmée
# 2. Rendre le texte depuis le template
# 3. Obtenir/synthétiser l'audio (utiliser le cache)
# 4. Calculer tx_id
# 5. INSERT tx_history avec status="PENDING" puis COMMIT
#    - Si le commit échoue → STOP, PAS d'émission
# 6. Re-vérifier non périmée immédiatement avant TX
# 7. Acquérir le verrou TX global
# 8. PTT ON → délai lead → jouer audio → délai tail → PTT OFF
# 9. Watchdog applique 30s max de durée PTT (force OFF)
# 10. UPDATE status="SENT"|"FAILED" + COMMIT
```

### Ressource radio partagée
- Une SEULE radio pour tous les canaux
- Verrou TX global empêche les transmissions simultanées
- Quand plusieurs annonces sont dues au même instant :
  - Mélanger l'ordre aléatoirement (shuffle)
  - Exécuter séquentiellement avec `inter_announcement_pause_seconds` entre (défaut : 10s)

## Composants de l'architecture

### Backend FastAPI (sans Nginx)
- Sert les endpoints API + fichiers statiques frontend
- Aucune clé API en dur nulle part
- Authentification par session avec changement obligatoire du mot de passe au premier login (défaut : admin/admin)

### Runner/Planificateur (service systemd)
- Interroge les providers à intervalle `poll_interval_seconds`
- Détecte les nouvelles mesures (par timestamp `measurement_at`)
- Planifie les TX basées sur les offsets : `tx_times = [measurement_at + offset for offset in offsets_seconds]`
- Politique V1 : `cancel_on_new` - nouvelle mesure annule les futures TX non exécutées
- Anti-spam : `min_interval_between_tx_seconds` par canal

### Système multi-providers
**Architecture obligatoire** : abstraction provider dès le départ, même si un seul est implémenté.

**Provider FFVL (à développer en premier) :**
- Requiert une clé API (fournie par l'utilisateur via UI, **jamais en dur**)
- DOIT ajouter `&key={ffvl_api_key}` à toutes les URLs d'appels API
- Extraction de l'ID station : `https://www.balisemeteo.com/balise.php?idBalise=67` → extraire le paramètre `idBalise`

**Provider OpenWindMap (API Pioupiou) - à développer ensuite :**
- Pas d'authentification requise
- Extraction de l'ID station depuis les URLs visuelles :
  - `https://www.openwindmap.org/pioupiou-385` → extraire `385`
  - `https://www.openwindmap.org/windbird-1500` → extraire `1500`
  - Pattern : extraire l'ID numérique de `xxx-NNNN` ou des chemins `/PPNNN`, `/WBNNN`
- Fetch groupé : `GET http://api.pioupiou.fr/v1/live/all` pour l'efficacité
- Fetch unique : `GET http://api.pioupiou.fr/v1/live/{station_id}`

### Moteur TTS (hors ligne, interchangeable)
**Moteur initial : Piper** (https://github.com/rhasspy/piper)
- Fonctionne hors ligne après installation
- Léger et rapide (compatible Raspberry Pi modestes)
- Voix françaises de qualité (ex : `fr_FR-siwis-medium`, `fr_FR-tom-medium`)
- Installation : binaire + fichiers modèle `.onnx`

**Stratégie cache-first obligatoire :**
```python
tts_cache_key = hash(engine_id, engine_version, model_version, 
                     voice_id, voice_params, locale, rendered_text)
# Vérifier table audio_cache en premier
# Si absent : synthétiser, sauver sur disque + DB, puis utiliser
# NE JAMAIS régénérer un audio existant
```

**Contrat moteur TTS (abstraction obligatoire) :**
```python
class TTSEngine(ABC):
    @abstractmethod
    def list_voices(self) -> list[dict]:
        """Retourne [{voice_id, label, languages}]"""
        pass
    
    @abstractmethod
    def synthesize(self, text: str, voice_id: str, params: dict) -> str:
        """Retourne le chemin du fichier audio généré"""
        pass
```

**Comment changer de moteur :**
1. Implémenter la classe héritant de `TTSEngine`
2. Ajouter dans `tts_engines.py` le nouveau moteur
3. Mettre à jour la config UI pour lister le nouveau moteur
4. Le cache reste compatible (clé inclut `engine_id`)

### Sortie audio
**Priorité : ALSA** (sortie par défaut du système)
- Sélection du périphérique audio via config UI
- Commande : `aplay -D <device> <audio_file>`
- Lister périphériques : `aplay -L`

**Support optionnel PulseAudio** (si présent sur Ubuntu) :
- Détection automatique de PulseAudio
- Fallback sur ALSA si PulseAudio indisponible
- Commande : `paplay --device=<device> <audio_file>`

### Contrôle PTT
- GPIO sur Raspberry Pi (pin et niveau actif configurables)
- Mode mock pour Ubuntu/développement (simule PTT sans GPIO)
- Timing : `lead_ms` (attente avant audio) + `tail_ms` (attente après audio)
- Watchdog matériel : force PTT OFF après 30s maximum

## Points clés du schéma de base de données

### Table channels
- `station_visual_url_cache` : stocke l'URL originale collée par l'utilisateur
- `offsets_seconds_json` : tableau comme `[0, 1200, 2400]` pour plusieurs TX par mesure
- `voice_params_json` : paramètres spécifiques au moteur

### Table channel_runtime (1:1 avec channels)
- `last_measurement_at` : timestamp de la dernière mesure connue
- `next_tx_at` : prochaine heure de transmission planifiée
- Conserve l'état entre les cycles de polling

### Table tx_history
- Colonne `tx_id` avec contrainte UNIQUE (idempotence)
- `mode` : "SCHEDULED" ou "MANUAL_TEST"
- `status` : "PENDING" → "SENT"|"FAILED"|"ABORTED"
- Au démarrage : marquer les anciens PENDING (>120s) en ABORTED pour éviter TX obsolètes

### Table system_settings (ligne unique, id=1)
- `master_enabled` : coupe-circuit global
- `tx_timeout_seconds` : verrouillé à 30
- `inter_announcement_pause_seconds` : pause entre annonces séquentielles

## Système de templates
Variables V1 :
- `{station_name}`, `{wind_avg_kmh}`, `{wind_max_kmh}`, `{measurement_age_minutes}`
- Arrondi à l'entier par défaut
- Langue : français

Exemple : `"Station {station_name}, vent moyen {wind_avg_kmh} kilomètres par heure, rafales {wind_max_kmh}."`

## Fonctionnalités de test
**Prévisualisation (sans PTT) :** Bouton "Écouter la valeur actuelle" - utilise la mesure courante, bloqué si périmée  
**Test émission (avec PTT) :** Bouton "Test émission radio" - suit la procédure idempotente complète incluant journalisation PENDING

## Flux de développement

### Services (2 unités systemd)
```ini
# /etc/systemd/system/vhf-balise-web.service
[Unit]
Description=Passerelle VHF - Serveur Web
After=network.target

[Service]
Type=simple
User=vhf-balise
WorkingDirectory=/opt/vhf-balise
ExecStart=/opt/vhf-balise/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

```ini
# /etc/systemd/system/vhf-balise-runner.service
[Unit]
Description=Passerelle VHF - Runner
After=network.target vhf-balise-web.service

[Service]
Type=simple
User=vhf-balise
WorkingDirectory=/opt/vhf-balise
ExecStart=/opt/vhf-balise/venv/bin/python -m app.runner
Restart=always

[Install]
WantedBy=multi-user.target
```

### Structure de déploiement
```
/opt/vhf-balise/
├── app/               # Code source Python
├── frontend/          # Fichiers statiques HTML/CSS/JS
├── venv/              # Environnement virtuel Python
├── data/              # Dossier persistant
│   ├── vhf-balise.db  # Base SQLite
│   ├── audio_cache/   # Fichiers audio synthétisés
│   └── logs/          # Logs applicatifs
└── install.sh         # Script d'installation
```

### État par défaut (installation)
- `master_enabled=false`
- Tous les canaux désactivés
- Aucun identifiant provider configuré
- **AUCUNE transmission possible** jusqu'à configuration explicite par un admin

## Patterns courants

### Gestion d'erreur (fail-closed)
```python
try:
    # Opération critique
    measurement = get_measurement(channel)
    if is_expired(measurement, channel.measurement_period_seconds):
        raise MeasurementExpiredError()
    
    # Journaliser AVANT émission
    tx_record = insert_pending_tx(tx_id, measurement)
    db.commit()  # CRITIQUE : vérifier le commit
    
    # Émettre seulement si tout est OK
    transmit_with_ptt(audio_path)
    
except Exception as e:
    logger.error(f"Erreur : {e}")
    channel_runtime.last_error = str(e)
    # NE PAS émettre - fail silently (fail-closed)
    return
```

### Normalisation des mesures
```python
# Tous les providers doivent retourner :
{
    "measurement_at": datetime,  # UTC
    "wind_avg_kmh": float,
    "wind_max_kmh": float,
    "wind_min_kmh": Optional[float]
}
```

### Résolution de station depuis URL
```python
def resolve_station_from_visual_url(url: str) -> tuple[str, int, str]:
    """
    Retourne : (provider_id, station_id, station_name)
    Lève ValidationError si le parsing échoue
    """
```

## Structure des endpoints API
- `/api/auth/*` - Authentification
- `/api/providers/*` - Config providers + résolution de stations
- `/api/channels/*` - CRUD + activation/désactivation + tests
- `/api/tts/*` - Info moteurs + liste voix + prévisualisation
- `/api/tx/history` - Journal des transmissions
- `/api/status` - Statut système/canaux
- `/api/logs` - Logs filtrés

## Noms d'écrans UI (frontend)
- **Connexion** - Login admin
- **Tableau de bord** - Vue globale (master_enabled, état Runner, verrou TX, logs récents)
- **Configuration providers** - Saisie clé FFVL, infos OpenWindMap
- **Gestion des canaux** - Liste, CRUD, activation/désactivation par canal
- **Nouveau canal / Modifier canal** - Formulaire complet (balise par URL, template, voix, planning)
- **Simulation** - Timeline prévisionnelle des annonces par canal
- **Historique des émissions** - Filtres par canal, statut, période
- **Administration** - Gestion comptes, logs système
- **Paramètres système** - master_enabled, intervalles, config PTT/audio

## Tests automatisés

### Tests unitaires (obligatoires)
```python
# test_template.py
def test_template_rendering():
    """Vérifie le rendu des variables {station_name}, {wind_avg_kmh}, etc."""
    
# test_url_parsing.py
def test_ffvl_url_parsing():
    """Vérifie extraction idBalise depuis URLs FFVL"""
    
def test_openwindmap_url_parsing():
    """Vérifie extraction station_id depuis URLs OpenWindMap"""
    
# test_measurement_normalization.py
def test_provider_normalization():
    """Vérifie normalisation mesures (dates, unités)"""
    
# test_scheduling.py
def test_offset_calculation():
    """Vérifie calcul des tx_times depuis measurement_at + offsets"""
    
# test_idempotence.py
def test_tx_id_uniqueness():
    """Vérifie que tx_id empêche duplications"""
```

### Test d'intégration (obligatoire)
```python
# test_fail_safe_integration.py
def test_no_tx_on_db_commit_failure():
    """Vérifie qu'aucune émission ne part si DB/commit échoue"""
    # Mode mock PTT
    # Simuler échec commit
    # Vérifier PTT jamais activé
    
def test_no_tx_on_expired_measurement():
    """Vérifie qu'aucune émission ne part si mesure périmée"""
    # Mode mock PTT
    # Mesure avec measurement_at ancien
    # Vérifier PTT jamais activé
```

### Lancer les tests
```bash
cd /opt/vhf-balise
source venv/bin/activate
pytest tests/ -v
```

## Script d'installation minimal

```bash
#!/bin/bash
# install.sh - Installation Passerelle VHF

set -e

# Créer utilisateur système
sudo useradd -r -s /bin/false vhf-balise || true

# Créer répertoires
sudo mkdir -p /opt/vhf-balise/data/{audio_cache,logs}
sudo chown -R vhf-balise:vhf-balise /opt/vhf-balise

# Installer dépendances système
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip alsa-utils

# Créer environnement virtuel
cd /opt/vhf-balise
python3 -m venv venv
source venv/bin/activate

# Installer dépendances Python
pip install fastapi uvicorn sqlalchemy aiosqlite pydantic

# Installer Piper TTS
pip install piper-tts
# Télécharger modèle voix FR
mkdir -p data/tts_models
wget -O data/tts_models/fr_FR-siwis-medium.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/fr/fr_FR/siwis/medium/fr_FR-siwis-medium.onnx

# Copier services systemd
sudo cp vhf-balise-web.service /etc/systemd/system/
sudo cp vhf-balise-runner.service /etc/systemd/system/
sudo systemctl daemon-reload

# Initialiser DB
python -m app.init_db

echo "Installation terminée. Utilisez :"
echo "  sudo systemctl start vhf-balise-web"
echo "  sudo systemctl start vhf-balise-runner"
```

## Contraintes clés
- **Internet** : requis pour récupérer les mesures, PAS pour la synthèse vocale
- **Carte SD** : tout le code doit fonctionner de manière fiable sur stockage SD Raspberry Pi
- **Pas de secrets dans le code** : clés API uniquement via DB/UI
- **Watchdog** : 30s max de durée PTT (sécurité matérielle)
- **Locale** : langue française pour synthèse vocale et UI
