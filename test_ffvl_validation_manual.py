#!/usr/bin/env python3
"""Test manuel de validation de clé FFVL."""

import asyncio
import sys
import os

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.providers.ffvl import FFVLProvider


async def test_validation():
    """Test de validation de différentes clés."""

    print("Test 1: Clé invalide (tous zéros)")
    invalid_key = "00000000000000000000000000000000"
    result = await FFVLProvider.validate_api_key(invalid_key)
    print(f"  Résultat: {result} (attendu: False)")
    assert result is False, "Clé invalide devrait être rejetée"
    print("  ✓ OK\n")

    print("Test 2: Clé vide")
    result = await FFVLProvider.validate_api_key("")
    print(f"  Résultat: {result} (attendu: False)")
    assert result is False, "Clé vide devrait être rejetée"
    print("  ✓ OK\n")

    print("Test 3: Clé mal formée")
    result = await FFVLProvider.validate_api_key("not-a-valid-key")
    print(f"  Résultat: {result} (attendu: False)")
    assert result is False, "Clé mal formée devrait être rejetée"
    print("  ✓ OK\n")

    print("Tous les tests ont réussi ✓")


if __name__ == "__main__":
    asyncio.run(test_validation())
