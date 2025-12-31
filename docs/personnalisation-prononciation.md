# Personnalisation de la prononciation TTS

💡 **Pour qui ?** Utilisateurs avancés et administrateurs système souhaitant optimiser la prononciation des directions du vent.

⚠️ **Niveau** : Technique - Requiert des connaissances en édition de fichiers et redémarrage de services.

## 🎯 Pourquoi personnaliser ?

Les moteurs de synthèse vocale (TTS) peuvent parfois mal prononcer certains mots. Le système utilise déjà des optimisations pour le français :
- **"Este"** au lieu de **"Est"** → Meilleure liaison phonétique dans "Nord-Este"
- **"Oueste"** au lieu de **"Ouest"** → Prononciation plus claire

Mais vous pouvez vouloir :
- Adapter à une voix spécifique
- Simplifier les directions (abréviations)
- Ajouter des pauses
- Revenir aux directions standard

## 🔊 Prononciations actuelles (optimisées)

## 🔊 Prononciations actuelles (optimisées)

| Degrés | Direction standard | Prononciation système | Résultat vocal |
|--------|-------------------|----------------------|----------------|
| 0° | Nord | Nord | "Nord" |
| 22.5° | Nord-Nord-Est | Nord-Nord-Este | "Nord-Nord-Este" |
| 45° | Nord-Est | Nord-Este | "Nord-Este" |
| 67.5° | Est-Nord-Est | **Este-Nord-Este** | "Este-Nord-Este" ⭐ |
| 90° | Est | Este | "Este" |
| 112.5° | Est-Sud-Est | Este-Sud-Este | "Este-Sud-Este" |
| 135° | Sud-Est | Sud-Este | "Sud-Este" |
| 157.5° | Sud-Sud-Est | Sud-Sud-Este | "Sud-Sud-Este" |
| 180° | Sud | Sud | "Sud" |
| 202.5° | Sud-Sud-Ouest | Sud-Sud-Oueste | "Sud-Sud-Oueste" |
| 225° | Sud-Ouest | Sud-Oueste | "Sud-Oueste" |
| 247.5° | Ouest-Sud-Ouest | Oueste-Sud-Oueste | "Oueste-Sud-Oueste" |
| 270° | Ouest | Oueste | "Oueste" |
| 292.5° | Ouest-Nord-Ouest | Oueste-Nord-Oueste | "Oueste-Nord-Oueste" |
| 315° | Nord-Ouest | Nord-Oueste | "Nord-Oueste" |
| 337.5° | Nord-Nord-Ouest | Nord-Nord-Oueste | "Nord-Nord-Oueste" |

⭐ **Optimisations phonétiques** :
- `"Este"` au lieu de `"Est"` quand suivi d'un tiret → meilleure liaison
- `"Oueste"` au lieu de `"Ouest"` → prononciation plus claire pour le TTS français

## 🛠️ Comment modifier (utilisateurs avancés)

### Méthode 1 : Tester sans modification (recommandé d'abord)

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
