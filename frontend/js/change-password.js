// Gestion du changement de mot de passe
document.getElementById('changePasswordForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const oldPassword = document.getElementById('old_password').value;
    const newPassword = document.getElementById('new_password').value;
    const confirmPassword = document.getElementById('confirm_password').value;
    const errorDiv = document.getElementById('error-message');
    const successDiv = document.getElementById('success-message');

    errorDiv.style.display = 'none';
    successDiv.style.display = 'none';

    // Vérifier que les mots de passe correspondent
    if (newPassword !== confirmPassword) {
        errorDiv.textContent = 'Les mots de passe ne correspondent pas';
        errorDiv.style.display = 'block';
        return;
    }

    // Vérifier la longueur minimale
    if (newPassword.length < 8) {
        errorDiv.textContent = 'Le mot de passe doit contenir au moins 8 caractères';
        errorDiv.style.display = 'block';
        return;
    }

    const token = localStorage.getItem('token');
    if (!token) {
        window.location.href = '/';
        return;
    }

    try {
        const response = await fetch('/api/auth/change-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                old_password: oldPassword,
                new_password: newPassword
            })
        });

        if (response.ok) {
            successDiv.textContent = 'Mot de passe changé avec succès ! Redirection...';
            successDiv.style.display = 'block';

            // Rediriger vers le dashboard après 2 secondes
            setTimeout(() => {
                window.location.href = '/static/dashboard.html';
            }, 2000);
        } else {
            const error = await response.json();
            errorDiv.textContent = error.detail || 'Erreur lors du changement de mot de passe';
            errorDiv.style.display = 'block';
        }
    } catch (err) {
        errorDiv.textContent = 'Erreur de connexion au serveur';
        errorDiv.style.display = 'block';
    }
});

// Gérer la déconnexion
document.getElementById('logoutLink').addEventListener('click', (e) => {
    e.preventDefault();
    localStorage.removeItem('token');
    window.location.href = '/';
});
