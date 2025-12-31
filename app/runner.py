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
from app.database import DATA_DIR

# Créer le dossier de logs
LOG_DIR = DATA_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_DIR / "runner.log"),
    ],
)
logger = logging.getLogger(__name__)


class VHFRunner:
    """Runner principal du système."""

    def __init__(self):
        """Initialise le runner."""
        # Services
        try:
            self.tts_engine = PiperEngine()
        except Exception as e:
            logger.warning(f"TTS Piper non disponible : {e}")
            self.tts_engine = None

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
                    pin=settings.ptt_gpio_pin, active_level=settings.ptt_active_level
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

        # Timestamp du dernier poll (initialisé dans le passé pour forcer le 1er poll)
        last_poll_time = datetime.utcnow() - timedelta(seconds=3600)

        while True:
            try:
                with get_db_session() as db:
                    # Récupérer les settings pour poll_interval
                    settings = db.query(SystemSettings).filter_by(id=1).first()

                    if settings and settings.master_enabled:
                        # Vérifier s'il est temps de faire un poll
                        elapsed = (datetime.utcnow() - last_poll_time).total_seconds()

                        if elapsed >= settings.poll_interval_seconds:
                            await self._iteration()
                            last_poll_time = datetime.utcnow()
                    else:
                        # Système désactivé, on attend quand même
                        pass

            except Exception as e:
                logger.error(f"Erreur dans l'itération du runner: {e}", exc_info=True)

            # Attendre 1 seconde avant de revérifier (plus réactif)
            await asyncio.sleep(1)

    def _cleanup_old_pending(self):
        """Marque les anciens PENDING en ABORTED au démarrage."""
        with get_db_session() as db:
            cutoff = datetime.utcnow() - timedelta(seconds=120)

            old_pending = (
                db.query(TxHistory)
                .filter(TxHistory.status == "PENDING", TxHistory.created_at < cutoff)
                .all()
            )

            for tx in old_pending:
                tx.status = "ABORTED"
                tx.error_message = "Aborted on runner restart (too old)"

            if old_pending:
                db.commit()
                logger.info(
                    f"Marqué {len(old_pending)} anciennes TX PENDING en ABORTED"
                )

    async def _iteration(self):
        """Une itération du runner."""
        logger.info("=== Début itération Runner ===")

        with get_db_session() as db:
            # Récupérer les settings
            settings = db.query(SystemSettings).filter_by(id=1).first()

            if not settings or not settings.master_enabled:
                # Système désactivé
                logger.debug("Système désactivé, skip itération")
                return

            # Initialiser PTT si nécessaire
            self._init_ptt_controller(settings)

            # Charger les credentials des providers
            provider_manager.load_credentials(db)
            logger.info("Credentials providers chargés")

            # Récupérer les canaux actifs
            active_channels = db.query(Channel).filter_by(is_enabled=True).all()

            if not active_channels:
                logger.info("Aucun canal actif")
                return

            logger.info(
                f"{len(active_channels)} canaux actifs : {[ch.name for ch in active_channels]}"
            )

            # Polling des mesures
            await self._poll_measurements(db, active_channels)

            # Planification et exécution des TX
            await self._execute_transmissions(db, active_channels, settings)

        logger.info("=== Fin itération Runner ===")

    async def _poll_measurements(self, db: Session, channels: List[Channel]):
        """
        Poll les mesures pour tous les canaux actifs.

        Regroupe par provider pour optimiser les appels API.
        """
        logger.info("--- Début polling mesures ---")

        # Regrouper par provider
        channels_by_provider: Dict[str, List[Channel]] = {}
        for channel in channels:
            if channel.provider_id not in channels_by_provider:
                channels_by_provider[channel.provider_id] = []
            channels_by_provider[channel.provider_id].append(channel)

        logger.info(f"Providers à interroger : {list(channels_by_provider.keys())}")

        # Fetch par provider
        for provider_id, provider_channels in channels_by_provider.items():
            provider = provider_manager.get_provider(provider_id)
            if not provider:
                logger.warning(f"Provider inconnu: {provider_id}")
                continue

            station_ids = [str(ch.station_id) for ch in provider_channels]
            logger.info(f"Fetching {provider_id} pour stations : {station_ids}")

            try:
                # Fetch bulk
                measurements = await provider.fetch_measurements_bulk(station_ids)
                logger.info(f"Reçu {len(measurements)} mesures de {provider_id}")

                # Mettre à jour les runtimes
                for channel in provider_channels:
                    measurement = measurements.get(str(channel.station_id))
                    if measurement:
                        self._update_channel_measurement(db, channel, measurement)
                    else:
                        logger.warning(
                            f"Pas de mesure pour station {channel.station_id}"
                        )

            except Exception as e:
                logger.error(
                    f"Erreur lors du polling {provider_id}: {e}", exc_info=True
                )

    def _update_channel_measurement(self, db: Session, channel: Channel, measurement):
        """Met à jour la mesure d'un canal."""
        # Récupérer ou créer le runtime
        runtime = channel.runtime
        if not runtime:
            runtime = ChannelRuntime(channel_id=channel.id)
            db.add(runtime)

        # Vérifier si c'est une nouvelle mesure
        if (
            runtime.last_measurement_at is None
            or measurement.measurement_at > runtime.last_measurement_at
        ):
            logger.info(
                f"Nouvelle mesure pour canal {channel.name}: {measurement.measurement_at}"
            )

            runtime.last_measurement_at = measurement.measurement_at
            runtime.last_error = None

            # Planifier les TX
            self._schedule_transmissions(db, channel, measurement)

        db.commit()

    def _schedule_transmissions(self, db: Session, channel: Channel, measurement):
        """
        Planifie les transmissions pour une nouvelle mesure.

        Politique V1 (cancel_on_new) : annule les futures TX non-exécutées.
        """
        # POLITIQUE V1 : Annuler les futures TX PENDING de ce canal
        future_pending = (
            db.query(TxHistory)
            .filter(
                TxHistory.channel_id == channel.id,
                TxHistory.status == "PENDING",
                TxHistory.planned_at > datetime.utcnow(),
            )
            .all()
        )

        if future_pending:
            for tx in future_pending:
                tx.status = "ABORTED"
                tx.error_message = "Cancelled by new measurement (cancel_on_new policy)"
            db.commit()
            logger.info(
                f"Annulé {len(future_pending)} TX futures pour {channel.name} (nouvelle mesure)"
            )

        # Calculer les tx_times depuis les offsets
        import json

        offsets = json.loads(channel.offsets_seconds_json or "[0]")

        # Trouver la prochaine TX valide (pas dans le passé)
        next_valid_tx = None

        for offset in offsets:
            planned_at = measurement.measurement_at + timedelta(seconds=offset)

            # Ne pas planifier dans le passé
            if planned_at < datetime.utcnow():
                logger.debug(
                    f"Skip TX planifiée dans le passé : {planned_at} (offset {offset}s)"
                )
                continue

            # Garder la plus proche TX valide
            if next_valid_tx is None or planned_at < next_valid_tx:
                next_valid_tx = planned_at

        # Mettre à jour next_tx_at seulement si on a une TX valide
        if next_valid_tx:
            channel.runtime.next_tx_at = next_valid_tx
            logger.info(f"TX planifiée pour {channel.name} à {next_valid_tx}")
        else:
            # Toutes les TX sont dans le passé, réinitialiser
            channel.runtime.next_tx_at = None
            logger.warning(
                f"Aucune TX valide pour {channel.name} (toutes dans le passé)"
            )

        db.commit()

    async def _execute_transmissions(
        self, db: Session, channels: List[Channel], settings: SystemSettings
    ):
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

        logger.info(
            f"{len(due_channels)} transmissions dues, ordre: {[ch.name for ch in due_channels]}"
        )

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
                logger.error(
                    f"Erreur lors de la TX du canal {channel.name}: {e}", exc_info=True
                )
                channel.runtime.last_error = str(e)
                db.commit()

    async def _execute_single_transmission(
        self, db: Session, channel: Channel, settings: SystemSettings
    ):
        """
        Exécute UNE transmission pour un canal.

        Suit la procédure fail-safe complète :
        1. Récupérer la mesure + vérifier non périmée
        2. Rendre le texte depuis le template
        3. Obtenir/synthétiser l'audio (utiliser le cache)
        4. Calculer tx_id
        5. INSERT tx_history avec status="PENDING" puis COMMIT
        6. Re-vérifier non périmée immédiatement avant TX
        7. Acquérir le verrou TX global
        8. PTT ON → délai lead → jouer audio → délai tail → PTT OFF
        9. UPDATE status="SENT"|"FAILED" + COMMIT
        """
        tx_record = None

        try:
            # ANTI-SPAM : Vérifier min_interval_between_tx
            if channel.runtime.last_tx_at:
                elapsed = (
                    datetime.utcnow() - channel.runtime.last_tx_at
                ).total_seconds()
                if elapsed < channel.min_interval_between_tx_seconds:
                    logger.info(
                        f"TX skipped pour {channel.name} : intervalle insuffisant "
                        f"({elapsed:.0f}s < {channel.min_interval_between_tx_seconds}s)"
                    )
                    channel.runtime.next_tx_at = None
                    db.commit()
                    return

            # ÉTAPE 1 : Récupérer la mesure
            provider = provider_manager.get_provider(channel.provider_id)
            if not provider:
                raise Exception(f"Provider {channel.provider_id} non disponible")

            measurement = await provider.fetch_measurement(channel.station_id)
            if not measurement:
                raise Exception("Mesure non disponible")

            # Vérifier non périmée
            if is_measurement_expired(
                measurement.measurement_at, channel.measurement_period_seconds
            ):
                raise MeasurementExpiredError(
                    f"Mesure périmée : {measurement.measurement_at}"
                )

            # ÉTAPE 2 : Rendre le template
            rendered_text = self.template_renderer.render(
                template=channel.template_text,
                station_name=channel.name,  # Utilise le nom du canal
                wind_avg_kmh=measurement.wind_avg_kmh,
                wind_max_kmh=measurement.wind_max_kmh,
                wind_min_kmh=measurement.wind_min_kmh,
                wind_direction_deg=measurement.wind_direction,  # Corrigé: utilise wind_direction (degrés)
                measurement_at=measurement.measurement_at,
            )

            # ÉTAPE 3 : Obtenir/synthétiser l'audio (cache-first)
            import json

            voice_params = json.loads(channel.voice_params_json or "{}")

            # Mode mock TTS si Piper non disponible
            if self.tts_engine is None:
                logger.warning("TTS non disponible, création d'un fichier audio mock")
                # Créer un fichier WAV factice
                from app.database import DATA_DIR

                audio_path = str(
                    DATA_DIR
                    / "audio_cache"
                    / f"mock_{channel.id}_{hash(rendered_text) % 10000}.wav"
                )
                Path(audio_path).parent.mkdir(parents=True, exist_ok=True)

                # WAV minimal (silence de 1 seconde)
                import wave

                with wave.open(audio_path, "wb") as wav:
                    wav.setnchannels(1)
                    wav.setsampwidth(2)
                    wav.setframerate(16000)
                    wav.writeframes(b"\x00" * 32000)  # 1 sec de silence
            else:
                audio_path = await self.tts_cache.get_or_synthesize(
                    engine=self.tts_engine,
                    engine_id=channel.engine_id,
                    voice_id=channel.voice_id,
                    voice_params=voice_params,
                    text=rendered_text,
                    locale="fr_FR",
                )

            if not audio_path or not Path(audio_path).exists():
                raise Exception("Fichier audio manquant")

            # ÉTAPE 4 : Calculer tx_id
            from app.utils import compute_tx_id

            tx_id = compute_tx_id(
                channel_id=channel.id,
                provider_id=channel.provider_id,
                station_id=channel.station_id,
                measurement_at=measurement.measurement_at,
                rendered_text=rendered_text,
                engine_id=channel.engine_id,
                voice_id=channel.voice_id,
                voice_params=voice_params,
                offset_seconds=0,  # TODO: récupérer l'offset réel
            )

            # ÉTAPE 5 : Journaliser PENDING (CRITIQUE)
            tx_record = TxHistory(
                tx_id=tx_id,
                channel_id=channel.id,
                mode="SCHEDULED",
                status="PENDING",
                station_id=str(channel.station_id),
                measurement_at=measurement.measurement_at,
                offset_seconds=0,
                planned_at=datetime.utcnow(),
                rendered_text=rendered_text,
                audio_path=audio_path,
            )
            db.add(tx_record)
            db.commit()  # COMMIT CRITIQUE : si ça échoue, pas de TX

            logger.info(f"TX {tx_id[:8]}... journalisée PENDING pour {channel.name}")

            # ÉTAPE 6 : Re-vérifier non périmée JUSTE AVANT TX
            if is_measurement_expired(
                measurement.measurement_at, channel.measurement_period_seconds
            ):
                raise MeasurementExpiredError("Mesure périmée juste avant transmission")

            # ÉTAPES 7-8 : Transmission PTT
            logger.info(f"Début transmission pour {channel.name}")
            await self.transmission_service.transmit(
                audio_path=audio_path,
                lead_ms=channel.lead_ms,
                tail_ms=channel.tail_ms,
                timeout_seconds=settings.tx_timeout_seconds,
            )

            # ÉTAPE 9 : Marquer SENT
            tx_record.status = "SENT"
            tx_record.sent_at = datetime.utcnow()
            channel.runtime.last_tx_at = datetime.utcnow()

            # Calculer le prochain offset pour la même mesure
            offsets = json.loads(channel.offsets_seconds_json or "[0]")
            next_offset_tx = None

            for offset in offsets:
                planned_at = measurement.measurement_at + timedelta(seconds=offset)
                # Chercher le prochain offset après maintenant
                if planned_at > datetime.utcnow():
                    if next_offset_tx is None or planned_at < next_offset_tx:
                        next_offset_tx = planned_at

            if next_offset_tx:
                channel.runtime.next_tx_at = next_offset_tx
                logger.info(
                    f"Prochain offset planifié pour {channel.name} à {next_offset_tx}"
                )
            else:
                channel.runtime.next_tx_at = None  # Tous les offsets ont été émis
                logger.info(f"Tous les offsets émis pour {channel.name}")

            db.commit()

            logger.info(f"✅ TX {tx_id[:8]}... envoyée avec succès pour {channel.name}")

        except MeasurementExpiredError as e:
            # Mesure périmée : fail silently (fail-closed)
            logger.warning(f"TX annulée pour {channel.name} : {e}")
            if tx_record:
                tx_record.status = "ABORTED"
                tx_record.error_message = str(e)
                db.commit()
            channel.runtime.next_tx_at = None
            db.commit()

        except Exception as e:
            # Toute autre erreur : fail silently
            logger.error(f"❌ Erreur TX pour {channel.name}: {e}", exc_info=True)
            if tx_record:
                tx_record.status = "FAILED"
                tx_record.error_message = str(e)
                db.commit()
            channel.runtime.last_error = str(e)
            channel.runtime.next_tx_at = None
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
