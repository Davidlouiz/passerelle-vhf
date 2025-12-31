// Gestion des utilisateurs (admin.html)

// Initialisation de la page
initSidebar('admin');
const token = checkAuth();

let currentUserId = null; // ID de l'utilisateur connecté

// Charger les informations de l'utilisateur courant
async function loadCurrentUser() {
    try {
        const response = await authenticatedFetch('/api/auth/me');
        if (response.ok) {
            const data = await response.json();
            currentUserId = data.id;
        }
    } catch (error) {
        console.error('Erreur lors du chargement de l\'utilisateur courant:', error);
    }
}

// Charger la liste des utilisateurs
async function loadUsers() {
    const container = document.getElementById('usersListContainer');

    try {
        const response = await authenticatedFetch('/api/users/');

        if (!response.ok) {
            throw new Error('Erreur lors du chargement des utilisateurs');
        }

        const users = await response.json();

        if (users.length === 0) {
            container.innerHTML = '<p class="text-muted">Aucun utilisateur trouvé.</p>';
            return;
        }

        // Créer un beau tableau
        let html = `
            <table class="table">
                <thead>
                    <tr>
                        <th>Nom d'utilisateur</th>
                        <th>Statut</th>
                        <th>Créé le</th>
                        <th>Dernière connexion</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
        `;

        users.forEach(user => {
            // Formater les dates
            const createdAt = new Date(user.created_at).toLocaleString('fr-FR');
            const lastLogin = user.last_login_at
                ? new Date(user.last_login_at).toLocaleString('fr-FR')
                : 'Jamais';

            // Statut
            const statusBadge = user.must_change_password
                ? '<span class="badge badge-warning">Doit changer le mot de passe</span>'
                : '<span class="badge badge-success">Actif</span>';

            // Vérifier si c'est l'utilisateur courant
            const isCurrentUser = user.id === currentUserId;
            const deleteButton = isCurrentUser
                ? '<button class="btn btn-danger btn-sm" disabled title="Vous ne pouvez pas supprimer votre propre compte">🗑️ Supprimer</button>'
                : `<button class="btn btn-danger btn-sm" onclick="deleteUser(${user.id}, '${user.username}')">🗑️ Supprimer</button>`;

            html += `
                <tr>
                    <td>
                        <strong>${user.username}</strong>
                        ${isCurrentUser ? '<span class="badge badge-info" style="margin-left: 0.5rem;">Vous</span>' : ''}
                    </td>
                    <td>${statusBadge}</td>
                    <td>${createdAt}</td>
                    <td>${lastLogin}</td>
                    <td>${deleteButton}</td>
                </tr>
            `;
        });

        html += `
                </tbody>
            </table>
        `;

        container.innerHTML = html;

    } catch (error) {
        console.error('Erreur:', error);
        container.innerHTML = '<p class="text-danger">Erreur lors du chargement des utilisateurs.</p>';
    }
}

// Créer un nouvel utilisateur
document.getElementById('addUserForm').addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('username').value.trim();

    if (!username) {
        alert('Veuillez saisir un nom d\'utilisateur');
        return;
    }

    try {
        const response = await authenticatedFetch('/api/users/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erreur lors de la création de l\'utilisateur');
        }

        const data = await response.json();

        // Afficher le mot de passe généré dans une modal
        document.getElementById('generatedPassword').textContent = data.generated_password;
        document.getElementById('passwordModal').style.display = 'flex';

        // Réinitialiser le formulaire
        document.getElementById('addUserForm').reset();

        // Recharger la liste des utilisateurs
        await loadUsers();

    } catch (error) {
        console.error('Erreur:', error);
        alert(error.message);
    }
});

// Copier le mot de passe généré
document.getElementById('copyPasswordBtn').addEventListener('click', () => {
    const password = document.getElementById('generatedPassword').textContent;
    navigator.clipboard.writeText(password).then(() => {
        const btn = document.getElementById('copyPasswordBtn');
        const originalText = btn.textContent;
        btn.textContent = '✅ Copié !';
        setTimeout(() => {
            btn.textContent = originalText;
        }, 2000);
    });
});

// Fermer la modal
document.getElementById('closeModalBtn').addEventListener('click', () => {
    document.getElementById('passwordModal').style.display = 'none';
});

// Supprimer un utilisateur
async function deleteUser(userId, username) {
    if (!confirm(`Êtes-vous sûr de vouloir supprimer l'utilisateur "${username}" ?`)) {
        return;
    }

    try {
        const response = await authenticatedFetch(`/api/users/${userId}`, {
            method: 'DELETE'
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Erreur lors de la suppression');
        }

        await loadUsers();

    } catch (error) {
        console.error('Erreur:', error);
        alert(error.message);
    }
}

// Charger la page
(async () => {
    await loadCurrentUser();
    await loadUsers();
})();
