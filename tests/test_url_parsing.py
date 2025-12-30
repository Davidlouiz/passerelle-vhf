"""Tests pour le parsing des URLs de providers."""

import pytest
from app.providers.ffvl import FFVLProvider
from app.providers.openwindmap import OpenWindMapProvider
from app.exceptions import ValidationError


class TestFFVLURLParsing:
    """Tests de parsing d'URLs FFVL."""

    def test_parse_standard_url(self):
        """Teste le parsing d'une URL FFVL standard."""
        provider = FFVLProvider()
        url = "https://www.balisemeteo.com/balise.php?idBalise=67"

        info = provider.resolve_station_from_url(url)

        assert info.provider_id == "ffvl"
        assert info.station_id == "67"

    def test_parse_mobile_url(self):
        """Teste le parsing d'une URL mobile FFVL."""
        provider = FFVLProvider()
        url = "https://www.balisemeteo.com/balise_mob.php?idBalise=123"

        info = provider.resolve_station_from_url(url)

        assert info.station_id == "123"

    def test_parse_url_with_multiple_params(self):
        """Teste le parsing avec plusieurs paramètres."""
        provider = FFVLProvider()
        url = "https://www.balisemeteo.com/balise.php?foo=bar&idBalise=42&baz=qux"

        info = provider.resolve_station_from_url(url)

        assert info.station_id == "42"

    def test_parse_invalid_domain(self):
        """Teste le rejet d'un domaine invalide."""
        provider = FFVLProvider()
        url = "https://example.com/balise.php?idBalise=67"

        with pytest.raises(ValidationError) as exc_info:
            provider.resolve_station_from_url(url)

        assert "non reconnue" in str(exc_info.value)

    def test_parse_missing_id_balise(self):
        """Teste le rejet si idBalise manquant."""
        provider = FFVLProvider()
        url = "https://www.balisemeteo.com/balise.php?foo=bar"

        with pytest.raises(ValidationError) as exc_info:
            provider.resolve_station_from_url(url)

        assert "idBalise" in str(exc_info.value)

    def test_parse_non_numeric_id(self):
        """Teste le rejet si idBalise n'est pas numérique."""
        provider = FFVLProvider()
        url = "https://www.balisemeteo.com/balise.php?idBalise=abc"

        with pytest.raises(ValidationError) as exc_info:
            provider.resolve_station_from_url(url)

        assert "entier" in str(exc_info.value)


class TestOpenWindMapURLParsing:
    """Tests de parsing d'URLs OpenWindMap."""

    def test_parse_pioupiou_url(self):
        """Teste le parsing d'une URL pioupiou-XXX."""
        provider = OpenWindMapProvider()
        url = "https://www.openwindmap.org/pioupiou-385"

        info = provider.resolve_station_from_url(url)

        assert info.provider_id == "openwindmap"
        assert info.station_id == "385"

    def test_parse_windbird_url(self):
        """Teste le parsing d'une URL windbird-XXX."""
        provider = OpenWindMapProvider()
        url = "https://www.openwindmap.org/windbird-1500"

        info = provider.resolve_station_from_url(url)

        assert info.station_id == "1500"

    def test_parse_pp_short_url(self):
        """Teste le parsing d'une URL courte PPXXX."""
        provider = OpenWindMapProvider()
        url = "https://www.openwindmap.org/PP603"

        info = provider.resolve_station_from_url(url)

        assert info.station_id == "603"

    def test_parse_wb_short_url(self):
        """Teste le parsing d'une URL courte WBXXX."""
        provider = OpenWindMapProvider()
        url = "https://www.openwindmap.org/WB1234"

        info = provider.resolve_station_from_url(url)

        assert info.station_id == "1234"

    def test_parse_invalid_domain(self):
        """Teste le rejet d'un domaine invalide."""
        provider = OpenWindMapProvider()
        url = "https://example.com/pioupiou-385"

        with pytest.raises(ValidationError) as exc_info:
            provider.resolve_station_from_url(url)

        assert "non reconnue" in str(exc_info.value)

    def test_parse_invalid_format(self):
        """Teste le rejet d'un format invalide."""
        provider = OpenWindMapProvider()
        url = "https://www.openwindmap.org/invalid-format"

        with pytest.raises(ValidationError) as exc_info:
            provider.resolve_station_from_url(url)

        assert "non reconnu" in str(exc_info.value)
