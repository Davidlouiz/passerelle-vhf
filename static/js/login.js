// Gestion du login
document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const errorDiv = document.getElementById('error-message');

    errorDiv.style.display = 'none';

    try {
        const response = await fetch('/api/auth/login', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ username, password })
        });

        if (response.ok) {
            const data = await response.json();

            // Sauver le token
            localStorage.setItem('token', data.access_token);

            // Vérifier si changement de mot de passe requis
            if (data.must_change_password) {
                window.location.href = '/static/change-password.html';
            } else {
                window.location.href = '/static/dashboard.html';
            }
        } else {
            const error = await response.json();
            errorDiv.textContent = error.detail || 'Erreur d\'authentification';
            errorDiv.style.display = 'block';
        }
    } catch (err) {
        errorDiv.textContent = 'Erreur de connexion au serveur';
        errorDiv.style.display = 'block';
    }
});
