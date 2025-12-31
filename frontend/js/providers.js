// Gestion de la page providers

// Charger le statut des providers
async function loadProviders() {
    try {
        const response = await authenticatedFetch('/api/providers/');

        if (response && response.ok) {
            const providers = await response.json();

            // Afficher le statut FFVL
            const ffvl = providers.find(p => p.provider_id === 'ffvl');
            const container = document.getElementById('ffvl-container');

            if (ffvl && ffvl.is_configured) {
                // Clé configurée : afficher statut + bouton supprimer
                container.innerHTML = `
                    <div class="success-message" style="margin-bottom: 1rem;">
                        ✓ Clé API configurée et active
                    </div>
                    <button onclick="removeFFVLKey()" class="btn btn-danger">
                        Retirer la clé API
                    </button>
                `;
            } else {
                // Pas de clé : afficher le formulaire
                container.innerHTML = `
                    <form id="ffvlForm">
                        <div class="form-group">
                            <label for="ffvl_api_key">Clé API FFVL</label>
                            <input type="password" id="ffvl_api_key" class="form-control" placeholder="Saisissez votre clé API">
                            <small class="text-muted">Vous pouvez obtenir une clé API sur balisemeteo.com</small>
                        </div>
                        <div id="ffvl-status" style="margin-bottom: 1rem;"></div>
                        <button type="submit" class="btn btn-primary">Enregistrer</button>
                    </form>
                `;
                
                // Réattacher l'event listener du formulaire
                document.getElementById('ffvlForm').addEventListener('submit', saveFFVLKey);
            }
        }
    } catch (err) {
        console.error('Erreur lors du chargement des providers:', err);
    }
}

// Sauvegarder la clé FFVL
async function saveFFVLKey(e) {
    e.preventDefault();

    const apiKey = document.getElementById('ffvl_api_key').value.trim();
    const statusDiv = document.getElementById('ffvl-status');

    if (!apiKey) {
        statusDiv.innerHTML = '<div class="error-message">Veuillez saisir une clé API</div>';
        return;
    }

    try {
        const response = await authenticatedFetch('/api/providers/credentials', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                provider_id: 'ffvl',
                api_key: apiKey
            })
        });

        if (response && response.ok) {
            statusDiv.innerHTML = '<div class="success-message">✓ Clé API enregistrée avec succès</div>';
            setTimeout(() => loadProviders(), 1000);
        } else {
            const error = response ? await response.json() : {};
            statusDiv.innerHTML = `<div class="error-message">Erreur: ${error.detail || 'Erreur inconnue'}</div>`;
        }
    } catch (err) {
        statusDiv.innerHTML = '<div class="error-message">Erreur de connexion au serveur</div>';
    }
}

// Retirer la clé FFVL
async function removeFFVLKey() {
    if (!confirm('Êtes-vous sûr de vouloir retirer la clé API FFVL ?')) {
        return;
    }

    try {
        const response = await authenticatedFetch('/api/providers/credentials/ffvl', {
            method: 'DELETE'
        });

        if (response && response.ok) {
            loadProviders(); // Recharger pour afficher le formulaire
        } else {
            const error = response ? await response.json() : {};
            alert(`Erreur: ${error.detail || 'Impossible de retirer la clé'}`);
        }
    } catch (err) {
        console.error('Erreur:', err);
        alert('Erreur de connexion au serveur');
    }
}

// Charger au démarrage
loadProviders();
