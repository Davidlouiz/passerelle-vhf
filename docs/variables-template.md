# Variables pour templates d'annonce vocale

Les templates vous permettent de personnaliser exactement ce qui sera annoncé sur la radio. Ce guide vous explique toutes les variables disponibles et comment les utiliser.

## 🎯 Principe des templates

Un template est un texte avec des **variables entre accolades** qui sont remplacées automatiquement par les valeurs réelles.

**Exemple** :
```
Template: "Balise de {station_name}, {wind_avg_kmh} kilomètres par heure"
Résultat: "Balise de Annecy, douze kilomètres par heure"
```

💡 **Conseil** : Utilisez le bouton **🎧 Écouter le rendu** pour tester avant de sauvegarder !

## 📋 Variables disponibles

### 📍 Informations sur la station

| Variable | Description | Exemple de valeur | Rendu vocal |
|----------|-------------|------------------|-------------|
| `{station_name}` | Nom de la balise météo | `"Annecy"` | "Annecy" |

### 🌬️ Mesures de vent (vitesse)

| Variable | Description | Exemple de valeur | Rendu vocal |
|----------|-------------|------------------|-------------|
| `{wind_avg_kmh}` | Vent moyen en km/h (arrondi) | `12.4 → 12` | "douze" |
| `{wind_max_kmh}` | Rafales (vent maximum) en km/h | `18.7 → 19` | "dix-neuf" |
| `{wind_min_kmh}` | Vent minimum en km/h ⚠️ | `8.2 → 8` | "huit" |

⚠️ **Note** : `wind_min_kmh` n'est pas disponible avec tous les providers météo.

### 🧭 Direction du vent

| Variable | Description | Exemple de valeur | Rendu vocal |
|----------|-------------|------------------|-------------|
| `{wind_direction_name}` | Direction en français complet | `"Nord-Este"` | "Nord-Este" |
| `{wind_direction_deg}` | Direction en degrés (0-359) | `45` | "quarante-cinq" |

**Directions disponibles** : Nord, Nord-Nord-Este, Nord-Este, Este-Nord-Este, Este, Este-Sud-Este, Sud-Este, Sud-Sud-Este, Sud, Sud-Sud-Oueste, Sud-Oueste, Oueste-Sud-Oueste, Oueste, Oueste-Nord-Oueste, Nord-Oueste, Nord-Nord-Oueste

💡 **Pourquoi "Este" et "Oueste" ?** Optimisation phonétique pour meilleure prononciation TTS.

### ⏱️ Fraîcheur des données

| Variable | Description | Exemple de valeur | Rendu vocal |
|----------|-------------|------------------|-------------|
| `{measurement_age_minutes}` | Ancienneté de la mesure (minutes) | `15.3 → 15` | "quinze" |

## 📝 Exemples de templates

### 🥇 Template par défaut (recommandé)
### 🥇 Template par défaut (recommandé)

```
Balise de {station_name}, {wind_direction_name}, {wind_avg_kmh} kilomètres par heure, {wind_max_kmh} maximum, il y a {measurement_age_minutes} minutes.
```

**Rendu avec données réelles** :
- Station : Annecy
- Direction : 45° (Nord-Este)
- Vent moyen : 12 km/h
- Rafales : 18 km/h
- Mesure : il y a 5 minutes

**Résultat vocal** :
> "Balise de Annecy, Nord-Este, douze kilomètres par heure, dix-huit maximum, il y a cinq minutes."

**✅ Avantages** : Complet, professionnel, format standard parapente/deltaplane.

---

### ⚡ Template court (annonces fréquentes)

```
{station_name}, {wind_direction_name} {wind_avg_kmh}, rafales {wind_max_kmh}.
```

**Résultat vocal** :
> "Annecy, Nord-Este douze, rafales dix-huit."

**✅ Avantages** : Rapide, moins de temps d'émission, idéal pour annonces toutes les 15 min.

---

### 📊 Template détaillé avec minimum

```
Balise {station_name}, vent {wind_direction_name}, moyenne {wind_avg_kmh}, rafales {wind_max_kmh}, minimum {wind_min_kmh} kilomètres par heure.
```

**Résultat vocal** :
> "Balise Annecy, vent Nord-Este, moyenne douze, rafales dix-huit, minimum huit kilomètres par heure."

**✅ Avantages** : Très complet, utile pour analyses détaillées du vent.  
**⚠️ Attention** : Variable `{wind_min_kmh}` pas toujours disponible !

---

### 🧭 Template avec degrés (utilisateurs avancés)

```
Station {station_name}, direction {wind_direction_deg} degrés, vent moyen {wind_avg_kmh} kilomètres par heure.
```

**Résultat vocal** :
> "Station Annecy, direction quarante-cinq degrés, vent moyen douze kilomètres par heure."

**✅ Avantages** : Précision maximale pour pilotes expérimentés.

---

### 🎯 Template style "info pilotes"

```
Attention parapentistes, balise {station_name}, vent secteur {wind_direction_name}, {wind_avg_kmh} kilomètres heure en moyenne, pointes à {wind_max_kmh}.
```

**Résultat vocal** :
> "Attention parapentistes, balise Annecy, vent secteur Nord-Este, douze kilomètres heure en moyenne, pointes à dix-huit."

**✅ Avantages** : Vocabulaire adapté, alerte claire pour les pilotes.

## 🎨 Créer son propre template

### Étape 1 : Partir d'un template de base

Utilisez le template par défaut comme point de départ.

### Étape 2 : Ajouter/retirer des variables

**Ajouter une information** :
```
Balise de {station_name}, secteur {wind_direction_name}, {wind_avg_kmh} kilomètres par heure, rafales {wind_max_kmh}, mesure d'il y a {measurement_age_minutes} minutes.
```

