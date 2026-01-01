"""
Tests de validation de la clé API FFVL.
"""

import pytest
from app.providers.ffvl import FFVLProvider


@pytest.mark.asyncio
async def test_validate_invalid_api_key():
    """Test avec une clé API invalide."""
    invalid_key = "00000000000000000000000000000000"
    is_valid = await FFVLProvider.validate_api_key(invalid_key)
    assert is_valid is False, "La clé invalide devrait être rejetée"


@pytest.mark.asyncio
async def test_validate_empty_api_key():
    """Test avec une clé API vide."""
    is_valid = await FFVLProvider.validate_api_key("")
    assert is_valid is False, "Une clé vide devrait être rejetée"


@pytest.mark.asyncio
async def test_validate_malformed_api_key():
    """Test avec une clé API mal formée."""
    malformed_key = "not-a-valid-key"
    is_valid = await FFVLProvider.validate_api_key(malformed_key)
    assert is_valid is False, "Une clé mal formée devrait être rejetée"


# NOTE: Pour tester une vraie clé valide, décommenter et remplacer par votre clé
# @pytest.mark.asyncio
# async def test_validate_valid_api_key():
#     """Test avec une clé API valide (nécessite une vraie clé)."""
#     valid_key = "VOTRE_CLE_VALIDE_ICI"
#     is_valid = await FFVLProvider.validate_api_key(valid_key)
#     assert is_valid is True, "Une clé valide devrait être acceptée"
