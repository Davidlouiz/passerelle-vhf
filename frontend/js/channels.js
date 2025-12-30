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
                    <th>Test</th>
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
                            <button onclick="testMeasurement(${ch.id}, '${ch.provider_id}', '${ch.station_id}')" class="btn btn-sm btn-info" title="Tester récupération mesure">
                                🌡️
                            </button>
                            <button onclick="previewAnnouncement(${ch.id})" class="btn btn-sm btn-primary" title="Écouter avec vraies valeurs">
                                🔊
                            </button>
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

// Tester la récupération de mesure
async function testMeasurement(channelId, providerId, stationId) {
    const btn = event.target;
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '⏳ Test...';

    try {
        const response = await fetch('/api/providers/test-measurement', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                provider_id: providerId,
                station_id: stationId
            })
        });

        if (response.ok) {
            const data = await response.json();
            const date = new Date(data.measurement_at);
            const age = Math.round((Date.now() - date.getTime()) / 60000); // minutes

            alert(
                `✅ Mesure récupérée avec succès!\n\n` +
                `📅 Date: ${date.toLocaleString('fr-FR')}\n` +
                `⏰ Âge: ${age} minute(s)\n` +
                `💨 Vent moyen: ${data.wind_avg_kmh.toFixed(1)} km/h\n` +
                `💨 Rafales: ${data.wind_max_kmh.toFixed(1)} km/h` +
                (data.wind_min_kmh ? `\n💨 Vent mini: ${data.wind_min_kmh.toFixed(1)} km/h` : '')
            );
        } else {
            const error = await response.json();
            alert(`❌ Erreur: ${error.detail || 'Erreur inconnue'}`);
        }
    } catch (err) {
        console.error('Erreur:', err);
        alert(`❌ Erreur lors du test: ${err.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// Prévisualiser une annonce avec vraies valeurs
async function previewAnnouncement(channelId) {
    const btn = event.target;
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '⏳';

    try {
        const response = await fetch(`/api/channels/${channelId}/preview`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json'
            }
        });

        if (response.ok) {
            const data = await response.json();
            
            // Afficher le modal de prévisualisation
            showPreviewModal(data);
            
        } else {
            const error = await response.json();
            alert(`❌ Erreur: ${error.detail || 'Erreur inconnue'}`);
        }
    } catch (err) {
        console.error('Erreur:', err);
        alert(`❌ Erreur lors de la prévisualisation: ${err.message}`);
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

// Afficher le modal de prévisualisation
function showPreviewModal(data) {
    // Créer le modal s'il n'existe pas
    let modal = document.getElementById('previewModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'previewModal';
        modal.className = 'modal';
        modal.innerHTML = `
            <div class="modal-content" style="max-width: 600px;">
                <div class="modal-header">
                    <h2>🔊 Prévisualisation annonce</h2>
                    <span class="close" onclick="closePreviewModal()">&times;</span>
                </div>
                <div class="modal-body">
                    <div class="preview-section">
                        <h3>📊 Mesures actuelles</h3>
                        <div id="previewMeasurement" class="info-box"></div>
                    </div>
                    
                    <div class="preview-section">
                        <h3>📝 Texte rendu</h3>
                        <div id="previewText" class="info-box" style="font-family: monospace;"></div>
                    </div>
                    
                    <div class="preview-section">
                        <h3>🎧 Audio</h3>
                        <audio id="previewAudio" controls style="width: 100%;"></audio>
                        <p class="text-muted" style="margin-top: 10px; font-size: 12px;" id="cacheInfo"></p>
                    </div>
                </div>
                <div class="modal-footer">
                    <button onclick="closePreviewModal()" class="btn btn-secondary">Fermer</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }
    
    // Remplir les données
    const measurement = data.measurement;
    const date = new Date(measurement.measurement_at);
    
    document.getElementById('previewMeasurement').innerHTML = `
        <p><strong>📅 Date:</strong> ${date.toLocaleString('fr-FR')}</p>
        <p><strong>⏰ Âge:</strong> ${measurement.age_minutes} minute(s)</p>
        <p><strong>💨 Vent moyen:</strong> ${measurement.wind_avg_kmh.toFixed(1)} km/h</p>
        <p><strong>💨 Rafales:</strong> ${measurement.wind_max_kmh.toFixed(1)} km/h</p>
    `;
    
    document.getElementById('previewText').textContent = data.rendered_text;
    
    const audio = document.getElementById('previewAudio');
    audio.src = data.audio_url;
    audio.load();
    
    const cacheInfo = data.was_cached ? 
        '✅ Audio récupéré du cache' : 
        '🆕 Audio nouvellement généré';
    document.getElementById('cacheInfo').textContent = cacheInfo;
    
    // Afficher le modal
    modal.style.display = 'flex';
}

// Fermer le modal de prévisualisation
function closePreviewModal() {
    const modal = document.getElementById('previewModal');
    if (modal) {
        const audio = document.getElementById('previewAudio');
        audio.pause();
        audio.currentTime = 0;
        modal.style.display = 'none';
    }
}


// Charger au démarrage
loadChannels();
