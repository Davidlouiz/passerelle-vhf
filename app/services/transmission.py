"""
Service de transmission (PTT + audio).

Gère la séquence complète de transmission radio.
"""

import asyncio
import threading
from pathlib import Path
from typing import Optional
from datetime import datetime
import logging

from app.exceptions import PTTError
from app.ptt.controller import PTTController

logger = logging.getLogger(__name__)


class TransmissionService:
    """Service de transmission radio."""

    def __init__(self, ptt_controller: PTTController):
        """
        Initialise le service de transmission.

        Args:
            ptt_controller: Contrôleur PTT
        """
        self.ptt = ptt_controller
        self._tx_lock = threading.Lock()  # Verrou global TX

    async def transmit(
        self,
        audio_path: str,
        lead_ms: int = 500,
        tail_ms: int = 500,
        timeout_seconds: int = 30,
    ):
        """
        Effectue une transmission complète (PTT + audio).

        Séquence:
        1. Acquérir verrou TX global
        2. PTT ON
        3. Attendre lead_ms
        4. Jouer audio
        5. Attendre tail_ms
        6. PTT OFF
        7. Libérer verrou

        Le watchdog garantit PTT OFF après timeout_seconds max.

        Args:
            audio_path: Chemin du fichier audio à jouer
            lead_ms: Délai avant audio (ms)
            tail_ms: Délai après audio (ms)
            timeout_seconds: Timeout max pour toute la TX

        Raises:
            PTTError en cas d'erreur PTT
            FileNotFoundError si audio absent
            TimeoutError si timeout dépassé
        """
        # Vérifier que le fichier audio existe
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Fichier audio introuvable: {audio_path}")

        # Acquérir le verrou TX global (bloquant)
        logger.info(f"Acquisition du verrou TX pour {audio_path}")
        acquired = self._tx_lock.acquire(timeout=timeout_seconds)

        if not acquired:
            raise PTTError(
                f"Impossible d'acquérir le verrou TX (timeout {timeout_seconds}s)"
            )

        try:
            logger.info(f"Début transmission: {audio_path}")
            start_time = datetime.utcnow()

            # Démarrer le watchdog
            watchdog_task = asyncio.create_task(
                self._watchdog(timeout_seconds, start_time)
            )

            try:
                # 1. PTT ON
                self.ptt.set_ptt(True)
                logger.debug(f"PTT ON")

                # 2. Lead delay
                await asyncio.sleep(lead_ms / 1000.0)

                # 3. Jouer l'audio
                logger.debug(f"Lecture audio: {audio_path}")
                await self._play_audio(audio_path)

                # 4. Tail delay
                await asyncio.sleep(tail_ms / 1000.0)

            finally:
                # 5. PTT OFF (toujours exécuté)
                self.ptt.set_ptt(False)
                logger.debug(f"PTT OFF")

                # Annuler le watchdog
                watchdog_task.cancel()
                try:
                    await watchdog_task
                except asyncio.CancelledError:
                    pass

            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info(f"Transmission terminée en {duration:.2f}s")

        finally:
            # Libérer le verrou TX
            self._tx_lock.release()
            logger.debug("Verrou TX libéré")

    async def _watchdog(self, timeout_seconds: int, start_time: datetime):
        """
        Watchdog qui force PTT OFF après timeout.

        Args:
            timeout_seconds: Timeout en secondes
            start_time: Heure de début de TX
        """
        await asyncio.sleep(timeout_seconds)

        # Si on arrive ici, c'est que le timeout a été atteint
        logger.error(
            f"WATCHDOG: Timeout de {timeout_seconds}s atteint, forçage PTT OFF"
        )
        try:
            self.ptt.set_ptt(False)
        except Exception as e:
            logger.critical(f"WATCHDOG: Impossible de forcer PTT OFF: {e}")

    async def _play_audio(self, audio_path: str):
        """
        Joue un fichier audio.

        Utilise aplay (ALSA) ou paplay (PulseAudio) selon disponibilité.

        Args:
            audio_path: Chemin du fichier audio
        """
        # Détecter quel outil utiliser
        # TODO: permettre sélection du device audio via config

        # Essayer aplay (ALSA) en premier
        proc = await asyncio.create_subprocess_exec(
            "aplay",
            audio_path,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.PIPE,
        )

        _, stderr = await proc.wait()

        if proc.returncode != 0:
            # Si aplay échoue, essayer paplay (PulseAudio)
            logger.warning(f"aplay échoué, tentative avec paplay")

            proc = await asyncio.create_subprocess_exec(
                "paplay",
                audio_path,
                stdout=asyncio.subprocess.DEVNULL,
                stderr=asyncio.subprocess.PIPE,
            )

            _, stderr = await proc.wait()

            if proc.returncode != 0:
                raise PTTError(f"Impossible de jouer l'audio: {stderr.decode()}")
