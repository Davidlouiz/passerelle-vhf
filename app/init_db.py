"""
Script d'initialisation de la base de données.

Crée le schéma et insère les données par défaut.
"""

from app.database import init_db, get_db_session
from app.models import User, SystemSettings
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_default_data():
    """Crée les données par défaut (admin, system_settings)."""
    with get_db_session() as db:
        # Créer utilisateur admin par défaut
        admin = db.query(User).filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=pwd_context.hash("admin"),
                must_change_password=True,
            )
            db.add(admin)
            print("✓ Utilisateur 'admin' créé (mot de passe: admin)")

        # Créer system_settings par défaut
        settings = db.query(SystemSettings).filter_by(id=1).first()
        if not settings:
            settings = SystemSettings(
                id=1,
                master_enabled=False,
                poll_interval_seconds=60,
                inter_announcement_pause_seconds=10,
                ptt_gpio_pin=None,
                ptt_active_level=1,
                ptt_lead_ms=500,
                ptt_tail_ms=500,
                tx_timeout_seconds=30,
            )
            db.add(settings)
            print("✓ Paramètres système par défaut créés")

        db.commit()


if __name__ == "__main__":
    print("Initialisation de la base de données...")
    init_db()
    create_default_data()
    print("✓ Initialisation terminée")
