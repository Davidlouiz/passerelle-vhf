// timeline.js - Gestion de la timeline prévisionnelle
const token = localStorage.getItem('token');

let currentForecast = null;

// Initialisation
document.addEventListener('DOMContentLoaded', function () {
    if (!token) {
        window.location.href = '/static/index.html';
        return;
    }

    // Event listeners
    document.getElementById('logoutBtn').addEventListener('click', logout);
    document.getElementById('refreshTimeline').addEventListener('click', loadTimeline);
    document.getElementById('forecastHours').addEventListener('change', loadTimeline);

    // Charger la timeline initiale
    loadTimeline();
});

/**
 * Charge et affiche la timeline prévisionnelle
 */
async function loadTimeline() {
    const hours = document.getElementById('forecastHours').value;
    const container = document.getElementById('timelineContainer');
    const eventCountEl = document.getElementById('eventCount');

    container.innerHTML = '<div class="text-center"><div class="spinner"></div>Chargement...</div>';

    try {
        const response = await fetch(`/api/timeline/forecast?hours=${hours}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (response.status === 401) {
            window.location.href = '/static/index.html';
            return;
        }

        if (!response.ok) {
            throw new Error(`Erreur HTTP ${response.status}`);
        }

        currentForecast = await response.json();

        // Mettre à jour le compteur
        eventCountEl.textContent = currentForecast.total_events;

        // Afficher la timeline
        renderTimeline(currentForecast);

    } catch (error) {
        console.error('Erreur lors du chargement de la timeline:', error);
        container.innerHTML = `
            <div class="alert alert-danger">
                <strong>Erreur</strong><br>
                Impossible de charger la timeline : ${escapeHtml(error.message)}
            </div>
        `;
    }
}

/**
 * Rend la timeline dans le DOM
 */
function renderTimeline(forecast) {
    const container = document.getElementById('timelineContainer');

    if (forecast.total_events === 0) {
        container.innerHTML = `
            <div class="alert alert-info">
                <strong>Aucune annonce planifiée</strong><br>
                Aucun canal actif ou aucune mesure disponible pour générer des annonces.
            </div>
        `;
        return;
    }

    // Grouper les événements par jour
    const eventsByDay = groupEventsByDay(forecast.events);

    let html = '';
    for (const [day, events] of Object.entries(eventsByDay)) {
        html += `<div class="timeline-day">`;
        html += `<h4 class="timeline-day-header">${day}</h4>`;
        html += `<div class="timeline-events">`;

        for (const event of events) {
            html += renderTimelineEvent(event);
        }

        html += `</div></div>`;
    }

    container.innerHTML = html;
}

/**
 * Groupe les événements par jour
 */
function groupEventsByDay(events) {
    const grouped = {};

    events.forEach(event => {
        const txDate = new Date(event.tx_time);
        const dayKey = formatDayHeader(txDate);

        if (!grouped[dayKey]) {
            grouped[dayKey] = [];
        }

        grouped[dayKey].push(event);
    });

    return grouped;
}

/**
 * Formate l'en-tête d'un jour (ex: "Aujourd'hui - 15 janvier 2024")
 */
function formatDayHeader(date) {
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    const isToday = date.toDateString() === today.toDateString();
    const isTomorrow = date.toDateString() === tomorrow.toDateString();

    let prefix = '';
    if (isToday) {
        prefix = "Aujourd'hui";
    } else if (isTomorrow) {
        prefix = "Demain";
    }

    const dateStr = date.toLocaleDateString('fr-FR', {
        weekday: 'long',
        day: 'numeric',
        month: 'long',
        year: 'numeric'
    });

    return prefix ? `${prefix} - ${dateStr}` : dateStr;
}

/**
 * Rend un événement de timeline
 */
function renderTimelineEvent(event) {
    const txTime = new Date(event.tx_time);
    const timeStr = txTime.toLocaleTimeString('fr-FR', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit'
    });

    // Badge pour le type de mesure
    const measurementBadge = event.is_simulated
        ? '<span class="badge badge-warning badge-sm">Simulée</span>'
        : '<span class="badge badge-success badge-sm">Réelle</span>';

    // Calculer le délai jusqu'à l'émission
    const now = new Date();
    const delayMs = txTime - now;
    const delayStr = formatDelay(delayMs);

    // Formater les données de mesure
    let measurementInfo = '';
    if (event.measurement) {
        const m = event.measurement;
        measurementInfo = `
            <div class="timeline-measurement">
                <strong>Vent moyen:</strong> ${m.wind_avg_kmh} km/h &nbsp;
                <strong>Rafales:</strong> ${m.wind_max_kmh} km/h
            </div>
        `;
    }

    return `
        <div class="timeline-event">
            <div class="timeline-event-time">
                <div class="time-badge">${timeStr}</div>
                <div class="time-delay text-muted">${delayStr}</div>
            </div>
            <div class="timeline-event-content">
                <div class="timeline-event-header">
                    <h5>${escapeHtml(event.channel_name)}</h5>
                    ${measurementBadge}
                </div>
                <div class="timeline-event-text">
                    <strong>Annonce:</strong> "${escapeHtml(event.rendered_text)}"
                </div>
                ${measurementInfo}
                ${event.is_simulated ? '<p class="text-warning mt-2"><em>⚠️ Utilise une mesure simulée (aucune mesure réelle disponible)</em></p>' : ''}
            </div>
        </div>
    `;
}

/**
 * Formate un délai en texte lisible
 */
function formatDelay(delayMs) {
    if (delayMs < 0) {
        return 'Passé';
    }

    const seconds = Math.floor(delayMs / 1000);
    const minutes = Math.floor(seconds / 60);
    const hours = Math.floor(minutes / 60);
    const days = Math.floor(hours / 24);

    if (days > 0) {
        return `dans ${days}j ${hours % 24}h`;
    } else if (hours > 0) {
        return `dans ${hours}h ${minutes % 60}min`;
    } else if (minutes > 0) {
        return `dans ${minutes}min`;
    } else {
        return `dans ${seconds}s`;
    }
}

/**
 * Échappe le HTML pour éviter les XSS
 */
function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Déconnexion
 */
function logout() {
    localStorage.removeItem('token');
    window.location.href = '/static/index.html';
}
