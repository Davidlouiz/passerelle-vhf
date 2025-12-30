"""
Configuration et connexion à la base de données SQLite.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from pathlib import Path
from typing import Generator
import os

from app.models import Base

# Chemin vers la base de données
DATA_DIR = Path(os.getenv("VHF_DATA_DIR", "/opt/vhf-balise/data"))
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DATA_DIR}/vhf-balise.db"

# Créer le moteur SQLite avec connection pooling approprié
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False  # True pour debug SQL
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialise la base de données (crée toutes les tables)."""
    Base.metadata.create_all(bind=engine)
    print(f"✓ Base de données initialisée : {DATABASE_URL}")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency pour FastAPI - fournit une session DB.
    
    Utilisation:
        @app.get("/...")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_session():
    """
    Context manager pour obtenir une session DB (usage hors FastAPI).
    
    Utilisation:
        with get_db_session() as db:
            db.query(...)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
