# Instructions Copilot - Passerelle VHF

## Contexte système
Radio VHF multi-canaux qui annonce vocalement les mesures météo. **Fail-safe critique** : aucune émission radio ne doit partir si une seule condition de sécurité échoue.

**Stack** : Python 3.10+ | FastAPI | SQLite | Piper TTS | GPIO PTT  
**Déploiement** : Raspberry Pi (`/opt/vhf-balise/`) ou dev local (`./data/`)  
**Architecture** : 2 processus - `uvicorn app.main:app` (API web) + `python -m app.runner` (scheduler TX)

## Développement rapide

```bash
./dev.sh                    # Affiche commandes dev + init DB si besoin
source venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000  # Terminal 1
python -m app.runner                                         # Terminal 2
pytest tests/ -v            # Tests (fail-safe = critique)
```

**DB locale** : auto-créée dans `./data/vhf-balise.db` (VHF_DATA_DIR non défini)  
**DB prod** : `export VHF_DATA_DIR=/opt/vhf-balise/data` (voir [app/database.py](app/database.py#L18-L22))

## ⚠️ Contrainte absolue : Fail-Safe

**Règle d'or** : Journaliser AVANT d'émettre. Aucune TX si échec commit ou mesure périmée.

### Séquence TX obligatoire ([app/runner.py](app/runner.py), [app/services/transmission.py](app/services/transmission.py))
```python
# 1. Vérifier mesure non périmée (app.utils.is_measurement_expired)
# 2. Rendre template + obtenir audio (cache-first)
# 3. Calculer tx_id = hash(channel_id, station_id, measurement_at, text...)
# 4. INSERT tx_history status="PENDING" + COMMIT (si échoue → STOP, pas de TX)
# 5. Re-vérifier péremption
# 6. Acquérir verrou TX global (_tx_lock)
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
1. **Web** (`app/main.py`) : FastAPI sert `/api/*` + `static/*` (frontend HTML/CSS/JS)
2. **Runner** (`app/runner.py`) : Boucle asyncio qui poll providers → planifie TX → exécute avec PTT

### Base de données ([app/models.py](app/models.py))
**Tables critiques** :
- `channels` : config canal (provider_id, station_id, template, voix, offsets)
- `channel_runtime` : état (last_measurement_at, next_tx_at, last_error) - 1:1 avec channels
- `tx_history` : journal TX avec `tx_id UNIQUE` (idempotence) + status PENDING→SENT/FAILED/ABORTED
- `system_settings` : master_enabled, ptt_gpio_pin, audio_device (ligne unique id=1)
- `provider_credentials` : clés API par provider (ex: ffvl_key)

**Au démarrage runner** : marquer anciens PENDING (>120s) en ABORTED (évite TX obsolètes)

### Providers météo ([app/providers/](app/providers/))
Abstraction `WeatherProvider` + singleton `provider_manager`.

**FFVL** ([ffvl.py](app/providers/ffvl.py)) : Requiert `ffvl_key` dans credentials, ajouter `&key={ffvl_key}` à toutes URLs API  
**OpenWindMap** ([openwindmap.py](app/providers/openwindmap.py)) : Aucune auth, fetch groupé `/v1/live/all` optimisé

**Normalisation obligatoire** : Tous providers retournent `Measurement(measurement_at: datetime, wind_avg_kmh, wind_max_kmh, wind_min_kmh)` - dates UTC timezone-aware.

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
    db.commit()  # Explicite !
```

### Résolution station depuis URL visuelle
Provider parse URL utilisateur → extrait `(provider_id, station_id)` :
- FFVL : `balisemeteo.com/balise.php?idBalise=67` → `("ffvl", "67")`
- OpenWindMap : `openwindmap.org/pioupiou-385` → `("openwindmap", "385")`

Voir [app/routers/providers.py](app/routers/providers.py) endpoint `/resolve`.

### Templates ([app/services/template.py](app/services/template.py))
Variables : `{station_name}`, `{wind_avg_kmh}`, `{wind_max_kmh}`, `{wind_direction_name}`  
**Prononciation TTS** : "Este" au lieu de "Est" (liaison phonétique), "Oueste" au lieu de "Ouest"

### Frontend statique
Fichiers dans `static/` (copie de `frontend/`) servis par FastAPI `StaticFiles`. Pas de framework JS - vanilla uniquement.

## Tests critiques

**Fail-safe** : [tests/test_fail_safe_integration.py](tests/test_fail_safe_integration.py) - vérifie qu'aucune TX si mesure périmée OU commit échoue  
**Idempotence** : [tests/test_idempotence.py](tests/test_idempotence.py) - tx_id unique empêche duplications  
**Tous** : `pytest tests/ -v` (utilise MockPTTController, DB SQLite in-memory)
