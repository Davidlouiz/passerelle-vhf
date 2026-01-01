"""
Runner/Scheduler principal.

Polling des providers, détection de nouvelles mesures, planification et exécution des TX.
"""

import asyncio
import logging
import sys
import os
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

# Fichier PID pour prévenir instances multiples
PID_FILE = DATA_DIR / "runner.pid"

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


def acquire_pid_lock() -> bool:
    """Acquérir le verrou PID.
    
    Returns:
        True si le verrou a été acquis, False sinon.
    """
    if PID_FILE.exists():
        # Lire le PID existant
        try:
            existing_pid = int(PID_FILE.read_text().strip())
            # Vérifier si le processus existe encore
            try:
                os.kill(existing_pid, 0)  # Signal 0 = vérifier existence
                logger.error(
                    f"❌ Un autre runner tourne déjà (PID {existing_pid}). "
                    f"Arrêtez-le avant de démarrer une nouvelle instance."
                )
                return False
            except ProcessLookupError:
                # Le processus n'existe plus, fichier PID obsolète
                logger.warning(
                    f"Fichier PID obsolète détecté (PID {existing_pid} n'existe plus). "
                    "Nettoyage et acquisition du verrou."
                )
                PID_FILE.unlink()
        except (ValueError, OSError) as e:
            logger.warning(f"Fichier PID corrompu : {e}. Recréation.")
            PID_FILE.unlink(missing_ok=True)
    
    # Créer le fichier PID
    try:
        PID_FILE.write_text(str(os.getpid()))
        logger.info(f"✓ Verrou PID acquis : {PID_FILE} (PID {os.getpid()})")
        return True
    except OSError as e:
        logger.error(f"❌ Impossible de créer le fichier PID : {e}")
        return False


