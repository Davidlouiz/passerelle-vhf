"""
Application FastAPI principale.

Point d'entrée de l'API et serveur de fichiers statiques.
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

from app.database import init_db

# Créer l'application
app = FastAPI(
    title="Passerelle VHF",
    description="Système d'annonces vocales pour balises météo sur radio VHF",
    version="1.0.0"
)

# CORS (pour développement)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restreindre en production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialiser la DB au démarrage
@app.on_event("startup")
async def startup_event():
    """Initialise la base de données au démarrage."""
    init_db()

# TODO: Ajouter les routers
# from app.routers import auth, channels, providers, tts, status
# app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
# app.include_router(channels.router, prefix="/api/channels", tags=["channels"])
# app.include_router(providers.router, prefix="/api/providers", tags=["providers"])
# app.include_router(tts.router, prefix="/api/tts", tags=["tts"])
# app.include_router(status.router, prefix="/api/status", tags=["status"])

# Servir les fichiers statiques du frontend
frontend_path = Path(__file__).parent.parent / "frontend"
if frontend_path.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    
    @app.get("/")
    async def serve_frontend():
        """Sert la page d'accueil."""
        return FileResponse(str(frontend_path / "index.html"))

# Endpoint de santé
@app.get("/health")
async def health_check():
    """Endpoint de santé pour vérifier que l'API fonctionne."""
    return {"status": "ok", "service": "vhf-balise"}
