// Gestion de la page providers
const token = localStorage.getItem('token');

// Charger le statut des providers
async function loadProviders() {
    try {
        const response = await fetch('/api/providers/', {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (response.ok) {
            const providers = await response.json();
            
            // Afficher le statut FFVL
            const ffvl = providers.find(p => p.provider_id === 'ffvl');
            const statusDiv = document.getElementById('ffvl-status');
            
            if (ffvl && ffvl.is_configured) {
                statusDiv.innerHTML = '<div class="success-message">✓ Clé API configurée</div>';
            } else {
                statusDiv.innerHTML = '<div class="text-muted">Aucune clé API configurée</div>';
            }
        }
    } catch (err) {
        console.error('Erreur lors du chargement des providers:', err);
    }
}

// Sauvegarder la clé FFVL
document.getElementById('ffvlForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const apiKey = document.getElementById('ffvl_api_key').value.trim();
    const statusDiv = document.getElementById('ffvl-status');
    
    if (!apiKey) {
        statusDiv.innerHTML = '<div class="error-message">Veuillez saisir une clé API</div>';
        return;
    }
    
    try {
        const response = await fetch('/api/providers/credentials', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                provider_id: 'ffvl',
                api_key: apiKey
            })
        });
        
        if (response.ok) {
            statusDiv.innerHTML = '<div class="success-message">✓ Clé API enregistrée avec succès</div>';
            document.getElementById('ffvl_api_key').value = '';
            setTimeout(() => loadProviders(), 1000);
        } else {
            const error = await response.json();
            statusDiv.innerHTML = `<div class="error-message">Erreur: ${error.detail}</div>`;
        }
    } catch (err) {
        statusDiv.innerHTML = '<div class="error-message">Erreur de connexion au serveur</div>';
    }
});

// Charger au démarrage
loadProviders();
