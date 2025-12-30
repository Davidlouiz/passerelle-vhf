"""
Runner/Scheduler principal.

Polling des providers, détection de nouvelles mesures, planification et exécution des TX.
"""
import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import random

from sqlalchemy.orm import Session

from app.database import get_db_session, init_db
from app.models import Channel, ChannelRuntime, SystemSettings, TxHistory
from app.providers.manager import provider_manager
from app.tts.piper_engine import PiperEngine
from app.tts.cache import TTSCacheService
from app.services.template import TemplateRenderer
from app.services.transmission import TransmissionService
from app.ptt.controller import MockPTTController, GPIOPTTController
from app.utils import compute_hash, is_measurement_expired
from app.exceptions import MeasurementExpiredError, PTTError

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("/opt/vhf-balise/data/logs/runner.log")
    ]
)
logger = logging.getLogger(__name__)


class VHFRunner:
    """Runner principal du système."""
    
    def __init__(self):
        """Initialise le runner."""
        # Services
        self.tts_engine = PiperEngine()
        self.tts_cache = TTSCacheService()
        self.template_renderer = TemplateRenderer()
        
        # PTT controller (sera initialisé selon config)
        self.ptt_controller = None
        self.transmission_service = None
        
        logger.info("Runner VHF initialisé")
    
    def _init_ptt_controller(self, settings: SystemSettings):
        """Initialise le contrôleur PTT selon la config."""
        if self.ptt_controller:
            return  # Déjà initialisé
        
        if settings.ptt_gpio_pin is not None:
            try:
                # Mode GPIO (Raspberry Pi)
                self.ptt_controller = GPIOPTTController(
                    pin=settings.ptt_gpio_pin,
                    active_level=settings.ptt_active_level
                )
                logger.info(f"PTT GPIO initialisé (pin {settings.ptt_gpio_pin})")
            except ImportError:
                # Fallback sur mock si GPIO non disponible
                logger.warning("GPIO non disponible, utilisation du mode MOCK")
                self.ptt_controller = MockPTTController()
        else:
            # Mode mock (développement)
            self.ptt_controller = MockPTTController()
        
        # Créer le service de transmission
        self.transmission_service = TransmissionService(self.ptt_controller)
    
    async def run(self):
        """Boucle principale du runner."""
        logger.info("Démarrage du runner...")
        
        # Initialiser la DB
        init_db()
        
        # Marquer les anciens PENDING en ABORTED
        self._cleanup_old_pending()
        
        while True:
            try:
                await self._iteration()
            except Exception as e:
                logger.error(f"Erreur dans l'itération du runner: {e}", exc_info=True)
            
            # Attendre avant la prochaine itération
            await asyncio.sleep(10)  # 10 secondes entre chaque itération
    
    def _cleanup_old_pending(self):
        """Marque les anciens PENDING en ABORTED au démarrage."""
        with get_db_session() as db:
            cutoff = datetime.utcnow() - timedelta(seconds=120)
            
            old_pending = db.query(TxHistory).filter(
                TxHistory.status == "PENDING",
                TxHistory.created_at < cutoff
            ).all()
            
            for tx in old_pending:
                tx.status = "ABORTED"
                tx.error_message = "Aborted on runner restart (too old)"
            
            if old_pending:
                db.commit()
                logger.info(f"Marqué {len(old_pending)} anciennes TX PENDING en ABORTED")
    
    async def _iteration(self):
        """Une itération du runner."""
        with get_db_session() as db:
            # Récupérer les settings
            settings = db.query(SystemSettings).filter_by(id=1).first()
            
            if not settings or not settings.master_enabled:
                # Système désactivé
                return
            
            # Initialiser PTT si nécessaire
            self._init_ptt_controller(settings)
            
            # Charger les credentials des providers
            provider_manager.load_credentials(db)
            
            # Récupérer les canaux actifs
            active_channels = db.query(Channel).filter_by(enabled=True).all()
            
            if not active_channels:
                return
            
            # Polling des mesures
            await self._poll_measurements(db, active_channels)
            
            # Planification et exécution des TX
            await self._execute_transmissions(db, active_channels, settings)
    
    async def _poll_measurements(self, db: Session, channels: List[Channel]):
        """
        Poll les mesures pour tous les canaux actifs.
        
        Regroupe par provider pour optimiser les appels API.
        """
        # Regrouper par provider
        channels_by_provider: Dict[str, List[Channel]] = {}
        for channel in channels:
            if channel.provider_id not in channels_by_provider:
                channels_by_provider[channel.provider_id] = []
            channels_by_provider[channel.provider_id].append(channel)
        
        # Fetch par provider
        for provider_id, provider_channels in channels_by_provider.items():
            provider = provider_manager.get_provider(provider_id)
            if not provider:
                logger.warning(f"Provider inconnu: {provider_id}")
                continue
            
            station_ids = [ch.station_id for ch in provider_channels]
            
            try:
                # Fetch bulk
                measurements = await provider.fetch_measurements_bulk(station_ids)
                
                # Mettre à jour les runtimes
                for channel in provider_channels:
                    measurement = measurements.get(channel.station_id)
                    if measurement:
                        self._update_channel_measurement(db, channel, measurement)
                
            except Exception as e:
                logger.error(f"Erreur lors du polling {provider_id}: {e}")
    
    def _update_channel_measurement(self, db: Session, channel: Channel, measurement):
        """Met à jour la mesure d'un canal."""
        # Récupérer ou créer le runtime
        runtime = channel.runtime
        if not runtime:
            runtime = ChannelRuntime(channel_id=channel.id)
            db.add(runtime)
        
        # Vérifier si c'est une nouvelle mesure
        if runtime.last_measurement_at is None or measurement.measurement_at > runtime.last_measurement_at:
            logger.info(f"Nouvelle mesure pour canal {channel.name}: {measurement.measurement_at}")
            
            runtime.last_measurement_at = measurement.measurement_at
            runtime.last_error = None
            
            # Planifier les TX
            self._schedule_transmissions(db, channel, measurement)
        
        db.commit()
    
    def _schedule_transmissions(self, db: Session, channel: Channel, measurement):
        """Planifie les transmissions pour une nouvelle mesure."""
        # Calculer les tx_times
        offsets = channel.offsets_seconds_json or [0]
        
        for offset in offsets:
            planned_at = measurement.measurement_at + timedelta(seconds=offset)
            
            # Ne pas planifier dans le passé
            if planned_at < datetime.utcnow():
                continue
            
            # TODO: Créer les entrées de planification
            # Pour V1, on va juste mettre à jour next_tx_at
            if not channel.runtime.next_tx_at or planned_at < channel.runtime.next_tx_at:
                channel.runtime.next_tx_at = planned_at
        
        db.commit()
        logger.info(f"TX planifiée pour {channel.name} à {channel.runtime.next_tx_at}")
    
    async def _execute_transmissions(self, db: Session, channels: List[Channel], settings: SystemSettings):
        """
        Exécute les transmissions dues.
        
        Gère les collisions (plusieurs TX au même moment).
        """
        now = datetime.utcnow()
        
        # Trouver les canaux avec TX due
        due_channels = []
        for channel in channels:
            if channel.runtime and channel.runtime.next_tx_at:
                if channel.runtime.next_tx_at <= now:
                    due_channels.append(channel)
        
        if not due_channels:
            return
        
        # Mélanger l'ordre (aléatoire)
        random.shuffle(due_channels)
        
        logger.info(f"{len(due_channels)} transmissions dues, ordre: {[ch.name for ch in due_channels]}")
        
        # Exécuter séquentiellement
        for i, channel in enumerate(due_channels):
            try:
                await self._execute_single_transmission(db, channel, settings)
                
                # Pause inter-annonce (sauf pour la dernière)
                if i < len(due_channels) - 1:
                    pause = settings.inter_announcement_pause_seconds
                    logger.info(f"Pause inter-annonce: {pause}s")
                    await asyncio.sleep(pause)
                
            except Exception as e:
                logger.error(f"Erreur lors de la TX du canal {channel.name}: {e}", exc_info=True)
                channel.runtime.last_error = str(e)
                db.commit()
    
    async def _execute_single_transmission(self, db: Session, channel: Channel, settings: SystemSettings):
        """
        Exécute UNE transmission pour un canal.
        
        Suit la procédure fail-safe complète.
        """
        # TODO: Implémenter la procédure complète de TX avec journalisation PENDING
        # Pour l'instant, juste un placeholder
        logger.info(f"Exécution TX pour canal {channel.name}")
        
        # Réinitialiser next_tx_at
        channel.runtime.next_tx_at = None
        channel.runtime.last_tx_at = datetime.utcnow()
        db.commit()


async def main():
    """Point d'entrée principal."""
    runner = VHFRunner()
    
    try:
        await runner.run()
    except KeyboardInterrupt:
        logger.info("Arrêt du runner (Ctrl+C)")
    finally:
        if runner.ptt_controller:
            runner.ptt_controller.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
