// Gestion de la page paramètres système

let currentSettings = null;
let runnerStatus = 'unknown';
let emissionEnabled = false;

// Charger les paramètres au chargement de la page
document.addEventListener('DOMContentLoaded', () => {
    loadSettings();
    loadRunnerStatus();
    
    // Gestionnaire du formulaire
    document.getElementById('settingsForm').addEventListener('submit', saveSettings);
    
    // Gestionnaires des boutons
    document.getElementById('runnerToggleBtn').addEventListener('click', toggleRunner);
    document.getElementById('emissionToggleBtn').addEventListener('click', toggleEmission);
    
    // Rafraîchir les statuts toutes les 5 secondes
    setInterval(() => {
        loadRunnerStatus();
        loadSettings();
    }, 5000);
});

// Charger les paramètres depuis l'API
async function loadSettings() {
    try {
        showLoading(true);
        const response = await authenticatedFetch('/api/settings');
        
        if (!response.ok) {
            throw new Error('Erreur lors du chargement des paramètres');
        }
        
        currentSettings = await response.json();
        displaySettings(currentSettings);
        
    } catch (error) {
        console.error('Erreur:', error);
        showError('Impossible de charger les paramètres système');
    } finally {
        showLoading(false);
    }
}

// Afficher les paramètres dans le formulaire
function displaySettings(settings) {
    emissionEnabled = settings.master_enabled;
    document.getElementById('poll_interval_seconds').value = settings.poll_interval_seconds;
    document.getElementById('inter_announcement_pause_seconds').value = settings.inter_announcement_pause_seconds;
    
    // PTT settings
    document.getElementById('ptt_gpio_pin').value = settings.ptt_gpio_pin || '';
    document.getElementById('ptt_active_level').value = settings.ptt_active_level;
    document.getElementById('ptt_lead_ms').value = settings.ptt_lead_ms;
    document.getElementById('ptt_tail_ms').value = settings.ptt_tail_ms;
    
    // Afficher timeout (lecture seule)
    document.getElementById('tx_timeout_display').textContent = settings.tx_timeout_seconds + ' secondes';
    
    // Mettre à jour les statuts
    updateMasterStatus(settings.master_enabled);
    updateEmissionButton(settings.master_enabled);
}

// Mettre à jour l'affichage du statut master
function updateMasterStatus(enabled) {
    const statusEl = document.getElementById('masterStatus');
    if (enabled) {
        statusEl.innerHTML = '<span class="badge badge-success">✓ Activé</span>';
    } else {
        statusEl.innerHTML = '<span class="badge badge-danger">✗ Désactivé</span>';
    }
}

// Mettre à jour le bouton d'émission
function updateEmissionButton(enabled) {
    const toggleBtn = document.getElementById('emissionToggleBtn');
    emissionEnabled = enabled;
    
    if (enabled) {
        toggleBtn.textContent = 'Désactiver l\'émission';
        toggleBtn.className = 'btn btn-danger';
        toggleBtn.disabled = false;
    } else {
        toggleBtn.textContent = 'Activer l\'émission';
        toggleBtn.className = 'btn btn-success';
        toggleBtn.disabled = false;
    }
}

// Charger le statut du runner
async function loadRunnerStatus() {
    try {
        const response = await authenticatedFetch('/api/status');
        
        if (!response.ok) {
            throw new Error('Erreur lors du chargement du statut runner');
        }
        
        const data = await response.json();
        runnerStatus = data.runner_status;
        updateRunnerStatus(runnerStatus);
        
    } catch (error) {
        console.error('Erreur:', error);
        runnerStatus = 'unknown';
        updateRunnerStatus('unknown');
    }
}

// Mettre à jour l'affichage du statut runner
function updateRunnerStatus(status) {
    const statusEl = document.getElementById('runnerStatus');
    const toggleBtn = document.getElementById('runnerToggleBtn');
    
    if (status === 'running') {
        statusEl.innerHTML = '<span class="badge badge-success">✓ Activé</span>';
        toggleBtn.textContent = 'Désactiver la réception';
        toggleBtn.className = 'btn btn-danger';
        toggleBtn.disabled = false;
    } else if (status === 'stopped') {
        statusEl.innerHTML = '<span class="badge badge-danger">✗ Désactivé</span>';
        toggleBtn.textContent = 'Activer la réception';
        toggleBtn.className = 'btn btn-success';
        toggleBtn.disabled = false;
    } else {
        statusEl.innerHTML = '<span class="badge badge-secondary">? État inconnu</span>';
        toggleBtn.textContent = 'État inconnu';
        toggleBtn.className = 'btn btn-secondary';
        toggleBtn.disabled = true;
    }
}

