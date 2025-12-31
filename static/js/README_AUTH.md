# Gestion de l'authentification automatique

## Fonction `authenticatedFetch()`

Une nouvelle fonction globale `authenticatedFetch()` est disponible dans `common.js` pour gérer automatiquement :
- L'ajout du token Bearer dans les headers
- La détection des erreurs 401 (token expiré)
- La redirection automatique vers la page de login avec message

## Migration du code existant

### ❌ Ancien code (à remplacer)
```javascript
const response = await fetch('/api/channels/', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
if (!response.ok) throw new Error('Erreur');
```

### ✅ Nouveau code (recommandé)
```javascript
const response = await authenticatedFetch('/api/channels/');
if (!response.ok) throw new Error('Erreur');
```

## Exemple complet

```javascript
async function loadChannels() {
    try {
        const response = await authenticatedFetch('/api/channels/');
        
        if (!response.ok) {
            throw new Error('Erreur chargement canaux');
        }
        
        const channels = await response.json();
        displayChannels(channels);
    } catch (error) {
        // Si erreur 401, l'utilisateur sera déjà redirigé
        // Gérer ici les autres erreurs (500, réseau, etc.)
        console.error('Erreur:', error);
    }
}
```

## Avec options (POST, PUT, etc.)

```javascript
const response = await authenticatedFetch('/api/channels/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(data)
});
```

## Comportement

1. **Token valide** → Requête normale
2. **Token expiré (401)** → 
   - Suppression du token
   - Enregistrement d'un flag "session_expired"
   - Redirection vers `/`
   - Affichage du message "Votre session a expiré"

## Fichiers à migrer

- [ ] `history.js` - toutes les requêtes fetch
- [ ] `channels.js` - toutes les requêtes fetch
- [ ] `dashboard.js` - toutes les requêtes fetch
- [ ] `providers.js` - toutes les requêtes fetch

## Note

Le fichier `login.js` gère déjà l'affichage du message "Session expirée" au chargement de la page.
