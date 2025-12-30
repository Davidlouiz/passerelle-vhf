# Guide de développement - Passerelle VHF

## Configuration de l'environnement de développement

### Prérequis
- Python 3.10+
- Ubuntu/Debian (ou Raspberry Pi OS pour test matériel)
- Git

### Installation locale

```bash
# Cloner le dépôt
git clone <repo-url>
cd "Passerelle VHF"

# Créer l'environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Créer les dossiers de données
mkdir -p data/{audio_cache,logs,tts_models}
export VHF_DATA_DIR=$(pwd)/data

# Initialiser la base de données
python -m app.init_db
```

### Lancement en mode développement

```bash
# Terminal 1 : API FastAPI
source venv/bin/activate
export VHF_DATA_DIR=$(pwd)/data
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 : Runner (optionnel)
source venv/bin/activate
export VHF_DATA_DIR=$(pwd)/data
python -m app.runner
```

### Lancer les tests

```bash
# Tous les tests
pytest tests/ -v

# Tests avec couverture
pytest tests/ --cov=app --cov-report=html

# Tests spécifiques
pytest tests/test_template.py -v
pytest tests/test_url_parsing.py -v
```

## Architecture du code

### Structure des modules

- **app/** : Code principal
  - **models.py** : Schéma SQLAlchemy (base de données)
  - **database.py** : Connexion et sessions DB
  - **auth.py** : Authentification JWT
  - **main.py** : Application FastAPI
  - **runner.py** : Scheduler/poller principal
  - **providers/** : Providers météo (FFVL, OpenWindMap)
  - **tts/** : Moteurs TTS (Piper)
  - **ptt/** : Contrôle PTT (GPIO, mock)
  - **services/** : Logique métier (template, transmission)

### Règles de développement

#### 1. Fail-Safe TOUJOURS
Toute fonction qui pourrait déclencher une émission DOIT :
- Vérifier que la mesure n'est pas périmée
- Journaliser en DB AVANT toute émission
- Vérifier le commit DB
- Gérer les exceptions proprement

```python
# ✅ Bon
try:
    if is_measurement_expired(measurement_at, period):
        raise MeasurementExpiredError()
    
    # Journaliser AVANT
    tx_record = insert_pending_tx(...)
    db.commit()  # Vérifier commit
    
    # Émettre seulement si tout OK
    await transmit(...)
except Exception as e:
    logger.error(f"Erreur: {e}")
    # NE PAS émettre
    return
```

#### 2. Idempotence
Toujours utiliser `tx_id` pour éviter les duplications :

```python
tx_id = compute_hash(
    channel_id, provider_id, station_id,
    measurement_at, rendered_text,
    engine_id, voice_id, voice_params,
    offset_seconds
)
```

#### 3. Tests obligatoires
Tout nouveau code doit avoir des tests :
- Tests unitaires pour la logique métier
- Tests d'intégration pour les flux critiques
- Mode mock PTT pour les tests

#### 4. Logging
Utiliser le logger Python, pas print() :

```python
import logging
logger = logging.getLogger(__name__)

logger.info("Opération normale")
logger.warning("Attention")
logger.error("Erreur", exc_info=True)
```

## Ajouter un nouveau provider

1. Créer `app/providers/nouveau_provider.py`
2. Implémenter l'interface `WeatherProvider`
3. Ajouter dans `app/providers/manager.py`
4. Créer les tests dans `tests/test_nouveau_provider.py`

Exemple :
```python
class NouveauProvider(WeatherProvider):
    @property
    def provider_id(self) -> str:
        return "nouveau"
    
    def resolve_station_from_url(self, url: str) -> StationInfo:
        # Parser l'URL
        ...
    
    async def fetch_measurement(self, station_id: str) -> Measurement:
        # Appeler l'API
        ...
```

## Ajouter un nouveau moteur TTS

1. Créer `app/tts/nouveau_engine.py`
2. Hériter de `TTSEngine`
3. Implémenter `list_voices()` et `synthesize()`
4. Le cache fonctionne automatiquement

Exemple :
```python
class NouveauEngine(TTSEngine):
    @property
    def engine_id(self) -> str:
        return "nouveau"
    
    def list_voices(self) -> List[Voice]:
        return [...]
    
    def synthesize(self, text, voice_id, output_path, params) -> str:
        # Générer l'audio
        ...
```

## Conventions de code

- **Style** : PEP 8
- **Docstrings** : Google style
- **Type hints** : Obligatoires pour les fonctions publiques
- **Langue** : Code en anglais, commentaires/docs en français

## Debug courant

### Problème : La DB est verrouillée
```bash
# Vérifier qu'aucun processus n'utilise la DB
lsof data/vhf-balise.db

# Si nécessaire, tuer les processus
pkill -f "python.*runner"
pkill -f "uvicorn.*main:app"
```

### Problème : Les tests échouent
```bash
# Vérifier les dépendances
pip install -r requirements.txt

# Vérifier la version Python
python --version  # Doit être 3.10+

# Lancer un test spécifique en verbose
pytest tests/test_xxx.py -vv -s
```

### Problème : Audio ne fonctionne pas
```bash
# Vérifier ALSA
aplay -L

# Tester un fichier audio
aplay /usr/share/sounds/alsa/Front_Center.wav

# Vérifier Piper
piper --version
```

## Contribuer

1. Fork le dépôt
2. Créer une branche (`git checkout -b feature/nouvelle-fonctionnalite`)
3. Commit les changements (`git commit -am 'Ajout nouvelle fonctionnalité'`)
4. Push vers la branche (`git push origin feature/nouvelle-fonctionnalite`)
5. Créer une Pull Request

### Checklist avant PR

- [ ] Les tests passent (`pytest tests/`)
- [ ] Le code suit PEP 8 (`flake8 app/`)
- [ ] La documentation est à jour
- [ ] Les nouvelles fonctionnalités ont des tests
- [ ] Aucun secret/clé API en dur dans le code
- [ ] Les règles fail-safe sont respectées

## Ressources

- Documentation Piper TTS : https://github.com/rhasspy/piper
- API Pioupiou : http://developers.pioupiou.fr/api.html
- FastAPI : https://fastapi.tiangolo.com/
- SQLAlchemy : https://docs.sqlalchemy.org/
