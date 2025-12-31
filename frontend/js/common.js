// Fonctions communes à toutes les pages

// Vérifier l'authentification
function checkAuth() {
    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/';
        return null;
    }
    return token;
}

// Fonction pour gérer les erreurs d'authentification (token expiré)
function handleAuthError(error) {
    console.error('Erreur d\'authentification:', error);
    localStorage.removeItem('token');
    localStorage.setItem('session_expired', 'true');
    window.location.href = '/';
}

// Fonction fetch avec gestion automatique des erreurs 401
async function authenticatedFetch(url, options = {}) {
    const token = localStorage.getItem('token');

    // Ajouter le header Authorization
    const headers = options.headers || {};
    headers['Authorization'] = `Bearer ${token}`;
    options.headers = headers;

    try {
        const response = await fetch(url, options);

        // Si 401, déconnecter automatiquement
        if (response.status === 401) {
            handleAuthError('Token expiré ou invalide');
            throw new Error('Session expirée');
        }

        return response;
    } catch (error) {
        // Si erreur réseau ou autre
        throw error;
    }
}

// Déconnexion
const logoutBtn = document.getElementById('logoutBtn');
if (logoutBtn) {
    logoutBtn.addEventListener('click', () => {
        localStorage.removeItem('token');
        localStorage.removeItem('session_expired');
        window.location.href = '/';
    });
}

// Vérifier l'auth au chargement
checkAuth();
