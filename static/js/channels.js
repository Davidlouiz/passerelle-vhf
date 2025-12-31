// Gestion des canaux
let currentChannelId = null;

// Charger la liste des canaux
async function loadChannels() {
    try {
        const response = await authenticatedFetch('/api/channels/');

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
            <p class="text-muted">Aucun canal configuré pour le moment.</p>
            <p class="text-muted">Cliquez sur "+ Nouveau canal" pour commencer.</p>
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
                            <button onclick="testMeasurement(${ch.id}, '${ch.provider_id}', '${ch.station_id}')" class="btn btn-sm btn-outline-secondary" title="Tester récupération mesure">
                                API
                            </button>
                            <button onclick="previewAnnouncement(${ch.id})" class="btn btn-sm btn-outline-secondary" title="Écouter avec vraies valeurs">
                                TTS
                            </button>
                        </td>
                        <td>
                            <button onclick="toggleChannel(${ch.id})" class="btn btn-sm btn-secondary">
                                ${ch.is_enabled ? 'Désactiver' : 'Activer'}
                            </button>
                            <button onclick="editChannel(${ch.id})" class="btn btn-sm btn-secondary">Modifier</button>
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
    document.getElementById('modalTitle').textContent = 'Nouveau canal';
    document.getElementById('channelForm').reset();
    document.getElementById('channelModal').style.display = 'flex';

    // Initialiser le menu des variables après ouverture du modal
    setTimeout(initVariableMenu, 100);
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
    const voiceId = document.getElementById('voice_id').value;
    const offsetsStr = document.getElementById('offsets').value.trim();

    // Parser les offsets
    const offsets = offsetsStr.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));

    const data = {
        name,
        station_visual_url: stationUrl,
        template_text: template,
        voice_id: voiceId,
        offsets_seconds_json: JSON.stringify(offsets)
    };

    const errorDiv = document.getElementById('form-error');
    errorDiv.style.display = 'none';

    try {
        const url = currentChannelId ? `/api/channels/${currentChannelId}` : '/api/channels/';
        const method = currentChannelId ? 'PUT' : 'POST';

        const response = await authenticatedFetch(url, {
            method,
            headers: {
                'Content-Type': 'application/json'
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
        const response = await authenticatedFetch(`/api/channels/${channelId}/toggle`, {
            method: 'POST'
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
        const response = await authenticatedFetch(`/api/channels/${channelId}`);

        if (response.ok) {
            const channel = await response.json();
            currentChannelId = channelId;

            document.getElementById('modalTitle').textContent = 'Modifier le canal';
            document.getElementById('channel_name').value = channel.name;
            document.getElementById('station_url').value = channel.station_visual_url_cache;
            document.getElementById('template').value = channel.template_text;
            document.getElementById('voice_id').value = channel.voice_id || 'fr_FR-siwis-medium';

            const offsets = JSON.parse(channel.offsets_seconds_json);
            document.getElementById('offsets').value = offsets.join(', ');

            document.getElementById('channelModal').style.display = 'flex';
        }
    } catch (err) {
        console.error('Erreur:', err);
    }
}

// Supprimer un canal
async function deleteChannel(channelId, channelName) {
    if (!confirm(`Voulez-vous vraiment supprimer le canal "${channelName}" ?`)) {
        return;
    }

    try {
        const response = await authenticatedFetch(`/api/channels/${channelId}`, {
            method: 'DELETE'
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
        const response = await authenticatedFetch('/api/providers/test-measurement', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                provider_id: providerId,
                station_id: stationId
            })
        });

        if (response && response.ok) {
            const data = await response.json();
            const date = new Date(data.measurement_at);
            const age = Math.round((Date.now() - date.getTime()) / 60000); // minutes

            showNotification(
                'Mesure récupérée avec succès',
                `<p><strong>📅 Date:</strong> ${date.toLocaleString('fr-FR')}</p>` +
                `<p><strong>⏰ Âge:</strong> ${age} minute(s)</p>` +
                `<p><strong>💨 Vent moyen:</strong> ${data.wind_avg_kmh.toFixed(1)} km/h</p>` +
                `<p><strong>💨 Rafales:</strong> ${data.wind_max_kmh.toFixed(1)} km/h</p>` +
                (data.wind_min_kmh ? `<p><strong>💨 Vent mini:</strong> ${data.wind_min_kmh.toFixed(1)} km/h</p>` : ''),
                'success'
            );
        } else {
            const error = response ? await response.json() : {};
            showNotification('Erreur', error.detail || 'Erreur inconnue', 'error');
        }
    } catch (err) {
        console.error('Erreur:', err);
        showNotification('Erreur', `Erreur lors du test: ${err.message}`, 'error');
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
        const response = await authenticatedFetch(`/api/channels/${channelId}/preview`, {
            method: 'POST'
        });

        if (response && response.ok) {
            const data = await response.json();

            // Afficher le modal de prévisualisation
            showPreviewModal(data);

        } else {
            const error = response ? await response.json() : {};
            showNotification('Erreur', error.detail || 'Erreur inconnue', 'error');
        }
    } catch (err) {
        console.error('Erreur:', err);
        showNotification('Erreur', `Erreur lors de la prévisualisation: ${err.message}`, 'error');
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
                    <button class="btn-close" onclick="closePreviewModal()">&times;</button>
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

    // Lancer la lecture automatiquement
    audio.play().catch(err => console.log('Autoplay bloqué:', err));

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


// Notification élégante
function showNotification(title, message, type = 'info') {
    // Créer le conteneur de notifications s'il n'existe pas
    let container = document.getElementById('notificationContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'notificationContainer';
        container.className = 'notification-container';
        document.body.appendChild(container);
    }

    // Créer la notification
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-header">
            <strong>${type === 'success' ? '✅' : type === 'error' ? '❌' : 'ℹ️'} ${title}</strong>
            <button onclick="this.parentElement.parentElement.remove()" class="notification-close">&times;</button>
        </div>
        <div class="notification-body">${message}</div>
    `;

    container.appendChild(notification);

    // Auto-supprimer après 5 secondes
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-out';
        setTimeout(() => notification.remove(), 300);
    }, 5000);
}

// Menu des variables - simplifié et fonctionnel
function initVariableMenu() {
    const insertBtn = document.getElementById('insertVarBtn');
    const menu = document.getElementById('variableMenu');
    const textarea = document.getElementById('template');

    if (!insertBtn || !menu || !textarea) {
        console.log('Éléments du menu variable non trouvés');
        return;
    }

    console.log('Initialisation du menu des variables');

    // Reset le menu
    menu.style.display = 'none';

    // Supprimer les anciens listeners en clonant les éléments
    const newInsertBtn = insertBtn.cloneNode(true);
    insertBtn.parentNode.replaceChild(newInsertBtn, insertBtn);

    // Toggle menu au clic sur le bouton
    newInsertBtn.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        const isVisible = menu.style.display === 'block';
        menu.style.display = isVisible ? 'none' : 'block';
        console.log('Menu toggled:', menu.style.display);
    });

    // Insertion au clic sur un item du menu
    menu.querySelectorAll('.variable-item').forEach(item => {
        // Cloner pour retirer les anciens listeners
        const newItem = item.cloneNode(true);
        item.parentNode.replaceChild(newItem, item);

        newItem.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();

            const varName = newItem.dataset.var;
            const cursorPos = textarea.selectionStart;
            const textBefore = textarea.value.substring(0, cursorPos);
            const textAfter = textarea.value.substring(cursorPos);

            textarea.value = textBefore + `{${varName}}` + textAfter;
            textarea.focus();
            textarea.selectionStart = textarea.selectionEnd = cursorPos + varName.length + 2;

            menu.style.display = 'none';
            console.log('Variable insérée:', varName);
        });
    });

    // Fermer le menu si on clique ailleurs
    document.addEventListener('click', (e) => {
        const insertBtnCurrent = document.getElementById('insertVarBtn');
        if (insertBtnCurrent && !insertBtnCurrent.contains(e.target) && !menu.contains(e.target)) {
            menu.style.display = 'none';
        }
    });
}

// Charger les voix disponibles
async function loadVoices() {
    try {
        const response = await authenticatedFetch('/api/tts/voices');

        if (response && response.ok) {
            const voices = await response.json();
            const select = document.getElementById('voice_id');
            select.innerHTML = voices.map(v =>
                `<option value="${v.voice_id}">${v.label}</option>`
            ).join('');
        }
    } catch (err) {
        console.error('Erreur chargement voix:', err);
    }
}

// Tester la voix avec le template actuel
async function testVoiceWithTemplate() {
    const voiceId = document.getElementById('voice_id').value;
    const template = document.getElementById('template').value.trim();

    if (!voiceId) {
        showNotification('Attention', 'Veuillez choisir une voix', 'info');
        return;
    }

    if (!template) {
        showNotification('Attention', 'Veuillez saisir un texte d\'annonce', 'info');
        return;
    }

    // Remplacer les variables par des valeurs fictives
    const testText = template
        .replace(/{station_name}/g, 'Col de la Forclaz')
        .replace(/{wind_avg_kmh}/g, '23')
        .replace(/{wind_max_kmh}/g, '37')
        .replace(/{wind_min_kmh}/g, '18')
        .replace(/{wind_direction_deg}/g, '225')
        .replace(/{wind_direction_cardinal}/g, 'SO')
        .replace(/{wind_direction_name}/g, 'Sud-Ouest')
        .replace(/{measurement_age_minutes}/g, '5');

    try {
        const response = await authenticatedFetch('/api/tts/synthesize', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: testText,
                voice_id: voiceId
            })
        });

        if (response && response.ok) {
            const data = await response.json();
            const audio = new Audio(data.audio_url);
            audio.play();
            showNotification('Lecture', 'Audio en cours de lecture...', 'success');
        }
    } catch (err) {
        console.error('Erreur test voix:', err);
        showNotification('Erreur', 'Erreur lors du test de la voix', 'error');
    }
}

// Charger au démarrage
loadChannels();
loadVoices();
