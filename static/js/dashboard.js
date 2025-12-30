// Vérifier l'authentification
function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/';
        return null;
    }
    return token;
}

// Utilitaire pour faire des requêtes API
async function apiRequest(url, options = {}) {
    const token = checkAuth();
    if (!token) return;

    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers
    };

    const response = await fetch(url, {
        ...options,
        headers
    });

    if (response.status === 401) {
        // Token expiré
        localStorage.removeItem('token');
        window.location.href = '/';
        return;
    }

    return response;
}

// Charger le statut système
async function loadSystemStatus() {
    try {
        const response = await apiRequest('/api/status');
        if (!response) return;

        if (response.ok) {
            const data = await response.json();
            updateDashboard(data);
        }
    } catch (err) {
        console.error('Erreur lors du chargement du statut:', err);
    }
}

// Mettre à jour le dashboard
function updateDashboard(data) {
    // TODO: mettre à jour les éléments du dashboard
    // Pour l'instant, juste des placeholders

    document.getElementById('master-enabled').textContent =
        data.master_enabled ? '✓ Activé' : '✗ Désactivé';

    const statusBadge = document.getElementById('system-status');
    if (data.master_enabled) {
        statusBadge.textContent = 'Système actif';
        statusBadge.className = 'badge badge-success';
    } else {
        statusBadge.textContent = 'Système désactivé';
        statusBadge.className = 'badge badge-danger';
    }
}

// Déconnexion
document.getElementById('logoutBtn').addEventListener('click', () => {
    localStorage.removeItem('token');
    window.location.href = '/';
});

// Charger les données au démarrage
checkAuth();
loadSystemStatus();

// Rafraîchir toutes les 10 secondes
setInterval(loadSystemStatus, 10000);