// Basculer le runner (démarrer/arrêter)
async function toggleRunner() {
    const action = runnerStatus === 'running' ? 'stop' : 'start';
    const endpoint = `/api/status/runner/${action}`;
    
    try {
        showLoading(true);
        
        const response = await authenticatedFetch(endpoint, {
            method: 'POST'
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `Erreur lors de l'opération`);
        }
        
        const result = await response.json();
        showSuccess(result.message);
        
        // Rafraîchir le statut immédiatement
        await loadRunnerStatus();
        
    } catch (error) {
        console.error('Erreur:', error);
        showError(error.message);
    } finally {
        showLoading(false);
    }
}

// Basculer l'émission (activer/désactiver)
async function toggleEmission() {
    const newState = !emissionEnabled;
    
    try {
        showLoading(true);
        
        // Récupérer les paramètres actuels
        const pttGpioValue = document.getElementById('ptt_gpio_pin').value.trim();
        
        const data = {
            master_enabled: newState,
            poll_interval_seconds: parseInt(document.getElementById('poll_interval_seconds').value),
            inter_announcement_pause_seconds: parseInt(document.getElementById('inter_announcement_pause_seconds').value),
            ptt_gpio_pin: pttGpioValue === '' ? null : parseInt(pttGpioValue),
            ptt_active_level: parseInt(document.getElementById('ptt_active_level').value),
            ptt_lead_ms: parseInt(document.getElementById('ptt_lead_ms').value),
            ptt_tail_ms: parseInt(document.getElementById('ptt_tail_ms').value),
        };
        
        const response = await authenticatedFetch('/api/settings', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erreur lors du basculement');
        }
        
        const result = await response.json();
        currentSettings = result;
        displaySettings(result);
        showSuccess(newState ? 'Émission activée' : 'Émission désactivée');
        
    } catch (error) {
        console.error('Erreur:', error);
        showError(error.message);
    } finally {
        showLoading(false);
    }
}

// Sauvegarder les paramètres
async function saveSettings(event) {
    event.preventDefault();
    
    // Récupérer les valeurs du formulaire
    const pttGpioValue = document.getElementById('ptt_gpio_pin').value.trim();
    
    const data = {
        master_enabled: emissionEnabled, // Utiliser l'état actuel de l'émission
        poll_interval_seconds: parseInt(document.getElementById('poll_interval_seconds').value),
        inter_announcement_pause_seconds: parseInt(document.getElementById('inter_announcement_pause_seconds').value),
        ptt_gpio_pin: pttGpioValue === '' ? null : parseInt(pttGpioValue),
        ptt_active_level: parseInt(document.getElementById('ptt_active_level').value),
        ptt_lead_ms: parseInt(document.getElementById('ptt_lead_ms').value),
        ptt_tail_ms: parseInt(document.getElementById('ptt_tail_ms').value),
    };
    
    try {
        showLoading(true);
        
        const response = await authenticatedFetch('/api/settings', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erreur lors de la sauvegarde');
        }
        
        currentSettings = await response.json();
        displaySettings(currentSettings);
        showSuccess('Paramètres sauvegardés avec succès');
        
    } catch (error) {
        console.error('Erreur:', error);
        showError(error.message);
    } finally {
        showLoading(false);
    }
}

// Afficher un message d'erreur
function showError(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger';
    alertDiv.textContent = message;
    
    const content = document.querySelector('.content');
    content.insertBefore(alertDiv, content.firstChild);
    
    setTimeout(() => alertDiv.remove(), 5000);
}

// Afficher un message de succès
function showSuccess(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-success';
    alertDiv.textContent = message;
    
    const content = document.querySelector('.content');
    content.insertBefore(alertDiv, content.firstChild);
    
    setTimeout(() => alertDiv.remove(), 3000);
}

// Afficher/masquer le chargement
function showLoading(show) {
    const submitBtn = document.querySelector('button[type="submit"]');
    if (show) {
        submitBtn.disabled = true;
        submitBtn.textContent = 'Enregistrement...';
    } else {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Enregistrer les paramètres';
    }
}
