"""API Router pour la gestion des providers météo."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from pydantic import BaseModel, HttpUrl
from typing import Optional

from app.database import get_db
from app.models import ProviderCredential, AuditLog
from app.dependencies import get_current_user
from app.providers.ffvl import FFVLProvider
from app.providers.openwindmap import OpenWindMapProvider
import datetime

router = APIRouter()


class ProviderInfo(BaseModel):
    """Information sur un provider."""

    provider_id: str
    name: str
    requires_auth: bool
    description: str
    is_configured: bool


class CredentialUpdate(BaseModel):
    """Mise à jour des credentials d'un provider."""

    provider_id: str
    api_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class StationResolutionRequest(BaseModel):
    """Requête de résolution d'une station depuis son URL."""

    visual_url: str


class StationResolutionResponse(BaseModel):
    """Réponse de résolution d'une station."""

    provider_id: str
    station_id: int
    station_name: str


@router.get("/", response_model=list[ProviderInfo])
def list_providers(
    db: Session = Depends(get_db), current_user=Depends(get_current_user)
):
    """Liste tous les providers disponibles avec leur statut de configuration."""

    # Récupérer les credentials existantes
    credentials = {c.provider_id: c for c in db.query(ProviderCredential).all()}

    providers = [
        ProviderInfo(
            provider_id="ffvl",
            name="FFVL (Fédération Française de Vol Libre)",
            requires_auth=True,
            description="Accès aux balises météo FFVL via balisemeteo.com",
            is_configured="ffvl" in credentials
            and bool(credentials["ffvl"].credentials_json.get("api_key")),
        ),
        ProviderInfo(
            provider_id="openwindmap",
            name="OpenWindMap (API Pioupiou)",
            requires_auth=False,
            description="Accès gratuit aux stations Pioupiou et Windbird",
            is_configured=True,  # Toujours configuré (pas d'auth requise)
        ),
    ]

    return providers


@router.post("/credentials")
def update_credentials(
    data: CredentialUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Met à jour les credentials d'un provider."""

    if data.provider_id not in ["ffvl", "openwindmap"]:
        raise HTTPException(status_code=400, detail="Provider inconnu")

    # OpenWindMap ne nécessite pas de credentials
    if data.provider_id == "openwindmap":
        raise HTTPException(
            status_code=400, detail="OpenWindMap ne nécessite pas de credentials"
        )

    # Vérifier si les credentials existent déjà
    credential = (
        db.query(ProviderCredential)
        .filter(ProviderCredential.provider_id == data.provider_id)
        .first()
    )

    # Construire le dict de credentials
    credentials_dict = {}
    if data.api_key is not None:
        credentials_dict["api_key"] = data.api_key
    if data.username is not None:
        credentials_dict["username"] = data.username
    if data.password is not None:
        credentials_dict["password"] = data.password

    if credential:
        # Mise à jour - fusionner avec l'existant
        existing = credential.credentials_json or {}
        existing.update(credentials_dict)
        credential.credentials_json = existing
        credential.updated_at = datetime.datetime.now(datetime.timezone.utc)
    else:
        # Création
        credential = ProviderCredential(
            provider_id=data.provider_id,
            credentials_json=credentials_dict,
        )
        db.add(credential)

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action=f"UPDATE_PROVIDER_CREDENTIALS",
        details_json=f"Provider: {data.provider_id}",
        ip_address="127.0.0.1",  # TODO: récupérer vraie IP
    )
    db.add(audit)

    db.commit()

    return {"message": "Credentials mis à jour avec succès"}


@router.post("/resolve-station", response_model=StationResolutionResponse)
def resolve_station(
    data: StationResolutionRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Résout une station depuis son URL visuelle."""

    url = data.visual_url.strip()

    # Essayer FFVL d'abord
    if "balisemeteo.com" in url or "ffvl" in url.lower():
        provider = FFVLProvider()
        station_info = provider.resolve_station_from_url(url)
        return StationResolutionResponse(
            provider_id=station_info.provider_id,
            station_id=int(station_info.station_id),
            station_name=station_info.station_name,
        )

    # Essayer OpenWindMap
    if "openwindmap.org" in url or "pioupiou" in url.lower():
        provider = OpenWindMapProvider()
        station_info = provider.resolve_station_from_url(url)
        return StationResolutionResponse(
            provider_id=station_info.provider_id,
            station_id=int(station_info.station_id),
            station_name=station_info.station_name,
        )

    raise HTTPException(
        status_code=400,
        detail="URL non reconnue. Formats supportés : balisemeteo.com (FFVL) ou openwindmap.org (Pioupiou)",
    )


class MeasurementTestRequest(BaseModel):
    """Requête de test de récupération de mesure."""

    provider_id: str
    station_id: str


class MeasurementResponse(BaseModel):
    """Réponse avec une mesure météo."""

    measurement_at: str
    wind_avg_kmh: float
    wind_max_kmh: float
    wind_min_kmh: Optional[float] = None


@router.post("/test-measurement", response_model=MeasurementResponse)
async def test_measurement(
    data: MeasurementTestRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Teste la récupération d'une mesure depuis un provider."""

    from app.providers.manager import provider_manager

    # Charger les credentials depuis la DB
    provider_manager.load_credentials(db)

    # Récupérer le provider
    provider = provider_manager.get_provider(data.provider_id)
    if not provider:
        raise HTTPException(
            status_code=400, detail=f"Provider {data.provider_id} inconnu"
        )

    # Récupérer la mesure
    try:
        measurement = await provider.fetch_measurement(data.station_id)

        if not measurement:
            raise HTTPException(
                status_code=404,
                detail=f"Aucune mesure disponible pour la station {data.station_id}",
            )

        return MeasurementResponse(
            measurement_at=measurement.measurement_at.isoformat() + "Z"
            if not measurement.measurement_at.isoformat().endswith("Z")
            else measurement.measurement_at.isoformat(),
            wind_avg_kmh=measurement.wind_avg_kmh,
            wind_max_kmh=measurement.wind_max_kmh,
            wind_min_kmh=measurement.wind_min_kmh,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de la récupération: {str(e)}"
        )
