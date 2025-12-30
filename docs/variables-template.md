# Variables disponibles pour les templates d'annonce vocale

## Variables de base

### Informations station
- **`{station_name}`** - Nom de la balise météo
  - Exemple : "Annecy"

### Mesures de vent
- **`{wind_avg_kmh}`** - Vent moyen en kilomètres par heure (arrondi à l'entier)
  - Exemple : "12"

- **`{wind_max_kmh}`** - Rafales (vent maximum) en kilomètres par heure (arrondi à l'entier)
  - Exemple : "18"

- **`{wind_min_kmh}`** - Vent minimum en kilomètres par heure (arrondi à l'entier)
  - Exemple : "8"
  - Note : Peut ne pas être disponible selon le provider

### Direction du vent
- **`{wind_direction_name}`** - Direction du vent en français complet
  - Valeurs possibles : Nord, Nord-Nord-Est, Nord-Est, Est-Nord-Est, Est, Est-Sud-Est, Sud-Est, Sud-Sud-Est, Sud, Sud-Sud-Ouest, Sud-Ouest, Ouest-Sud-Ouest, Ouest, Ouest-Nord-Ouest, Nord-Ouest, Nord-Nord-Ouest
  - Exemple : "Nord-Est"

- **`{wind_direction_deg}`** - Direction du vent en degrés (0-359, arrondi à l'entier)
  - Exemple : "45"

### Ancienneté de la mesure
- **`{measurement_age_minutes}`** - Temps écoulé depuis la mesure en minutes (arrondi à l'entier)
  - Exemple : "15"

## Exemples de templates

### Template par défaut (recommandé)
```
Balise de {station_name}, {wind_direction_name}, {wind_avg_kmh} kilomètres par heure, {wind_max_kmh} maximum, il y a {measurement_age_minutes} minutes.
```

### Template court
```
{station_name}, vent {wind_direction_name} {wind_avg_kmh}, rafales {wind_max_kmh}.
```

### Template détaillé avec minimum
```
Balise {station_name}, vent {wind_direction_name}, moyenne {wind_avg_kmh}, rafales {wind_max_kmh}, minimum {wind_min_kmh} kilomètres par heure.
```

### Template avec degrés
```
Station {station_name}, direction {wind_direction_deg} degrés, vent moyen {wind_avg_kmh} kilomètres par heure.
```

## Notes importantes

1. **Arrondi automatique** : Toutes les valeurs numériques sont arrondies à l'entier le plus proche pour une meilleure lisibilité vocale.

2. **Direction du vent** : Le système calcule automatiquement le nom en français (Nord, Nord-Est, etc.) à partir des degrés fournis par le provider.

3. **Compatibilité providers** :
   - `wind_min_kmh` peut ne pas être disponible avec tous les providers
   - `wind_direction_deg` est toujours converti en nom français

4. **Langue** : Actuellement, seul le français est supporté.

5. **Fail-safe** : Si une variable n'est pas disponible, l'annonce ne sera **pas** diffusée (principe fail-closed pour éviter les annonces incomplètes).
