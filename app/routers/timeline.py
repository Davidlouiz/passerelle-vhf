"""
Router pour la timeline prévisionnelle.

Affiche les transmissions planifiées pour les prochaines 24h.
"""

from datetime import datetime, timedelta
from typing import List, Dict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
import json

from app.database import get_db
from app.models import Channel, ChannelRuntime
from app.dependencies import get_current_user
from app.providers.manager import provider_manager
from app.services.template import TemplateRenderer

router = APIRouter()


@router.get("/forecast")
def get_timeline_forecast(
    hours: int = Query(24, ge=1, le=168, description="Nombre d'heures à prévoir"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Génère une timeline prévisionnelle des TX planifiées.
    
    Pour chaque canal actif :
    - Récupère la dernière mesure (ou simule si pas disponible)
    - Calcule les prochaines TX basées sur les offsets
    - Rend le template pour obtenir le texte qui sera annoncé
    
    Args:
        hours: Nombre d'heures dans le futur à prévoir (défaut: 24h)
        
    Returns:
        Liste chronologique des TX planifiées par canal
    """
    now = datetime.utcnow()
    forecast_until = now + timedelta(hours=hours)
    
    # Récupérer les canaux actifs
    channels = db.query(Channel).filter_by(is_enabled=True).all()
    
    timeline_events = []
    template_renderer = TemplateRenderer()
    
    for channel in channels:
        # Récupérer le provider
        provider = provider_manager.get_provider(channel.provider_id)
        if not provider:
            continue
        
        # Charger les credentials du provider
        provider_manager.load_credentials(db)
        
        # Tenter de récupérer la dernière mesure
        measurement = None
        try:
            measurement = provider.get_latest_measurement(str(channel.station_id))
        except Exception as e:
            # Si échec, utiliser des données simulées
            measurement = None
        
        # Parser les offsets
        try:
            offsets = json.loads(channel.offsets_seconds_json)
        except:
            offsets = [0]
        
        # Si pas de mesure réelle, simuler une mesure pour la prévisualisation
        if measurement is None:
            measurement_time = now
            measurement_data = {
                "measurement_at": measurement_time,
                "wind_avg_kmh": 20.0,  # Valeur fictive
                "wind_max_kmh": 28.0,
                "wind_min_kmh": 15.0,
                "wind_direction_deg": 270,
            }
            is_simulated = True
        else:
            measurement_time = measurement.measurement_at
            measurement_data = {
                "measurement_at": measurement_time,
                "wind_avg_kmh": measurement.wind_avg_kmh,
                "wind_max_kmh": measurement.wind_max_kmh,
                "wind_min_kmh": measurement.wind_min_kmh,
                "wind_direction_deg": getattr(measurement, 'wind_direction_deg', None),
            }
            is_simulated = False
        
        # Calculer les prochaines TX pour ce canal
        # On suppose une nouvelle mesure toutes les measurement_period_seconds
        num_cycles = int((hours * 3600) / channel.measurement_period_seconds) + 1
        
        for cycle in range(num_cycles):
            # Timestamp de la mesure hypothétique
            cycle_measurement_time = now + timedelta(seconds=cycle * channel.measurement_period_seconds)
            
            if cycle_measurement_time > forecast_until:
                break
            
            # Pour chaque offset, créer un événement TX
            for offset_seconds in offsets:
                tx_time = cycle_measurement_time + timedelta(seconds=offset_seconds)
                
                # Ne garder que les TX futures
                if tx_time < now or tx_time > forecast_until:
                    continue
                
                # Rendre le template pour obtenir le texte
                try:
                    rendered_text = template_renderer.render(
                        channel.template_text,
                        station_name=channel.name,
                        **measurement_data
                    )
                except Exception as e:
                    rendered_text = f"Erreur de rendu : {str(e)}"
                
                timeline_events.append({
                    "channel_id": channel.id,
                    "channel_name": channel.name,
                    "tx_time": tx_time.isoformat(),
                    "measurement_time": cycle_measurement_time.isoformat(),
                    "offset_seconds": offset_seconds,
                    "rendered_text": rendered_text,
                    "measurement": measurement_data if cycle == 0 else None,  # Seulement pour le premier cycle
                    "is_simulated": is_simulated if cycle == 0 else True,
                })
    
    # Trier par heure de TX
    timeline_events.sort(key=lambda x: x["tx_time"])
    
    return {
        "forecast_start": now.isoformat(),
        "forecast_end": forecast_until.isoformat(),
        "total_events": len(timeline_events),
        "events": timeline_events,
    }


@router.get("/next")
def get_next_transmissions(
    limit: int = Query(10, ge=1, le=50, description="Nombre de prochaines TX"),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Retourne les N prochaines transmissions planifiées (tous canaux confondus).
    
    Args:
        limit: Nombre max de TX à retourner
        
    Returns:
        Liste des prochaines TX triées par date
    """
    # Utiliser le même endpoint mais avec un nombre d'heures adapté
    forecast = get_timeline_forecast(hours=48, db=db, current_user=current_user)
    
    # Ne garder que les N premières
    events = forecast["events"][:limit]
    
    return {
        "next_transmissions": events,
        "count": len(events),
    }
