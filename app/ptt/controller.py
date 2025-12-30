"""
Contrôleur PTT (Push-To-Talk).

Gère le contrôle du PTT via GPIO (Raspberry Pi) ou mode mock (développement).
"""

from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class PTTController(ABC):
    """Interface abstraite pour le contrôle PTT."""

    @abstractmethod
    def set_ptt(self, active: bool):
        """
        Active ou désactive le PTT.

        Args:
            active: True pour PTT ON, False pour PTT OFF
        """
        pass

    @abstractmethod
    def cleanup(self):
        """Nettoie les ressources (appelé à la fermeture)."""
        pass


class MockPTTController(PTTController):
    """Contrôleur PTT simulé pour développement/tests."""

    def __init__(self):
        self._state = False
        logger.info("Contrôleur PTT en mode MOCK initialisé")

    def set_ptt(self, active: bool):
        """Simule l'activation du PTT."""
        self._state = active
        logger.info(f"[MOCK PTT] {'ON' if active else 'OFF'}")

    def cleanup(self):
        """Rien à nettoyer en mode mock."""
        pass


class GPIOPTTController(PTTController):
    """Contrôleur PTT via GPIO Raspberry Pi."""

    def __init__(self, pin: int, active_level: int = 1):
        """
        Initialise le contrôle GPIO.

        Args:
            pin: Numéro de pin GPIO (BCM)
            active_level: Niveau actif (1=HIGH, 0=LOW)
        """
        try:
            import RPi.GPIO as GPIO

            self.GPIO = GPIO
        except ImportError:
            raise ImportError(
                "RPi.GPIO non disponible. "
                "Installez-le avec: pip install RPi.GPIO "
                "ou utilisez MockPTTController pour le développement."
            )

        self.pin = pin
        self.active_level = active_level
        self.inactive_level = 1 - active_level

        # Configurer GPIO
        self.GPIO.setmode(self.GPIO.BCM)
        self.GPIO.setup(self.pin, self.GPIO.OUT, initial=self.inactive_level)

        logger.info(
            f"Contrôleur PTT GPIO initialisé (pin={pin}, active_level={active_level})"
        )

    def set_ptt(self, active: bool):
        """Active ou désactive le PTT via GPIO."""
        level = self.active_level if active else self.inactive_level
        self.GPIO.output(self.pin, level)
        logger.debug(
            f"GPIO pin {self.pin} -> {'HIGH' if level else 'LOW'} (PTT {'ON' if active else 'OFF'})"
        )

    def cleanup(self):
        """Nettoie les GPIO."""
        try:
            # S'assurer que PTT est OFF
            self.set_ptt(False)
            self.GPIO.cleanup(self.pin)
            logger.info("GPIO nettoyé")
        except Exception as e:
            logger.error(f"Erreur lors du nettoyage GPIO: {e}")