def release_pid_lock():
    """Libérer le verrou PID."""
    try:
        if PID_FILE.exists():
            current_pid = int(PID_FILE.read_text().strip())
            if current_pid == os.getpid():
                PID_FILE.unlink()
                logger.info("✓ Verrou PID libéré")
            else:
                logger.warning(
                    f"Le fichier PID appartient à un autre processus ({current_pid}), "
                    "pas de suppression."
                )
    except Exception as e:
        logger.error(f"Erreur lors de la libération du verrou PID : {e}")


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
        """Marque les anciennes TX PENDING en ABORTED au démarrage.

        Annule uniquement les TX dont planned_at est dans le passé de plus de 1h.
        Les TX récemment passées (< 1h) restent PENDING et seront exécutées.
        """
        with get_db_session() as db:
            cutoff = datetime.utcnow() - timedelta(seconds=3600)  # 1 heure

            old_pending = (
                db.query(TxHistory)
                .filter(TxHistory.status == "PENDING", TxHistory.planned_at < cutoff)
                .all()
            )

            for tx in old_pending:
                tx.status = "ABORTED"
                tx.error_message = "Aborted on runner restart (planned_at > 1h ago)"

            if old_pending:
                db.commit()
                logger.info(
                    f"Marqué {len(old_pending)} TX PENDING obsolètes en ABORTED"
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
        # IMPORTANT: SQLite ne supporte pas les timezones, donc on stocke en UTC naïf
        # et on compare avec des UTC naïfs également
        measurement_utc_naive = (
            measurement.measurement_at.replace(tzinfo=None)
            if measurement.measurement_at.tzinfo
            else measurement.measurement_at
        )
        last_measurement_utc_naive = runtime.last_measurement_at

        if (
            last_measurement_utc_naive is None
            or measurement_utc_naive > last_measurement_utc_naive
        ):
            logger.info(
                f"Nouvelle mesure pour canal {channel.name}: {measurement_utc_naive} UTC"
            )

            runtime.last_measurement_at = measurement_utc_naive
            runtime.last_error = None

            # Planifier les TX
            self._schedule_transmissions(db, channel, measurement)

        db.commit()

    def _schedule_transmissions(self, db: Session, channel: Channel, measurement):
        """
        Planifie les transmissions pour une nouvelle mesure.

        Politique V1 (cancel_on_new) : annule les futures TX non-exécutées
        et crée TOUTES les nouvelles TX dans tx_history.
        """
        # POLITIQUE V1 : Annuler TOUTES les TX PENDING de ce canal (futures et passées)
        pending_tx = (
            db.query(TxHistory)
            .filter(
                TxHistory.channel_id == channel.id,
                TxHistory.status == "PENDING",
            )
            .all()
        )

        if pending_tx:
            for tx in pending_tx:
                tx.status = "ABORTED"
                tx.error_message = "Cancelled by new measurement (cancel_on_new policy)"
            logger.info(
                f"Annulé {len(pending_tx)} TX PENDING pour {channel.name} (nouvelle mesure)"
            )

        # Calculer TOUTES les TX depuis les offsets et les créer dans tx_history
        import json
        from app.utils import compute_hash

        offsets = json.loads(channel.offsets_seconds_json or "[0]")
        created_count = 0

        # Utiliser le même UTC naïf que celui stocké dans runtime
        measurement_utc_naive = (
            measurement.measurement_at.replace(tzinfo=None)
            if measurement.measurement_at.tzinfo
            else measurement.measurement_at
        )

        for offset in offsets:
            planned_at = measurement_utc_naive + timedelta(seconds=offset)

            # Rendre le texte pour calculer tx_id (fonction centralisée)
            from app.services.announcement import prepare_announcement_text

            rendered_text = prepare_announcement_text(channel, measurement)

            # Calculer tx_id (idempotence)
            tx_id = compute_hash(
                channel.id,
                channel.provider_id,
                channel.station_id,
                measurement_utc_naive.isoformat(),
                rendered_text,
                channel.engine_id,
                channel.voice_id,
                channel.voice_params_json or "{}",
                offset,
            )

            # Vérifier si cette TX existe déjà (idempotence)
            existing = db.query(TxHistory).filter_by(tx_id=tx_id).first()
            if existing:
                logger.debug(f"TX {tx_id[:12]}... existe déjà, skip")
                continue

            # Créer la TX avec status="PENDING"
            tx_record = TxHistory(
                tx_id=tx_id,
                channel_id=channel.id,
                mode="SCHEDULED",
                status="PENDING",
                station_id=str(channel.station_id),
                measurement_at=measurement_utc_naive,
                offset_seconds=offset,
                planned_at=planned_at,
                rendered_text=rendered_text,
            )
            db.add(tx_record)
            created_count += 1
            logger.debug(f"Créé TX offset {offset}s pour {channel.name} à {planned_at}")

        # Commit pour persister les TX
        db.commit()

        logger.info(f"Créé {created_count} TX PENDING pour {channel.name}")

        # Calculer next_tx_at : la plus proche TX PENDING
        next_pending = (
            db.query(TxHistory)
            .filter(
                TxHistory.channel_id == channel.id,
                TxHistory.status == "PENDING",
            )
            .order_by(TxHistory.planned_at)
            .first()
        )

        if next_pending:
            channel.runtime.next_tx_at = next_pending.planned_at
            logger.info(f"Prochaine TX pour {channel.name} : {next_pending.planned_at}")
        else:
            channel.runtime.next_tx_at = None
            logger.warning(f"Aucune TX PENDING pour {channel.name}")

        db.commit()

    async def _execute_transmissions(
        self, db: Session, channels: List[Channel], settings: SystemSettings
    ):
        """
        Exécute TOUTES les transmissions PENDING dont planned_at <= now.

        Une par une, en marquant chaque TX avant de l'exécuter.
        """
        now = datetime.utcnow()

        # Trouver TOUTES les TX PENDING dues (planned_at <= now)
        due_tx = (
            db.query(TxHistory)
            .filter(
                TxHistory.status == "PENDING",
                TxHistory.planned_at <= now,
            )
            .order_by(TxHistory.planned_at)  # Ordre chronologique
            .all()
        )

        if not due_tx:
            return

        logger.info(f"{len(due_tx)} TX PENDING à exécuter")

        # Exécuter séquentiellement
        for i, tx_record in enumerate(due_tx):
            try:
                # Récupérer le canal
                channel = db.query(Channel).filter_by(id=tx_record.channel_id).first()
                if not channel:
                    logger.error(f"Canal {tx_record.channel_id} introuvable")
                    tx_record.status = "FAILED"
                    tx_record.error_message = "Channel not found"
                    db.commit()
                    continue

                await self._execute_single_transmission(
                    db, channel, settings, tx_record
                )

                # Pause inter-annonce (sauf pour la dernière)
                if i < len(due_tx) - 1:
                    pause = settings.inter_announcement_pause_seconds
                    logger.info(f"Pause inter-annonce: {pause}s")
                    await asyncio.sleep(pause)

            except Exception as e:
                logger.error(
                    f"Erreur lors de la TX {tx_record.tx_id[:12]}...: {e}",
                    exc_info=True,
                )
                tx_record.status = "FAILED"
                tx_record.error_message = str(e)
                if channel:
                    channel.runtime.last_error = str(e)
                db.commit()

        # Recalculer next_tx_at pour tous les canaux affectés
        affected_channels = set(tx.channel_id for tx in due_tx)
        for channel_id in affected_channels:
            channel = db.query(Channel).filter_by(id=channel_id).first()
            if channel and channel.runtime:
                next_pending = (
                    db.query(TxHistory)
                    .filter(
                        TxHistory.channel_id == channel_id,
                        TxHistory.status == "PENDING",
                    )
                    .order_by(TxHistory.planned_at)
                    .first()
                )
                channel.runtime.next_tx_at = (
                    next_pending.planned_at if next_pending else None
                )
                logger.debug(
                    f"next_tx_at mis à jour pour {channel.name}: {channel.runtime.next_tx_at}"
                )

        db.commit()

    async def _execute_single_transmission(
        self,
        db: Session,
        channel: Channel,
        settings: SystemSettings,
        tx_record: TxHistory,
    ):
        """
        Exécute UNE transmission pour un canal.

        La TX est DÉJÀ créée dans tx_history avec status="PENDING".

        Procédure :
        1. Vérifier mesure non périmée
        2. Obtenir/synthétiser l'audio (cache)
        3. Re-vérifier non périmée JUSTE AVANT TX
        4. Acquérir verrou TX + PTT ON → audio → PTT OFF
        5. Marquer status="SENT" ou "FAILED"
        """
        try:
            # ÉTAPE 1 : Récupérer la mesure et vérifier non périmée
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

            # ÉTAPE 2 : Obtenir/synthétiser l'audio (cache-first)
            import json

            voice_params = json.loads(channel.voice_params_json or "{}")

            # Si audio_path déjà dans tx_record, l'utiliser
            if tx_record.audio_path and Path(tx_record.audio_path).exists():
                audio_path = tx_record.audio_path
            else:
                # Synthétiser avec Piper
                from app.database import DATA_DIR

                audio_path = str(
                    DATA_DIR / "audio_cache" / f"tx_{tx_record.tx_id[:12]}.wav"
                )
                Path(audio_path).parent.mkdir(parents=True, exist_ok=True)

                if self.tts_engine:
                    # Utiliser Piper pour synthétiser
                    logger.info(f"Synthèse TTS : '{tx_record.rendered_text[:50]}...'")

                    # Piper synthesize est synchrone, on l'exécute dans un thread
                    audio_path = await asyncio.to_thread(
                        self.tts_engine.synthesize,
                        tx_record.rendered_text,  # text
                        channel.voice_id,  # voice_id
                        audio_path,  # output_path
                        voice_params,  # params
                    )

                    logger.info(f"Audio synthétisé : {audio_path}")
                else:
                    # Fallback : WAV mock si TTS indisponible
                    logger.warning("TTS indisponible, création audio mock")
                    import wave

                    with wave.open(audio_path, "wb") as wav:
                        wav.setnchannels(1)
                        wav.setsampwidth(2)
                        wav.setframerate(16000)
                        wav.writeframes(b"\x00" * 32000)

                if not audio_path or not Path(audio_path).exists():
                    raise Exception("Fichier audio manquant")

                # Sauvegarder audio_path dans tx_record
                tx_record.audio_path = audio_path
                db.commit()

            logger.info(
                f"TX {tx_record.tx_id[:12]}... pour {channel.name}, audio: {audio_path}"
            )

            # ÉTAPE 3 : Re-vérifier non périmée JUSTE AVANT TX
            if is_measurement_expired(
                measurement.measurement_at, channel.measurement_period_seconds
            ):
                raise MeasurementExpiredError("Mesure périmée juste avant transmission")

            # ÉTAPE 3.5 : Marquer comme SENT AVANT transmission (évite race condition)
            # Si la TX échoue, on la marquera FAILED dans le except
            tx_record.status = "SENT"
            tx_record.sent_at = datetime.utcnow()
            channel.runtime.last_tx_at = datetime.utcnow()
            db.commit()

            # ÉTAPE 4 : Transmission PTT
            logger.info(f"Début transmission pour {channel.name}")
            await self.transmission_service.transmit(
                audio_path=audio_path,
                lead_ms=settings.ptt_lead_ms,
                tail_ms=settings.ptt_tail_ms,
                timeout_seconds=settings.tx_timeout_seconds,
            )

            logger.info(
                f"✅ TX {tx_record.tx_id[:12]}... envoyée avec succès pour {channel.name}"
            )

        except MeasurementExpiredError as e:
            # Mesure périmée : annuler la TX
            logger.warning(f"TX annulée pour {channel.name} : {e}")
            tx_record.status = "ABORTED"
            tx_record.error_message = str(e)
            db.commit()

        except Exception as e:
            # Toute autre erreur : marquer FAILED
            # Note: Si on avait déjà marqué SENT avant transmission, on repasse en FAILED
            logger.error(f"❌ Erreur TX pour {channel.name}: {e}", exc_info=True)
            tx_record.status = "FAILED"
            tx_record.error_message = str(e)
            channel.runtime.last_error = str(e)
            db.commit()


async def main():
    """Point d'entrée principal."""
    # Acquérir le verrou PID avant toute chose
    if not acquire_pid_lock():
        logger.error("Impossible de démarrer : un autre runner est déjà actif.")
        sys.exit(1)
    
    runner = VHFRunner()

    try:
        await runner.run()
    except KeyboardInterrupt:
        logger.info("Arrêt du runner (Ctrl+C)")
    finally:
        if runner.ptt_controller:
            runner.ptt_controller.cleanup()
        release_pid_lock()


if __name__ == "__main__":
    asyncio.run(main())
