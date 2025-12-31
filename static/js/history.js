/**
 * Interface d'historique des transmissions
 * 
 * Affiche l'historique des TX avec filtres et pagination
 */

document.addEventListener('DOMContentLoaded', () => {
    // État de l'application
    const state = {
        currentPage: 0,
        pageSize: 50,
        filters: {
            channel_id: null,
            status: null,
            mode: null,
            start_date: null,
            end_date: null,
        }
    };

    // Éléments DOM
    const channelFilter = document.getElementById('channelFilter');
    const statusFilter = document.getElementById('statusFilter');
    const modeFilter = document.getElementById('modeFilter');
    const startDateInput = document.getElementById('startDate');
    const endDateInput = document.getElementById('endDate');
    const applyFiltersBtn = document.getElementById('applyFilters');
    const clearFiltersBtn = document.getElementById('clearFilters');
    const historyTable = document.getElementById('historyTable');
    const paginationControls = document.getElementById('paginationControls');
    const statsContainer = document.getElementById('statsContainer');

    // Initialisation
    init();

    async function init() {
        await loadChannels();
        await loadHistory();
        await loadStats();
        setupEventListeners();
    }

    function setupEventListeners() {
        applyFiltersBtn.addEventListener('click', applyFilters);
        clearFiltersBtn.addEventListener('click', clearFilters);

        // Déconnexion
        const logoutBtn = document.getElementById('logoutBtn');
        if (logoutBtn) {
            logoutBtn.addEventListener('click', logout);
        }
    }

    async function loadChannels() {
        try {
            const response = await authenticatedFetch('/api/channels/');
            if (!response.ok) throw new Error('Erreur chargement canaux');

            const channels = await response.json();

            // Remplir le select
            channelFilter.innerHTML = '<option value="">Tous les canaux</option>';
            channels.forEach(channel => {
                const option = document.createElement('option');
                option.value = channel.id;
                option.textContent = channel.name;
                channelFilter.appendChild(option);
            });
        } catch (error) {
            console.error('Erreur:', error);
        }
    }

    async function loadHistory() {
        try {
            // Construire les paramètres de requête
            const params = new URLSearchParams({
                limit: state.pageSize,
                offset: state.currentPage * state.pageSize,
            });

            // Ajouter les filtres
            if (state.filters.channel_id) params.append('channel_id', state.filters.channel_id);
            if (state.filters.status) params.append('status', state.filters.status);
            if (state.filters.mode) params.append('mode', state.filters.mode);
            if (state.filters.start_date) params.append('start_date', state.filters.start_date);
            if (state.filters.end_date) params.append('end_date', state.filters.end_date);

            const response = await authenticatedFetch(`/api/tx/history?${params}`);
            if (!response.ok) throw new Error('Erreur chargement historique');

            const data = await response.json();

            renderHistory(data.results);
            renderPagination(data.total, data.offset, data.limit);
        } catch (error) {
            console.error('Erreur:', error);
            historyTable.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-danger">
                        Erreur lors du chargement de l'historique
                    </td>
                </tr>
            `;
        }
    }

    function renderHistory(records) {
        if (records.length === 0) {
            historyTable.innerHTML = `
                <tr>
                    <td colspan="8" class="text-center text-muted">
                        Aucune transmission enregistrée
                    </td>
                </tr>
            `;
            return;
        }

        historyTable.innerHTML = records.map(tx => {
            const statusClass = getStatusClass(tx.status);
            const modeLabel = tx.mode === 'SCHEDULED' ? 'Planifiée' : 'Test manuel';

            // Pour les PENDING, afficher planned_at en grisé
            let dateDisplay;
            if (tx.status === 'PENDING') {
                dateDisplay = tx.planned_at ?
                    `<span style="color: #999;">${new Date(tx.planned_at).toLocaleString('fr-FR')}</span>` :
                    '<span style="color: #999;">-</span>';
            } else {
                dateDisplay = tx.sent_at ?
                    new Date(tx.sent_at).toLocaleString('fr-FR') :
                    '-';
            }

            return `
                <tr>
                    <td>${dateDisplay}</td>
                    <td><strong>${escapeHtml(tx.channel_name)}</strong></td>
                    <td>
                        <span class="badge badge-${tx.mode === 'SCHEDULED' ? 'primary' : 'info'}">
                            ${modeLabel}
                        </span>
                    </td>
                    <td>
                        <span class="badge badge-${statusClass}">
                            ${getStatusLabel(tx.status)}
                        </span>
                    </td>
                    <td class="text-truncate" style="max-width: 300px;" title="${escapeHtml(tx.rendered_text)}">
                        ${escapeHtml(tx.rendered_text)}
                    </td>
                    <td>
                        ${tx.station_id || '-'}
                    </td>
                    <td>
                        ${tx.error_message ?
                    `<span class="text-danger" title="${escapeHtml(tx.error_message)}">⚠️</span>` :
                    '-'}
                    </td>
                </tr>
            `;
        }).join('');
    }

    function renderPagination(total, offset, limit) {
        const totalPages = Math.ceil(total / limit);
        const currentPage = Math.floor(offset / limit);

        if (totalPages <= 1) {
            paginationControls.innerHTML = `
                <div class="text-muted">
                    ${total} résultat${total > 1 ? 's' : ''}
                </div>
            `;
            return;
        }

        paginationControls.innerHTML = `
            <div class="pagination-info">
                Page ${currentPage + 1} / ${totalPages} (${total} résultat${total > 1 ? 's' : ''})
            </div>
            <div class="pagination-buttons">
                <button class="btn btn-sm btn-secondary" 
                        ${currentPage === 0 ? 'disabled' : ''} 
                        onclick="changePage(${currentPage - 1})">
                    ← Précédent
                </button>
                <button class="btn btn-sm btn-secondary" 
                        ${currentPage === totalPages - 1 ? 'disabled' : ''} 
                        onclick="changePage(${currentPage + 1})">
                    Suivant →
                </button>
            </div>
        `;
    }

    async function loadStats() {
        try {
            const response = await authenticatedFetch('/api/tx/stats?hours=24');
            if (!response.ok) throw new Error('Erreur chargement stats');

            const stats = await response.json();
            renderStats(stats);
        } catch (error) {
            console.error('Erreur stats:', error);
        }
    }

    function renderStats(stats) {
        statsContainer.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-value">${stats.total}</div>
                    <div class="stat-label">Total 24h</div>
                </div>
                <div class="stat-card stat-success">
                    <div class="stat-value">${stats.by_status.SENT || 0}</div>
                    <div class="stat-label">Envoyées</div>
                </div>
                <div class="stat-card stat-danger">
                    <div class="stat-value">${stats.by_status.FAILED || 0}</div>
                    <div class="stat-label">Échecs</div>
                </div>
                <div class="stat-card stat-warning">
                    <div class="stat-value">${stats.by_status.ABORTED || 0}</div>
                    <div class="stat-label">Annulées</div>
                </div>
            </div>
        `;
    }

    function applyFilters() {
        state.filters.channel_id = channelFilter.value || null;
        state.filters.status = statusFilter.value || null;
        state.filters.mode = modeFilter.value || null;
        
        // Convertir les dates locales en UTC ISO pour l'API
        if (startDateInput.value) {
            const localDate = new Date(startDateInput.value);
            state.filters.start_date = localDate.toISOString();
        } else {
            state.filters.start_date = null;
        }
        
        if (endDateInput.value) {
            const localDate = new Date(endDateInput.value);
            state.filters.end_date = localDate.toISOString();
        } else {
            state.filters.end_date = null;
        }
        
        state.currentPage = 0;

        loadHistory();
    }

    function clearFilters() {
        channelFilter.value = '';
        statusFilter.value = '';
        modeFilter.value = '';
        startDateInput.value = '';
        endDateInput.value = '';

        state.filters = {
            channel_id: null,
            status: null,
            mode: null,
            start_date: null,
            end_date: null,
        };
        state.currentPage = 0;

        loadHistory();
    }

    // Fonction globale pour la pagination
    window.changePage = function (page) {
        state.currentPage = page;
        loadHistory();
    };

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
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async function logout() {
        try {
            await fetch('/api/auth/logout', { method: 'POST' });
            window.location.href = '/static/index.html';
        } catch (error) {
            console.error('Erreur déconnexion:', error);
        }
    }
});
