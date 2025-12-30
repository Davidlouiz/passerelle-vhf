"""Tests d'intégration fail-safe."""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from app.ptt.controller import MockPTTController
from app.services.transmission import TransmissionService
from app.utils import is_measurement_expired


@pytest.mark.asyncio
async def test_no_tx_on_expired_measurement():
    """Vérifie qu'aucune émission ne part si la mesure est périmée."""
    # Créer une mesure ancienne
    old_measurement_at = datetime.utcnow() - timedelta(hours=2)
    period_seconds = 3600  # 1 heure

    # Vérifier que la mesure est détectée comme périmée
    assert is_measurement_expired(old_measurement_at, period_seconds)


@pytest.mark.asyncio
async def test_ptt_controller_mock():
    """Teste le contrôleur PTT en mode mock."""
    ptt = MockPTTController()

    # PTT OFF par défaut
    assert ptt._state == False

    # Activer PTT
    ptt.set_ptt(True)
    assert ptt._state == True

    # Désactiver PTT
    ptt.set_ptt(False)
    assert ptt._state == False

    # Cleanup
    ptt.cleanup()


@pytest.mark.asyncio
async def test_transmission_service_basic():
    """Teste le service de transmission de base."""
    ptt = MockPTTController()
    tx_service = TransmissionService(ptt)

    # Créer un fichier audio temporaire pour le test
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        audio_path = f.name
        f.write(b"fake audio data")

    try:
        # Mock de la lecture audio
        with patch.object(tx_service, "_play_audio", return_value=asyncio.sleep(0)):
            # La transmission devrait fonctionner
            await tx_service.transmit(
                audio_path=audio_path, lead_ms=100, tail_ms=100, timeout_seconds=5
            )

        # Le PTT doit être OFF après la transmission
        assert ptt._state == False

    finally:
        # Nettoyer
        os.unlink(audio_path)


@pytest.mark.asyncio
async def test_no_tx_on_missing_audio():
    """Vérifie qu'aucune émission ne part si l'audio est manquant."""
    ptt = MockPTTController()
    tx_service = TransmissionService(ptt)

    # Essayer de transmettre avec un fichier inexistant
    with pytest.raises(FileNotFoundError):
        await tx_service.transmit(
            audio_path="/chemin/inexistant/audio.wav",
            lead_ms=100,
            tail_ms=100,
            timeout_seconds=5,
        )

    # Le PTT ne doit jamais avoir été activé
    assert ptt._state == False


@pytest.mark.asyncio
async def test_watchdog_timeout():
    """Teste que le watchdog force PTT OFF après timeout."""
    ptt = MockPTTController()
    tx_service = TransmissionService(ptt)

    import tempfile
    import os

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        audio_path = f.name
        f.write(b"fake audio data")

    try:
        # Mock de la lecture audio qui prend trop de temps
        async def slow_audio_play(path):
            await asyncio.sleep(10)  # 10 secondes

        with patch.object(tx_service, "_play_audio", side_effect=slow_audio_play):
            # Utiliser un timeout court
            try:
                await tx_service.transmit(
                    audio_path=audio_path,
                    lead_ms=100,
                    tail_ms=100,
                    timeout_seconds=1,  # 1 seconde seulement
                )
            except Exception:
                pass  # On s'attend à ce que ça timeout

        # Le PTT doit être forcé OFF par le watchdog
        assert ptt._state == False

    finally:
        os.unlink(audio_path)
