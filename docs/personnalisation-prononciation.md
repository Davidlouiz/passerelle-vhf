# Personnalisation de la prononciation TTS

## 🔊 Directions du vent

Les directions du vent peuvent être personnalisées pour améliorer leur prononciation par les moteurs de synthèse vocale.

### Fichier à modifier

**📁 Fichier** : `app/services/template.py`  
**🔍 Fonction** : `degrees_to_name()`

### Prononciations par défaut

| Degrés | Direction | Prononciation optimisée |
|--------|-----------|-------------------------|
| 0° | Nord | Nord |
| 22.5° | Nord-Nord-Est | Nord-Nord-Este |
| 45° | Nord-Est | Nord-Este |
| 67.5° | Est-Nord-Est | **Este-Nord-Este** ⭐ |
| 90° | Est | Este |
| 112.5° | Est-Sud-Est | Este-Sud-Este |
| 135° | Sud-Est | Sud-Este |
| 157.5° | Sud-Sud-Est | Sud-Sud-Este |
| 180° | Sud | Sud |
| 202.5° | Sud-Sud-Ouest | Sud-Sud-Oueste |
| 225° | Sud-Ouest | Sud-Oueste |
| 247.5° | Ouest-Sud-Ouest | Oueste-Sud-Oueste |
| 270° | Ouest | Oueste |
| 292.5° | Ouest-Nord-Ouest | Oueste-Nord-Oueste |
| 315° | Nord-Ouest | Nord-Oueste |
| 337.5° | Nord-Nord-Ouest | Nord-Nord-Oueste |

⭐ **Optimisations appliquées** :
- `"Este"` au lieu de `"Est"` quand suivi d'un tiret → meilleure liaison phonétique
- `"Oueste"` au lieu de `"Ouest"` → prononciation plus claire

### Comment personnaliser

#### 1️⃣ Ouvrir le fichier

```bash
nano app/services/template.py
# ou
vim app/services/template.py
```

#### 2️⃣ Localiser la section

Chercher le commentaire :
```python
# 🔊 PERSONNALISATION PRONONCIATION TTS
```

#### 3️⃣ Modifier les valeurs

```python
names = [
    "Nord",              # 0° (360°)
    "Nord-Nord-Este",    # 22.5° ← Modifiez ici
    "Nord-Este",         # 45°
    "Este-Nord-Este",    # 67.5°
    # ... etc
]
```

#### 4️⃣ Redémarrer le serveur

```bash
# Si en mode développement (--reload), les changements sont automatiques
# Sinon, redémarrer :
sudo systemctl restart vhf-balise-web
```

### Exemples de modifications

#### Ralentir la prononciation
Ajouter des espaces pour forcer des pauses :

```python
names = [
    "Nord",
    "Nord - Nord - Este",  # Pauses entre chaque mot
    "Nord - Este",
    # ...
]
```

#### Simplifier les directions
Utiliser des noms plus courts :

```python
names = [
    "Nord",
    "NNE",  # Abrégé
    "NE",
    "ENE",
    # ...
]
```

#### Prononciation alternative
Si une direction est mal prononcée :

```python
names = [
    "Nord",
    "Nord-Nord-Est",  # Revenir à "Est" si "Este" pose problème
    # ...
]
```

### Tester vos modifications

1. **Via l'interface web** :
   - Aller dans "Balises" → "Nouvelle balise"
   - Utiliser le template : `Direction du vent : {wind_direction_name}`
   - Cliquer sur "🎧 Écouter le rendu"

2. **Via l'API** :
   ```bash
   curl -X POST http://localhost:8000/api/tts/synthesize \
     -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "text": "Direction Este-Nord-Este",
       "voice_id": "fr_FR-siwis-medium"
     }'
   ```

3. **Avec un script Python** :
   ```python
   from app.services.template import degrees_to_name
   
   # Tester une direction
   print(degrees_to_name(67.5))  # Affiche: "Este-Nord-Este"
   ```

### Autres variables personnalisables

Dans le même fichier `app/services/template.py`, vous pouvez aussi personnaliser :

#### Directions cardinales courtes

Fonction `degrees_to_cardinal()` :
```python
directions = [
    "N",   # Nord
    "NNE", # Nord-Nord-Est
    "NE",  # Nord-Est
    # ... modifier ici pour changer les abréviations
]
```

## 💡 Conseils

1. **Testez toujours** après modification avec plusieurs voix
2. **Notez vos changements** dans un fichier séparé pour ne pas les perdre lors des mises à jour
3. **Évitez les caractères spéciaux** qui pourraient poser problème au TTS
4. **Privilégiez la phonétique française** : "Este", "Oueste" plutôt que "Est", "Ouest"

## 🔄 Retour aux valeurs par défaut

Si vos modifications ne donnent pas le résultat souhaité :

```bash
git checkout app/services/template.py
sudo systemctl restart vhf-balise-web
```

## 📝 Support

Les modifications de prononciation sont spécifiques à votre installation et ne sont **pas** écrasées par les mises à jour du système si vous utilisez une branche personnalisée.

Pour conserver vos personnalisations lors d'une mise à jour :
```bash
# Sauvegarder vos modifications
git stash

# Mettre à jour
git pull

# Réappliquer vos modifications
git stash pop
```
