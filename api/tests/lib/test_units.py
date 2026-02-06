"""Tests for lib/units.py module"""

import pytest

from lib.units import from_g, from_ml, to_g, to_ml


class TestToMl:
    """Tests for to_ml function"""

    def test_ml_passthrough(self):
        """Test that ml returns unchanged"""
        assert to_ml(100, "ml") == 100
        assert to_ml(500, "ML") == 500

    def test_liters_to_ml(self):
        """Test liters to ml conversion"""
        result = to_ml(1, "l")
        assert result == 1000

        result = to_ml(2.5, "L")
        assert result == 2500

    def test_gallons_to_ml(self):
        """Test US gallons to ml conversion"""
        result = to_ml(1, "gal")
        assert pytest.approx(result, rel=0.001) == 3785.41

    def test_imperial_gallons_to_ml(self):
        """Test imperial gallons to ml conversion"""
        result = to_ml(1, "gal (imperial)")
        assert pytest.approx(result, rel=0.001) == 4546.09

    def test_pints_to_ml(self):
        """Test pints to ml conversion"""
        result = to_ml(1, "pt")
        assert pytest.approx(result, rel=0.001) == 473.18

    def test_imperial_pints_to_ml(self):
        """Test imperial pints to ml conversion"""
        result = to_ml(1, "p (imperial)")
        assert pytest.approx(result, rel=0.001) == 568.26

    def test_quarts_to_ml(self):
        """Test quarts to ml conversion"""
        result = to_ml(1, "qt")
        assert pytest.approx(result, rel=0.001) == 946.35

    def test_cups_to_ml(self):
        """Test cups to ml conversion"""
        result = to_ml(1, "cup")
        assert pytest.approx(result, rel=0.001) == 236.59

    def test_ounces_to_ml(self):
        """Test fluid ounces to ml conversion"""
        result = to_ml(1, "oz")
        assert pytest.approx(result, rel=0.001) == 29.57

    def test_invalid_unit_raises(self):
        """Test invalid unit raises exception"""
        with pytest.raises(Exception) as exc_info:
            to_ml(100, "invalid")
        assert "invalid volume unit" in str(exc_info.value)


class TestFromMl:
    """Tests for from_ml function"""

    def test_ml_to_liters(self):
        """Test ml to liters conversion"""
        result = from_ml(1000, "l")
        assert result == 1.0

    def test_ml_to_gallons(self):
        """Test ml to US gallons conversion"""
        result = from_ml(3785.41, "gal")
        assert pytest.approx(result, rel=0.001) == 1.0

    def test_ml_to_pints(self):
        """Test ml to pints conversion"""
        result = from_ml(473.18, "pt")
        assert pytest.approx(result, rel=0.001) == 1.0

    def test_ml_to_ounces(self):
        """Test ml to fluid ounces conversion"""
        result = from_ml(29.57, "oz")
        assert pytest.approx(result, rel=0.001) == 1.0

    def test_invalid_unit_raises(self):
        """Test invalid unit raises exception"""
        with pytest.raises(Exception) as exc_info:
            from_ml(100, "invalid")
        assert "invalid volume unit" in str(exc_info.value)


class TestToG:
    """Tests for to_g function"""

    def test_g_passthrough(self):
        """Test that grams returns unchanged"""
        assert to_g(100, "g") == 100
        assert to_g(500, "G") == 500

    def test_kg_to_g(self):
        """Test kilograms to grams conversion"""
        result = to_g(1, "kg")
        assert result == 1000

        result = to_g(2.5, "KG")
        assert result == 2500

    def test_oz_to_g(self):
        """Test ounces to grams conversion"""
        result = to_g(1, "oz")
        assert pytest.approx(result, rel=0.001) == 28.35

    def test_lb_to_g(self):
        """Test pounds to grams conversion"""
        result = to_g(1, "lb")
        assert pytest.approx(result, rel=0.001) == 453.59

    def test_invalid_unit_raises(self):
        """Test invalid unit raises exception"""
        with pytest.raises(Exception) as exc_info:
            to_g(100, "invalid")
        assert "invalid" in str(exc_info.value).lower()


class TestFromG:
    """Tests for from_g function"""

    def test_g_passthrough(self):
        """Test that grams returns unchanged"""
        assert from_g(100, "g") == 100
        assert from_g(500, "G") == 500

    def test_zero_returns_zero(self):
        """Test that zero value returns zero for any unit"""
        assert from_g(0, "kg") == 0
        assert from_g(0, "oz") == 0
        assert from_g(0, "lb") == 0

    def test_g_to_kg(self):
        """Test grams to kilograms conversion"""
        result = from_g(1000, "kg")
        assert result == 1.0

    def test_g_to_oz(self):
        """Test grams to ounces conversion"""
        result = from_g(28.35, "oz")
        assert pytest.approx(result, rel=0.001) == 1.0

    def test_g_to_lb(self):
        """Test grams to pounds conversion"""
        result = from_g(453.59, "lb")
        assert pytest.approx(result, rel=0.001) == 1.0

    def test_invalid_unit_raises(self):
        """Test invalid unit raises exception"""
        with pytest.raises(Exception) as exc_info:
            from_g(100, "invalid")
        assert "invalid" in str(exc_info.value).lower()


class TestRoundTrip:
    """Round-trip conversion tests"""

    def test_ml_round_trip_liters(self):
        """Test ml -> L -> ml round trip"""
        original = 1500.0
        converted = to_ml(from_ml(original, "l"), "l")
        assert pytest.approx(converted, rel=0.0001) == original

    def test_ml_round_trip_gallons(self):
        """Test ml -> gal -> ml round trip"""
        original = 5000.0
        converted = to_ml(from_ml(original, "gal"), "gal")
        assert pytest.approx(converted, rel=0.0001) == original

    def test_g_round_trip_kg(self):
        """Test g -> kg -> g round trip"""
        original = 2500.0
        converted = to_g(from_g(original, "kg"), "kg")
        assert pytest.approx(converted, rel=0.0001) == original

    def test_g_round_trip_lb(self):
        """Test g -> lb -> g round trip"""
        original = 1000.0
        converted = to_g(from_g(original, "lb"), "lb")
        assert pytest.approx(converted, rel=0.0001) == original
