# Sidebar factorisée

## Fichier créé

- `frontend/js/sidebar.js` - Composant réutilisable pour la sidebar

## Comment utiliser (pour futures pages)

### Option 1 : Sidebar générée dynamiquement (recommandé)

```html
<body>
    <div class="app-container">
        <!-- La sidebar sera insérée ici automatiquement -->
        
        <main class="main-content">
            <!-- Votre contenu -->
        </main>
    </div>
    
    <script src="/static/js/sidebar.js"></script>
    <script>
        // Indiquer la page courante pour l'item actif
        initSidebar('dashboard'); // ou 'channels', 'providers', etc.
    </script>
    <script src="/static/js/votre-page.js"></script>
</body>
```

### Option 2 : Sidebar statique (actuel)

Les pages actuelles utilisent encore la sidebar statique dans le HTML.
Pour les migrer vers la sidebar dynamique :

1. Supprimer le bloc `<aside class="sidebar">...</aside>`
2. Ajouter `<script src="/static/js/sidebar.js"></script>`
3. Appeler `initSidebar('nom_page')` avant votre script

## Avantages de la sidebar dynamique

✅ Un seul endroit pour modifier la navigation
✅ Ajout facile de nouveaux items
✅ Cohérence garantie entre toutes les pages
✅ Réduction du code dupliqué

## Configuration

Modifier `NAV_ITEMS` dans `sidebar.js` pour ajouter/modifier des items :

```javascript
const NAV_ITEMS = [
    { href: '/static/dashboard.html', icon: '📊', label: 'Tableau de bord', page: 'dashboard' },
    // ... ajouter vos items ici
];
```

## Migration future

Pour migrer toutes les pages vers la sidebar dynamique, il suffit de :
1. Créer un script de migration
2. Remplacer les `<aside>` dans tous les HTML
3. Tester chaque page

Pour l'instant, les deux approches coexistent (statique dans HTML pour compatibilité).
