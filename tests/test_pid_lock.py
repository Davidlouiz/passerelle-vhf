"""Tests du verrou PID pour empêcher instances multiples du runner."""

import os
import pytest
from pathlib import Path
import tempfile
import time
from unittest.mock import patch

from app.runner import acquire_pid_lock, release_pid_lock, PID_FILE


def test_acquire_pid_lock_first_time(tmp_path):
    """Premier verrou PID doit réussir."""
    test_pid_file = tmp_path / "test_runner.pid"

    with patch("app.runner.PID_FILE", test_pid_file):
        assert acquire_pid_lock() is True
        assert test_pid_file.exists()
        assert int(test_pid_file.read_text()) == os.getpid()

        # Cleanup
        release_pid_lock()
        assert not test_pid_file.exists()


def test_acquire_pid_lock_already_locked(tmp_path):
    """Deuxième tentative avec runner actif doit échouer."""
    test_pid_file = tmp_path / "test_runner.pid"

    with patch("app.runner.PID_FILE", test_pid_file):
        # Premier lock réussit
        assert acquire_pid_lock() is True

        # Deuxième tentative échoue (même PID)
        assert acquire_pid_lock() is False

        # Cleanup
        release_pid_lock()


def test_acquire_pid_lock_stale_pid(tmp_path):
    """Verrou avec PID obsolète (processus mort) doit être nettoyé."""
    test_pid_file = tmp_path / "test_runner.pid"

    with patch("app.runner.PID_FILE", test_pid_file):
        # Créer fichier PID avec PID inexistant (très grand nombre)
        fake_pid = 999999
        test_pid_file.write_text(str(fake_pid))

        # Tentative acquisition doit réussir après nettoyage
        assert acquire_pid_lock() is True
        assert int(test_pid_file.read_text()) == os.getpid()

        # Cleanup
        release_pid_lock()


def test_acquire_pid_lock_corrupted_file(tmp_path):
    """Fichier PID corrompu doit être recréé."""
    test_pid_file = tmp_path / "test_runner.pid"

    with patch("app.runner.PID_FILE", test_pid_file):
        # Créer fichier PID avec contenu invalide
        test_pid_file.write_text("not_a_number")

        # Acquisition doit réussir après nettoyage
        assert acquire_pid_lock() is True
        assert int(test_pid_file.read_text()) == os.getpid()

        # Cleanup
        release_pid_lock()


def test_release_pid_lock_wrong_pid(tmp_path):
    """Libération ne doit pas supprimer PID d'un autre processus."""
    test_pid_file = tmp_path / "test_runner.pid"

    with patch("app.runner.PID_FILE", test_pid_file):
        # Écrire PID différent
        other_pid = os.getpid() + 1
        test_pid_file.write_text(str(other_pid))

        # Tentative libération ne doit pas supprimer
        release_pid_lock()
        assert test_pid_file.exists()
        assert int(test_pid_file.read_text()) == other_pid


def test_pid_lock_prevents_double_runner(tmp_path):
    """Scénario réel : 2 runners ne peuvent tourner simultanément."""
    test_pid_file = tmp_path / "test_runner.pid"

    with patch("app.runner.PID_FILE", test_pid_file):
        # Simulation runner 1
        assert acquire_pid_lock() is True
        pid1 = os.getpid()

        # Tentative runner 2 (doit échouer)
        assert acquire_pid_lock() is False

        # Vérifier que le PID n'a pas changé
        assert int(test_pid_file.read_text()) == pid1

        # Runner 1 termine proprement
        release_pid_lock()
        assert not test_pid_file.exists()

        # Maintenant runner 2 peut démarrer
        assert acquire_pid_lock() is True
        release_pid_lock()
