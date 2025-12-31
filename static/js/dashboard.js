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
    // Statut système
    document.getElementById('master-enabled').textContent =
        data.master_enabled ? '✓ Activé' : '✗ Désactivé';

    document.getElementById('master-enabled').className =
        data.master_enabled ? 'stat-value text-success' : 'stat-value text-danger';

    document.getElementById('active-channels').textContent =
        `${data.active_channels} / ${data.total_channels}`;

    document.getElementById('tx-lock-status').textContent =
        data.tx_lock_active ? '🔒 Occupé' : '✓ Libre';

    document.getElementById('runner-status').textContent =
        data.runner_status === 'unknown' ? 'État inconnu' : data.runner_status;

    const statusBadge = document.getElementById('system-status');
    if (data.master_enabled) {
        statusBadge.textContent = 'Système actif';
        statusBadge.className = 'badge badge-success';
    } else {
        statusBadge.textContent = 'Système désactivé';
        statusBadge.className = 'badge badge-danger';
    }

    // Stats TX 24h
    if (data.tx_stats_24h) {
        document.getElementById('tx-total').textContent = data.tx_stats_24h.total;
        document.getElementById('tx-sent').textContent = data.tx_stats_24h.sent;
        document.getElementById('tx-failed').textContent = data.tx_stats_24h.failed;
        document.getElementById('tx-aborted').textContent = data.tx_stats_24h.aborted;
    }

    // Liste des canaux avec stats
    if (data.channels_stats && data.channels_stats.length > 0) {
        const channelsList = document.getElementById('channels-list');
        channelsList.innerHTML = `
            <table class="table">
                <thead>
                    <tr>
                        <th>Canal</th>
                        <th>Statut</th>
                        <th>TX 24h</th>
                        <th>Dernière mesure</th>
                        <th>Prochaine TX</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.channels_stats.map(ch => `
                        <tr>
                            <td><strong>${escapeHtml(ch.name)}</strong></td>
                            <td>
                                <span class="badge ${ch.is_enabled ? 'badge-success' : 'badge-secondary'}">
                                    ${ch.is_enabled ? 'Actif' : 'Inactif'}
                                </span>
                            </td>
                            <td>${ch.tx_count_24h}</td>
                            <td>${formatDate(ch.last_measurement_at)}</td>
                            <td>${formatDate(ch.next_tx_at)}</td>
                        </tr>
                        ${ch.last_error ? `
                        <tr class="error-row">
                            <td colspan="5" class="text-danger">
                                ⚠️ ${escapeHtml(ch.last_error)}
                            </td>
                        </tr>
                        ` : ''}
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    // Dernières transmissions
    if (data.recent_tx && data.recent_tx.length > 0) {
        const recentTx = document.getElementById('recent-tx');
        recentTx.innerHTML = `
            <table class="table table-sm">
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Canal</th>
                        <th>Mode</th>
                        <th>Statut</th>
                    </tr>
                </thead>
                <tbody>
                    ${data.recent_tx.map(tx => `
                        <tr>
                            <td>${new Date(tx.sent_at).toLocaleString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        })}</td>
                            <td>${escapeHtml(tx.channel_name)}</td>
                            <td>
                                <span class="badge badge-${tx.mode === 'SCHEDULED' ? 'primary' : 'info'} badge-sm">
                                    ${tx.mode === 'SCHEDULED' ? 'Auto' : 'Test'}
                                </span>
                            </td>
                            <td>
                                <span class="badge badge-${getStatusClass(tx.status)} badge-sm">
                                    ${getStatusLabel(tx.status)}
                                </span>
                                ${tx.error_message ? `<span title="${escapeHtml(tx.error_message)}">⚠️</span>` : ''}
                            </td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }
}

// Utilitaires
function formatDate(dateStr) {
    if (!dateStr) return '—';
    const date = new Date(dateStr);
    return date.toLocaleString('fr-FR', {
        day: '2-digit',
        month: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function getStatusClass(status) {
    const classes = {
        'SENT': 'success',
        'FAILED': 'danger',
        'ABORTED': 'warning',
        'PENDING': 'info',
    };
    return classes[status] || 'secondary';
}

function getStatusLabel(status) {
    const labels = {
        'SENT': 'Envoyé',
        'FAILED': 'Échec',
        'ABORTED': 'Annulé',
        'PENDING': 'En attente',
    };
    return labels[status] || status;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
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
