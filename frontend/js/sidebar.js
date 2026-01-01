/**
 * Génération dynamique de la sidebar
 * Permet de factoriser le code HTML de la navigation
 */

// Configuration des items de navigation
const NAV_ITEMS = [
    { href: '/static/dashboard.html', icon: '📊', label: 'Tableau de bord', page: 'dashboard' },
    { href: '/static/channels.html', icon: '📡', label: 'Canaux', page: 'channels' },
    { href: '/static/settings.html', icon: '⚙️', label: 'Paramètres', page: 'settings' },
    { href: '/static/admin.html', icon: '👤', label: 'Administration', page: 'admin' }
];

/**
 * Génère le HTML de la sidebar
 * @param {string} currentPage - Nom de la page courante pour activer l'item correspondant
 */
function generateSidebar(currentPage) {
    const navItems = NAV_ITEMS.map(item => {
        const isActive = item.page === currentPage ? 'active' : '';
        return `
            <a href="${item.href}" class="nav-item ${isActive}">
                <span class="icon">${item.icon}</span>
                ${item.label}
            </a>
        `;
    }).join('');

    return `
        <aside class="sidebar">
            <div class="sidebar-header">
                <h2>📻 Passerelle VHF</h2>
            </div>
            <nav class="sidebar-nav">
                ${navItems}
            </nav>
            <div class="sidebar-footer">
                <button id="logoutBtn" class="btn btn-secondary btn-block">
                    Déconnexion
                </button>
            </div>
        </aside>
    `;
}

/**
 * Insère la sidebar dans la page
 * À appeler au chargement de chaque page
 */
function initSidebar(currentPage) {
    console.log('[SIDEBAR] Initialisation pour page:', currentPage);

    // Trouver le conteneur de l'app
    const appContainer = document.querySelector('.app-container');

    if (appContainer) {
        // Insérer la sidebar au début
        appContainer.insertAdjacentHTML('afterbegin', generateSidebar(currentPage));
        console.log('[SIDEBAR] Sidebar insérée');

        // NE PAS gérer le bouton de déconnexion ici
        // C'est géré par common.js pour éviter les conflits
    } else {
        console.error('[SIDEBAR] Conteneur .app-container non trouvé !');
    }
}
