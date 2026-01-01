# Instructions Copilot - Passerelle VHF

## Contexte système
Radio VHF multi-canaux qui annonce vocalement les mesures météo. **Fail-safe critique** : aucune émission radio ne doit partir si une seule condition de sécurité échoue.

**Stack** : Python 3.10+ | FastAPI | SQLite | Piper TTS | GPIO PTT  
**Déploiement** : Raspberry Pi (`/opt/vhf-balise/`) ou dev local (`./data/`)  
**Architecture** : 2 processus - `uvicorn app.main:app` (API web) + `python -m app.runner` (scheduler TX)  
**⚠️ VERROU PID OBLIGATOIRE** : Runner utilise `data/runner.pid` pour empêcher instances multiples (fail-safe critique anti-doublons TX)

## Développement rapide

```bash
./dev.sh                    # Affiche commandes dev + init DB si besoin
source venv/bin/activate    # ⚠️ OBLIGATOIRE avant toute commande Python
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000  # Terminal 1
python -m app.runner                                         # Terminal 2
pytest tests/ -v            # Tests (fail-safe = critique, inclut tests async)
pytest tests/ -v --cov      # Tests avec couverture de code
```

**DB locale** : auto-créée dans `./data/vhf-balise.db` (VHF_DATA_DIR non défini)  
**DB prod** : `export VHF_DATA_DIR=/opt/vhf-balise/data` (voir [app/database.py](app/database.py#L18-L22))  
**Init manuelle DB** : `python -m app.init_db` (si `./dev.sh` ne suffit pas)  
**⚠️ Venv OBLIGATOIRE** : Toujours `source venv/bin/activate` avant toute commande Python (pytest, runner, etc.)  
**Test complet** : Les 2 processus doivent tourner ensemble en dev pour tester l'architecture complète

## ⚠️ Contrainte absolue : Fail-Safe

**Règle d'or** : Journaliser AVANT d'émettre. Aucune TX si échec commit ou mesure périmée.

### Séquence TX obligatoire ([app/runner.py](app/runner.py), [app/services/transmission.py](app/services/transmission.py))
```python
# 1. Vérifier mesure non périmée (app.utils.is_measurement_expired)
# 2. Rendre template + obtenir audio (cache-first)
# 3. Calculer tx_id = hash(channel_id, station_id, measurement_at, text...) via compute_tx_id()
# 4. INSERT tx_history status="PENDING" + COMMIT (si échoue → STOP, pas de TX)
# 5. Re-vérifier péremption
# 6. Acquérir verrou TX global (_tx_lock threading.Lock)
# 7. PTT ON → lead_ms → play audio → tail_ms → PTT OFF
# 8. UPDATE status="SENT"|"FAILED" + COMMIT
```

**Conditions requises** (échec = pas de TX) :
- `system_settings.master_enabled=true`
- Canal activé (`channel.is_enabled=true`)
- Provider credentials présents
- Mesure fraîche : `now - measurement_at <= measurement_period_seconds`
- Audio existe OU synthèse réussie
- Commit DB réussi

### Verrou TX global
Un SEUL PTT pour tous canaux. Si N annonces dues simultanément : shuffle ordre + exécuter séquentiellement avec pause `inter_announcement_pause_seconds` (10s) entre chaque.

## Architecture clé

### Deux processus indépendants
1. **Web** (`app/main.py`) : FastAPI (uvicorn) sert `/api/*` + `static/*` (frontend HTML/CSS/JS)
2. **Runner** (`app/runner.py`) : Boucle asyncio (`async def run()`) qui poll providers → planifie TX → exécute avec PTT. Un seul runner actif à la fois.

### Base de données ([app/models.py](app/models.py))
**Tables critiques** :
- `users` : authentification (username, password_hash, must_change_password) - compte par défaut `admin`/`admin`
- `channels` : config canal (provider_id, station_id, template, voix, offsets)
- `channel_runtime` : état (last_measurement_at, next_tx_at, last_error) - 1:1 avec channels
- `tx_history` : journal TX avec `tx_id UNIQUE` (idempotence) + status PENDING→SENT/FAILED/ABORTED
- `system_settings` : master_enabled, ptt_gpio_pin, audio_device (ligne unique id=1)
- `provider_credentials` : clés API par provider (ex: ffvl_key)
- `audio_cache` : cache TTS (engine_id, voice_id, text_hash) → chemin fichier WAV

**⚠️ Timezone critique** : 
- **SQLite limitation** : SQLite ne supporte pas les timezones natives. Même avec `DateTime(timezone=True)`, les datetimes sont stockés/lus comme naïfs.
- **Solution** : Tous les datetimes sont **convertis en UTC puis stockés sans timezone** (UTC naïf) via `.replace(tzinfo=None)`.
- **Règle absolue** : Toute date écrite en base DOIT être `datetime.utcnow()` ou `dt.astimezone(pytz.UTC).replace(tzinfo=None)`.
- **Lecture** : Les datetimes lus sont traités comme UTC naïfs (via `format_utc_datetime()` dans routers).
- **Comparaisons** : Toujours comparer des UTC naïfs entre eux (voir `_update_channel_measurement()` dans runner.py).

**Au démarrage runner** : 
1. **Verrou PID** : acquérir `data/runner.pid` via `acquire_pid_lock()` - refuse démarrage si autre runner actif
2. Marquer anciens PENDING (planned_at > 1h) en ABORTED (évite TX obsolètes)  
**Au shutdown runner** : libérer PID via `release_pid_lock()` (garanti par finally block)

### Providers météo ([app/providers/](app/providers/))
Abstraction `WeatherProvider` + singleton `provider_manager`.

**FFVL** ([ffvl.py](app/providers/ffvl.py)) :  
- Requiert `ffvl_key` dans credentials (via `api_key`), ajouter `&key={api_key}` à toutes URLs API  
- **Timezone API** : dates retournées en heure locale Paris (Europe/Paris) - TOUJOURS convertir en UTC avec pytz :
  ```python
  dt_naive = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
  paris_tz = pytz.timezone("Europe/Paris")
  dt_paris = paris_tz.localize(dt_naive)
  measurement_at = dt_paris.astimezone(pytz.UTC)  # ← Obligatoire !
  ```
- Validation clé : endpoint `/list` retourne JSON si valide, HTML si invalide

**OpenWindMap** ([openwindmap.py](app/providers/openwindmap.py)) : Aucune auth, fetch groupé `/v1/live/all` optimisé, dates déjà UTC

**Normalisation obligatoire** : Tous providers retournent `Measurement(measurement_at: datetime, wind_avg_kmh, wind_max_kmh, wind_min_kmh)` - dates UTC timezone-aware obligatoires  
**Pattern async** : Toutes requêtes HTTP via `async def fetch_measurement()` - utiliser `await` dans runner

### TTS cache-first ([app/tts/](app/tts/))
**Moteur** : Piper ([piper_engine.py](app/tts/piper_engine.py)) - 6 voix FR dans `data/tts_models/*.onnx`  
**Cache** ([cache.py](app/tts/cache.py)) : clé = hash(engine_id, voice_id, voice_params, text) → table `audio_cache` + fichier disque  
**JAMAIS régénérer** un audio existant (économie CPU Raspberry Pi)

### PTT ([app/ptt/controller.py](app/ptt/controller.py))
**GPIO** si Raspberry Pi (pin configurable) OU **Mock** si dev Ubuntu (log seulement)  
**Watchdog** : force PTT OFF après 30s max (sécurité matérielle)

## Patterns projet-spécifiques

### Gestion sessions DB
```python
# Dans routers FastAPI
def endpoint(db: Session = Depends(get_db)):  # get_db auto-close session

# Dans runner (hors FastAPI)
from app.database import get_db_session
with get_db_session() as db:
    # faire ops
    db.commit()  # Explicite ! (pas de auto-commit)
```

**IMPORTANT** : Dans le runner, TOUJOURS commit explicitement. Pas de auto-commit dans ce projet.

### Résolution station depuis URL visuelle
Provider parse URL utilisateur → extrait `(provider_id, station_id)` :
- FFVL : `balisemeteo.com/balise.php?idBalise=67` → `("ffvl", "67")`
- OpenWindMap : `openwindmap.org/pioupiou-385` → `("openwindmap", "385")`

Voir [app/routers/providers.py](app/routers/providers.py) endpoint `/resolve`.

### Templates ([app/services/template.py](app/services/template.py))
Variables : `{station_name}`, `{wind_avg_kmh}`, `{wind_max_kmh}`, `{wind_direction_name}`  
**Prononciation TTS** : "Este" au lieu de "Est" (liaison phonétique), "Oueste" au lieu de "Ouest"

### Frontend statique
Fichiers dans `frontend/` servis directement par FastAPI (`app.mount("/static", StaticFiles(directory="frontend"))`). Pas de framework JS - vanilla uniquement.

**Auth JWT** : Token stocké dans `localStorage`, envoyé via header `Authorization: Bearer <token>`  
**Helper fetch** : Utiliser `authenticatedFetch(url, options)` (dans [common.js](frontend/js/common.js)) au lieu de `fetch()` - gère auto header + redirect 401  
**Workflow modif frontend** : Éditer `frontend/*` directement → reload navigateur (pas de copie vers `static/` nécessaire)

## Authentification ([app/auth.py](app/auth.py))

**Login** : POST `/api/auth/login` → retourne JWT (expire 8h)  
**Compte par défaut** : `admin` / `admin` (CHANGER en production via UI ou POST `/api/auth/change-password`)  
**Protection endpoints** : Dependency `current_user = Depends(get_current_user)` sur tous routers sauf `/api/auth/login`  
**Frontend** : `authenticatedFetch()` ajoute header JWT + redirige vers login si 401

## Gestion erreurs

**Exceptions custom** ([app/exceptions.py](app/exceptions.py)) : `MeasurementExpiredError`, `ProviderError`, `TTSError`, `PTTError`, `ValidationError`, `AuthenticationError` - toutes héritent de `VHFBaseException`  
**API HTTP** : Lever `HTTPException(status_code=404, detail="...")` dans routers FastAPI  
**Runner** : Logger erreurs + marquer TX status="FAILED" avec error_message - JAMAIS propager exception qui stopperait le runner

## Tests critiques
(via `compute_tx_id()` dans [app/utils.py](app/utils.py))  
**Tests async** : Utiliser `@pytest.mark.asyncio` + `async def test_*()` pour tests async (transmission, providers) 
**Fail-safe** : [tests/test_fail_safe_integration.py](tests/test_fail_safe_integration.py) - vérifie qu'aucune TX si mesure périmée OU commit échoue  
**Idempotence** : [tests/test_idempotence.py](tests/test_idempotence.py) - tx_id unique empêche duplications  
**Tous** : `pytest tests/ -v` (utilise MockPTTController, DB SQLite in-memory)  
**Fixture commune** : [tests/conftest.py](tests/conftest.py) fournit `db_session` (SQLite in-memory + auto-cleanup)

## Débogage & Logs

**Logs runner** : `./data/logs/runner.log` ou `journalctl -u vhf-balise-runner -f` (prod)  
**Logs web** : `journalctl -u vhf-balise-web -f` (prod) ou stdout terminal dev  
**SQL debug** : Mettre `echo=True` dans [app/database.py](app/database.py#L30) `create_engine()`  
**Audio dev** : Cache TTS dans `./data/audio_cache/` - supprimer pour forcer régénération test

## Production (Raspberry Pi)

**Services systemd** :
```bash
sudo systemctl status vhf-balise-web      # État API
sudo systemctl status vhf-balise-runner   # État runner
sudo systemctl restart vhf-balise-web     # Redémarrer API
sudo systemctl restart vhf-balise-runner  # Redémarrer runner
sudo journalctl -u vhf-balise-runner -f   # Logs temps réel
```

**Installation** : `sudo ./install.sh` (déploie vers `/opt/vhf-balise/`, crée user `vhf-balise`, installe services)  
**Compte par défaut** : `admin`/`admin` → http://raspberry-ip:8000 (CHANGER le mot de passe immédiatement)