**Retirer une information** (vent min) :
```
{station_name}, {wind_direction_name}, {wind_avg_kmh} km/h moyen, {wind_max_kmh} en rafales.
```

### Étape 3 : Personnaliser le vocabulaire

Exemples de variations :

| Standard | Personnalisé | Effet |
|----------|-------------|-------|
| "kilomètres par heure" | "kilomètres heure" | Plus court |
| "maximum" | "en rafales" / "en pointes" | Vocabulaire aéronautique |
| "il y a X minutes" | "mesure d'il y a X minutes" | Plus précis |
| "Balise de" | "Station" / "Balise météo" | Variation de style |

### Étape 4 : Tester avec 🎧 "Écouter le rendu"

**Toujours tester avant de sauvegarder !**

1. Entrez votre template dans l'interface
2. Cliquez sur 🎧 "Écouter le rendu"
3. Le système utilise les données réelles de la station
4. Écoutez et ajustez jusqu'à satisfaction

## ⚠️ Erreurs courantes à éviter

### ❌ Oublier les accolades

```
Mauvais: Balise de station_name
Bon:     Balise de {station_name}
```

→ Sans `{}`, le texte littéral "station_name" sera prononcé !

### ❌ Variable inexistante

```
Mauvais: {temperature_celsius}
```

→ La variable n'existe pas. Consultez la liste ci-dessus.

### ❌ Fautes de frappe dans les variables

```
Mauvais: {wind_avg_kph}  (kph au lieu de kmh)
Bon:     {wind_avg_kmh}
```

→ Le système ne remplacera pas la variable et dira le texte littéral.

### ❌ Template trop long

```
Attention : "Bonjour, voici l'annonce météo de la balise de {station_name} située à mille mètres d'altitude, avec un vent de direction {wind_direction_name}..."
```

→ Les templates très longs :
- Prennent beaucoup de temps d'émission
- Occupent la fréquence trop longtemps
- Peuvent lasser les auditeurs

**Recommandation** : Rester sous 30 secondes d'annonce.

### ❌ Utiliser `wind_min_kmh` sans vérifier

```
Risqué: {wind_min_kmh}
```

→ Cette variable n'est pas disponible avec tous les providers !

**Solution** : Tester avec votre source de données ou ne l'utiliser que si vous êtes sûr.

## 💡 Astuces de personnalisation

### Adapter la prononciation

Le TTS prononce le texte **littéralement**. Jouez sur l'orthographe :

| Problème | Mauvais | Bon | Raison |
|----------|---------|-----|--------|
| "Est" mal prononcé | {wind_direction_name} = "Nord-Est" | Système utilise "Nord-Este" | Meilleure liaison phonétique |
| Nombres mal dits | "14 km/h" | "quatorze kilomètres heure" | Plus clair |
| Pauses manquantes | "Annecy,Nord,12" | "Annecy, Nord, douze" | Les virgules créent des pauses |

💡 Le système fait déjà des optimisations phonétiques ("Este", "Oueste"), pas besoin de modifier.

### Ajouter du contexte

Exemples de contexte utile :

```
Attention, conditions de vol, balise {station_name}, {wind_direction_name} {wind_avg_kmh} kilomètres heure.
```

```
Bulletin météo parapente, site de {station_name}, vent {wind_direction_name}, moyenne {wind_avg_kmh}, rafales {wind_max_kmh}.
```

### Adapter le rythme

**Lent et posé** (ajoutez des virgules pour les pauses) :
```
Balise de {station_name}, direction du vent, {wind_direction_name}, vitesse moyenne, {wind_avg_kmh} kilomètres par heure.
```

**Rapide et direct** (peu de ponctuation) :
```
{station_name} {wind_direction_name} {wind_avg_kmh} rafales {wind_max_kmh}
```

## 🔍 Variables techniques (référence développeurs)

Ces variables sont calculées automatiquement par le système :

| Variable | Type | Format | Source |
|----------|------|--------|--------|
| `{station_name}` | Texte | Variable | API provider |
| `{wind_avg_kmh}` | Nombre | Entier | API provider (arrondi) |
| `{wind_max_kmh}` | Nombre | Entier | API provider (arrondi) |
| `{wind_min_kmh}` | Nombre | Entier | API provider (arrondi) |
| `{wind_direction_deg}` | Nombre | 0-359 | API provider |
| `{wind_direction_name}` | Texte | Nom français | Calculé depuis degrés |
| `{measurement_age_minutes}` | Nombre | Entier | Calculé (now - timestamp) |

## 📚 Exemples réels par activité

### 🪂 Parapente / Deltaplane

```
Décollage de {station_name}, vent {wind_direction_name}, force {wind_avg_kmh}, rafales {wind_max_kmh} kilomètres heure.
```

### 🪁 Kitesurf

```
Spot de {station_name}, {wind_direction_name} {wind_avg_kmh} en moyenne, {wind_max_kmh} en rafales.
```

### ✈️ Vol à voile (planeur)

```
Station {station_name}, vent au sol {wind_direction_deg} degrés, {wind_avg_kmh} kilomètres heure.
```

## 📖 Ressources complémentaires

- **[voix-disponibles.md](voix-disponibles.md)** - Choisir la meilleure voix pour vos annonces
- **[personnalisation-prononciation.md](personnalisation-prononciation.md)** - Ajuster la prononciation des directions
- **[GUIDE_UTILISATEUR.md](GUIDE_UTILISATEUR.md)** - Créer et gérer vos balises

---

**🎯 Bon template !**  
N'oubliez pas : **Testez toujours avec 🎧** avant de valider.
