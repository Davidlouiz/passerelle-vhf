/**
 * Interface JavaScript pour test de synthèse vocale (TTS)
 */

let currentAudio = null;

/**
 * Charge la liste des voix disponibles au démarrage
 */
async function loadVoices() {
    try {
        const response = await fetch('/api/tts/voices', {
            headers: {
                'Authorization': `Bearer ${getToken()}`
            }
        });

        if (!response.ok) {
            throw new Error('Erreur lors du chargement des voix');
        }

        const voices = await response.json();
        const select = document.getElementById('voice-select');
        select.innerHTML = '';

        if (voices.length === 0) {
            select.innerHTML = '<option value="">Aucune voix disponible</option>';
            showStatus('error', 'Aucune voix TTS disponible. Vérifiez l\'installation de Piper.');
            return;
        }

        voices.forEach(voice => {
            const option = document.createElement('option');
            option.value = voice.voice_id;
            option.textContent = `${voice.label} (${voice.languages.join(', ')})`;
            select.appendChild(option);
        });

        // Sélectionner la première voix par défaut
        if (voices.length > 0) {
            select.value = voices[0].voice_id;
        }

        // Mettre à jour le compteur de voix
        document.getElementById('voice-count').textContent = voices.length;

    } catch (error) {
        console.error('Erreur:', error);
        showStatus('error', `Erreur : ${error.message}`);
    }
}

/**
 * Synthétise le texte et joue l'audio
 */
async function synthesizeAndPlay() {
    const textInput = document.getElementById('text-input');
    const voiceSelect = document.getElementById('voice-select');
    const synthesizeBtn = document.getElementById('synthesize-btn');
    const stopBtn = document.getElementById('stop-btn');

    const text = textInput.value.trim();
    const voiceId = voiceSelect.value;

    if (!text) {
        showStatus('error', 'Veuillez saisir un texte à synthétiser.');
        return;
    }

    if (!voiceId) {
        showStatus('error', 'Veuillez sélectionner une voix.');
        return;
    }

    // Désactiver le bouton pendant le traitement
    synthesizeBtn.disabled = true;
    synthesizeBtn.textContent = '⏳ Synthèse en cours...';
    showStatus('info', 'Synthèse en cours...');

    try {
        const response = await fetch('/api/tts/synthesize', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getToken()}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: text,
                voice_id: voiceId,
                voice_params: {}
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erreur lors de la synthèse');
        }

        const result = await response.json();

        // Afficher le lecteur audio
        const audioPlayer = document.getElementById('audio-player');
        const audioElement = document.getElementById('audio-element');

        audioElement.src = result.audio_url;
        audioPlayer.style.display = 'block';

        // Stocker la référence pour pouvoir arrêter
        currentAudio = audioElement;

        // Jouer automatiquement
        audioElement.play();

        // Afficher le bouton stop
        stopBtn.style.display = 'inline-block';

        // Masquer le bouton stop quand l'audio se termine
        audioElement.onended = () => {
            stopBtn.style.display = 'none';
        };

        // Construire le message de succès avec les infos disponibles
        let successMessage = '✅ Audio synthétisé avec succès !';
        if (result.duration_seconds !== undefined && result.file_size_bytes !== undefined) {
            const durationStr = result.duration_seconds.toFixed(1);
            const sizeKb = (result.file_size_bytes / 1024).toFixed(1);
            successMessage += ` (${durationStr}s, ${sizeKb} Ko)`;
        }
        showStatus('success', successMessage);

    } catch (error) {
        console.error('Erreur:', error);
        showStatus('error', `❌ Erreur : ${error.message}`);
    } finally {
        synthesizeBtn.disabled = false;
        synthesizeBtn.textContent = '🔊 Synthétiser et écouter';
    }
}

/**
 * Arrête la lecture audio
 */
function stopAudio() {
    if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        document.getElementById('stop-btn').style.display = 'none';
    }
}

/**
 * Charge un exemple de texte dans le champ de saisie
 */
function loadExample(button) {
    const text = button.textContent.trim();
    document.getElementById('text-input').value = text;

    // Animation visuelle
    button.style.background = '#d4edda';
    setTimeout(() => {
        button.style.background = '#f9f9f9';
    }, 300);
}

/**
 * Affiche un message de statut
 */
function showStatus(type, message) {
    const statusDiv = document.getElementById('audio-status');
    statusDiv.className = `status-message ${type}`;
    statusDiv.textContent = message;
    statusDiv.style.display = 'block';

    // Masquer automatiquement après 5 secondes (sauf pour les erreurs)
    if (type !== 'error') {
        setTimeout(() => {
            statusDiv.style.display = 'none';
        }, 5000);
    }
}

/**
 * Déconnexion
 */
function logout() {
    localStorage.removeItem('token');
    window.location.href = '/login.html';
}

/**
 * Obtient le token JWT depuis le localStorage
 */
function getToken() {
    return localStorage.getItem('token');
}

/**
 * Vérifie l'authentification au chargement
 */
function checkAuth() {
    const token = getToken();
    if (!token) {
        window.location.href = '/login.html';
        return false;
    }
    return true;
}

/**
 * Initialisation au chargement de la page
 */
document.addEventListener('DOMContentLoaded', () => {
    if (!checkAuth()) return;

    loadVoices();

    // Gérer la touche Entrée (avec Ctrl/Cmd) pour synthétiser
    document.getElementById('text-input').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            synthesizeAndPlay();
        }
    });
});
