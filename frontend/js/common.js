// Fonctions communes à toutes les pages
console.log('[COMMON.JS] Fichier chargé à', new Date().toISOString());

// Vérifier l'authentification
function checkAuth() {
    const token = localStorage.getItem('token');
    const path = window.location.pathname;

    console.log('[AUTH] checkAuth() appelé - token:', token ? 'présent' : 'absent', '- path:', path);

    if (!token) {
        console.log('[AUTH] Pas de token trouvé');
        // Ne rediriger que si on n'est pas déjà sur la page de login
        const isLoginPage = path === '/' || path === '/index.html' || path === '/static/index.html';
        if (!isLoginPage) {
            console.log('[AUTH] ❌ REDIRECTION vers login depuis:', path);
            window.location.href = '/';
        } else {
            console.log('[AUTH] Page de login, pas de redirection');
        }
        return null;
    }
    console.log('[AUTH] ✓ Token présent, OK');
    return token;
}

// Fonction pour gérer les erreurs d'authentification (token expiré)
function handleAuthError(error) {
    console.error('❌ [AUTH] handleAuthError appelé!');
    console.error('❌ [AUTH] Raison:', error);
    console.error('❌ [AUTH] Stack trace:', new Error().stack);

    // Afficher une alerte avant de déconnecter
    alert('⏱️ Session expirée ou serveur redémarré.\n\nVous allez être redirigé vers la page de connexion.');

    localStorage.removeItem('token');
    localStorage.setItem('session_expired', 'true');
    window.location.href = '/';
}

// Fonction fetch avec gestion automatique des erreurs 401
async function authenticatedFetch(url, options = {}) {
    const token = localStorage.getItem('token');

    if (!token) {
        // Pas de token, rediriger vers login
        window.location.href = '/';
        throw new Error('Non authentifié');
    }

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
        // Si c'est une erreur 401, on a déjà géré
        if (error.message === 'Session expirée') {
            throw error;
        }
        // Autres erreurs (réseau, etc.) : ne pas déconnecter l'utilisateur
        console.error('Erreur réseau:', error);
        throw error;
    }
}

// Déconnexion
console.log('[COMMON.JS] Attente du DOMContentLoaded...');

document.addEventListener('DOMContentLoaded', () => {
    console.log('[COMMON.JS] DOMContentLoaded déclenché');

    const logoutBtn = document.getElementById('logoutBtn');
    if (logoutBtn) {
        console.log('[AUTH] Bouton logout trouvé');
        logoutBtn.addEventListener('click', () => {
            console.log('[AUTH] 🚪 Déconnexion manuelle');
            localStorage.removeItem('token');
            localStorage.removeItem('session_expired');
            window.location.href = '/';
        });
    } else {
        console.log('[AUTH] Bouton logout non trouvé (probablement page login)');
    }

    // Vérifier l'auth au chargement seulement si on n'est pas sur la page de login
    const path = window.location.pathname;
    const isLoginPage = path === '/' || path === '/index.html' || path === '/static/index.html';

    console.log('[AUTH] Path:', path, '- isLoginPage:', isLoginPage);

    if (!isLoginPage) {
        console.log('[AUTH] 🔍 Lancement vérification auth...');
        checkAuth();
    } else {
        console.log('[AUTH] Page de login, pas de vérification');
    }
});

