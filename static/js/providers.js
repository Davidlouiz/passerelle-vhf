// Gestion de la page sources

// Charger le statut des sources
async function loadProviders() {
    try {
        const response = await authenticatedFetch('/api/providers/');

        if (response && response.ok) {
            const sources = await response.json();

            // Afficher le statut FFVL
            const ffvl = sources.find(p => p.provider_id === 'ffvl');
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
                            <small class="text-muted">Pour obtenir une clé API, contactez la Fédération Française de Vol Libre (FFVL)</small>
                        </div>
                        
                        <div style="margin-top: 1rem;">
                            <button type="button" class="btn btn-sm btn-info" onclick="toggleEmailTemplate()" style="margin-bottom: 0.5rem;">
                                📧 Modèle de demande
                            </button>
                            <div id="emailTemplate" style="display: none; background-color: #e8f4f8; border-left: 4px solid #0066cc; padding: 1rem; font-size: 0.9rem;">
                                <div style="margin-top: 0.5rem;">
                                    <strong>Destinataire :</strong> Gilles MISSLIN (FFVL)
                                </div>
                                <div style="margin-top: 0.5rem;">
                                    <strong>Objet :</strong> Demande de clé API - Installation passerelle VHF météo automatique
                                </div>
                                <div style="margin-top: 0.5rem;">
                                    <strong>Message :</strong><br>
                                    Bonjour Monsieur MISSLIN,<br><br>
                                    J'installe une passerelle VHF permettant de diffuser automatiquement et vocalement les informations météorologiques issues de vos balises.<br><br>
                                    Le système interroge périodiquement les données météo (vent moyen, rafales, direction) et les annonce sur le canal VHF dédié, permettant ainsi aux pilotes de recevoir des bulletins à jour.<br><br>
                                    Pour accéder aux données de vos stations via balisemeteo.com, j'ai besoin d'une clé API.<br><br>
                                    Informations sur le projet :<br>
                                    - Projet : <a href="https://github.com/Davidlouiz/passerelle-vhf" target="_blank" style="color: #0066cc; text-decoration: underline;">https://github.com/Davidlouiz/passerelle-vhf</a><br>
                                    - Site/balise concerné : [à préciser]<br>
                                    - Localisation : [à préciser]<br>
                                    - Utilisation : diffusion VHF automatique locale<br><br>
                                    Pourriez-vous me communiquer une clé d'accès API pour cette installation ?<br><br>
                                    Je reste à votre disposition pour tout complément d'information.<br><br>
                                    Cordialement
                                </div>
                            </div>
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
        console.error('Erreur lors du chargement des sources:', err);
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

// Toggle affichage du modèle d'email
window.toggleEmailTemplate = function() {
    const template = document.getElementById('emailTemplate');
    if (template) {
        template.style.display = template.style.display === 'none' ? 'block' : 'none';
    }
};

// Charger au démarrage
loadProviders();
