// Gestion des canaux
const token = localStorage.getItem('token');
let currentChannelId = null;

// Charger la liste des canaux
async function loadChannels() {
    try {
        const response = await fetch('/api/channels/', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const channels = await response.json();
            displayChannels(channels);
        }
    } catch (err) {
        console.error('Erreur lors du chargement des canaux:', err);
    }
}

// Afficher les canaux
function displayChannels(channels) {
    const container = document.getElementById('channelsList');
    
    if (channels.length === 0) {
        container.innerHTML = `
            <p class="text-muted">Aucune balise configurée pour le moment.</p>
            <p class="text-muted">Cliquez sur "+ Nouvelle balise" pour commencer.</p>
        `;
        return;
    }
    
    const html = `
        <table class="table">
            <thead>
                <tr>
                    <th>Nom</th>
                    <th>Provider</th>
                    <th>Statut</th>
                    <th>Actions</th>
                </tr>
            </thead>
            <tbody>
                ${channels.map(ch => `
                    <tr>
                        <td><strong>${ch.name}</strong></td>
                        <td>${ch.provider_id.toUpperCase()}</td>
                        <td>
                            <span class="badge ${ch.is_enabled ? 'badge-success' : 'badge-danger'}">
                                ${ch.is_enabled ? 'Activé' : 'Désactivé'}
                            </span>
                        </td>
                        <td>
                            <button onclick="toggleChannel(${ch.id})" class="btn btn-sm ${ch.is_enabled ? 'btn-secondary' : 'btn-success'}">
                                ${ch.is_enabled ? 'Désactiver' : 'Activer'}
                            </button>
                            <button onclick="editChannel(${ch.id})" class="btn btn-sm btn-secondary">Éditer</button>
                            <button onclick="deleteChannel(${ch.id}, '${ch.name}')" class="btn btn-sm btn-danger">Supprimer</button>
                        </td>
                    </tr>
                `).join('')}
            </tbody>
        </table>
    `;
    
    container.innerHTML = html;
}

// Ouvrir le modal de création
document.getElementById('newChannelBtn').addEventListener('click', () => {
    currentChannelId = null;
    document.getElementById('modalTitle').textContent = 'Nouvelle balise';
    document.getElementById('channelForm').reset();
    document.getElementById('channelModal').style.display = 'flex';
});

// Fermer le modal
document.getElementById('closeModal').addEventListener('click', closeModal);
document.getElementById('cancelBtn').addEventListener('click', closeModal);

function closeModal() {
    document.getElementById('channelModal').style.display = 'none';
    document.getElementById('form-error').style.display = 'none';
}

// Soumettre le formulaire
document.getElementById('channelForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const name = document.getElementById('channel_name').value.trim();
    const stationUrl = document.getElementById('station_url').value.trim();
    const template = document.getElementById('template').value.trim();
    const offsetsStr = document.getElementById('offsets').value.trim();
    
    // Parser les offsets
    const offsets = offsetsStr.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
    
    const data = {
        name,
        station_visual_url: stationUrl,
        template_text: template,
        offsets_seconds_json: JSON.stringify(offsets)
    };
    
    const errorDiv = document.getElementById('form-error');
    errorDiv.style.display = 'none';
    
    try {
        const url = currentChannelId ? `/api/channels/${currentChannelId}` : '/api/channels/';
        const method = currentChannelId ? 'PUT' : 'POST';
        
        const response = await fetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        
        if (response.ok) {
            closeModal();
            loadChannels();
        } else {
            let errorMessage = 'Erreur lors de la sauvegarde';
            try {
                const error = await response.json();
                errorMessage = error.detail || errorMessage;
            } catch (e) {
                errorMessage = `Erreur HTTP ${response.status}`;
            }
            errorDiv.textContent = errorMessage;
            errorDiv.style.display = 'block';
        }
    } catch (err) {
        console.error('Erreur complète:', err);
        errorDiv.textContent = 'Erreur de connexion au serveur: ' + err.message;
        errorDiv.style.display = 'block';
    }
});

// Activer/désactiver un canal
async function toggleChannel(channelId) {
    try {
        const response = await fetch(`/api/channels/${channelId}/toggle`, {
            method: 'POST',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            loadChannels();
        }
    } catch (err) {
        console.error('Erreur:', err);
    }
}

// Éditer un canal
async function editChannel(channelId) {
    try {
        const response = await fetch(`/api/channels/${channelId}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            const channel = await response.json();
            currentChannelId = channelId;
            
            document.getElementById('modalTitle').textContent = 'Éditer la balise';
            document.getElementById('channel_name').value = channel.name;
            document.getElementById('station_url').value = channel.station_visual_url_cache;

            document.getElementById('template').value = channel.template_text;
            
            const offsets = JSON.parse(channel.offsets_seconds_json);
            document.getElementById('offsets').value = offsets.join(', ');
            
            document.getElementById('channelModal').style.display = 'flex';
        }
    } catch (err) {
        console.error('Erreur:', err);
    }
}

// Supprimer une balise
async function deleteChannel(channelId, channelName) {
    if (!confirm(`Voulez-vous vraiment supprimer la balise "${channelName}" ?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/channels/${channelId}`, {
            method: 'DELETE',
            headers: { 'Authorization': `Bearer ${token}` }
        });
        
        if (response.ok) {
            loadChannels();
        }
    } catch (err) {
        console.error('Erreur:', err);
    }
}

// Charger au démarrage
loadChannels();
