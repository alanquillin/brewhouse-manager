"""Tests for services/plaato_keg.py module - Plaato Keg service"""

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.plaato_keg import CONVERSIONS, PlaatoKegService, clean_str, to_bool, to_float, to_int


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestToInt:
    """Tests for to_int helper function"""

    def test_returns_int_unchanged(self):
        """Test returns int unchanged"""
        assert to_int(42) == 42

    def test_converts_string_to_int(self):
        """Test converts string to int"""
        assert to_int("123") == 123

    def test_handles_string_with_whitespace(self):
        """Test handles string with whitespace"""
        assert to_int("  456  ") == 456

    def test_returns_none_for_empty_string(self):
        """Test returns None for empty string"""
        assert to_int("") is None

    def test_returns_none_for_whitespace_only(self):
        """Test returns None for whitespace only"""
        assert to_int("   ") is None

    def test_returns_none_for_none(self):
        """Test returns None for None input"""
        assert to_int(None) is None


class TestToFloat:
    """Tests for to_float helper function"""

    def test_returns_float_unchanged(self):
        """Test returns float unchanged"""
        assert to_float(3.14) == 3.14

    def test_converts_string_to_float(self):
        """Test converts string to float"""
        assert to_float("3.14") == 3.14

    def test_converts_int_string_to_float(self):
        """Test converts integer string to float"""
        assert to_float("42") == 42.0

    def test_handles_string_with_whitespace(self):
        """Test handles string with whitespace"""
        assert to_float("  2.5  ") == 2.5

    def test_returns_none_for_empty_string(self):
        """Test returns None for empty string"""
        assert to_float("") is None

    def test_returns_none_for_none(self):
        """Test returns None for None input"""
        assert to_float(None) is None


class TestToBool:
    """Tests for to_bool helper function"""

    def test_returns_bool_unchanged(self):
        """Test returns bool unchanged"""
        assert to_bool(True) is True
        assert to_bool(False) is False

    def test_converts_true_string(self):
        """Test converts 'true' string to True"""
        assert to_bool("true") is True
        assert to_bool("True") is True
        assert to_bool("TRUE") is True

    def test_converts_1_string(self):
        """Test converts '1' string to True"""
        assert to_bool("1") is True

    def test_converts_false_string(self):
        """Test converts 'false' string to False"""
        assert to_bool("false") is False
        assert to_bool("False") is False

    def test_converts_0_string(self):
        """Test converts '0' string to False"""
        assert to_bool("0") is False

    def test_returns_none_for_empty_string(self):
        """Test returns None for empty string"""
        assert to_bool("") is None

    def test_returns_none_for_none(self):
        """Test returns None for None input"""
        assert to_bool(None) is None


class TestCleanStr:
    """Tests for clean_str helper function"""

    def test_strips_whitespace(self):
        """Test strips leading/trailing whitespace"""
        assert clean_str("  hello  ") == "hello"

    def test_returns_none_for_empty_string(self):
        """Test returns None for empty string"""
        assert clean_str("") is None

    def test_returns_none_for_whitespace_only(self):
        """Test returns None for whitespace only"""
        assert clean_str("   ") is None

    def test_returns_none_for_none(self):
        """Test returns None for None input"""
        assert clean_str(None) is None

    def test_preserves_content(self):
        """Test preserves actual content"""
        assert clean_str("hello world") == "hello world"


class TestConversions:
    """Tests for CONVERSIONS mapping"""

    def test_percent_of_beer_left_uses_float(self):
        """Test percent_of_beer_left uses to_float"""
        assert CONVERSIONS["percent_of_beer_left"] == to_float

    def test_is_pouring_uses_bool(self):
        """Test is_pouring uses to_bool"""
        assert CONVERSIONS["is_pouring"] == to_bool

    def test_wifi_signal_strength_uses_int(self):
        """Test wifi_signal_strength uses to_int"""
        assert CONVERSIONS["wifi_signal_strength"] == to_int

    def test_leak_detection_uses_bool(self):
        """Test leak_detection uses to_bool"""
        assert CONVERSIONS["leak_detection"] == to_bool


class TestPlaatoKegServiceTransformResponse:
    """Tests for PlaatoKegService.transform_response method"""

    def test_returns_none_for_none_input(self):
        """Test returns None when plaato_keg is None"""
        mock_session = AsyncMock()
        result = run_async(PlaatoKegService.transform_response(None, mock_session))
        assert result is None

    def test_basic_transformation(self):
        """Test basic plaato keg transformation"""
        mock_keg = MagicMock()
        mock_keg.id = "plaato-1"
        mock_keg.last_updated_on = datetime.now(timezone.utc)
        mock_keg.to_dict.return_value = {
            "id": "plaato-1",
            "name": "Test Keg",
            "percent_of_beer_left": "75.5",
            "is_pouring": "false",
        }

        mock_session = AsyncMock()

        with patch("services.plaato_keg.service_handler") as mock_handler:
            mock_handler.connection_handler.get_registered_device_ids.return_value = []
            result = run_async(PlaatoKegService.transform_response(mock_keg, mock_session))

        assert result is not None
        assert result["percentOfBeerLeft"] == 75.5
        assert result["isPouring"] is False

    def test_converts_numeric_fields(self):
        """Test converts numeric string fields to proper types"""
        mock_keg = MagicMock()
        mock_keg.id = "plaato-1"
        mock_keg.last_updated_on = datetime.now(timezone.utc)
        mock_keg.to_dict.return_value = {
            "id": "plaato-1",
            "amount_left": "10.5",
            "keg_temperature": "4.2",
            "wifi_signal_strength": "-65",
        }

        mock_session = AsyncMock()

        with patch("services.plaato_keg.service_handler") as mock_handler:
            mock_handler.connection_handler.get_registered_device_ids.return_value = []
            result = run_async(PlaatoKegService.transform_response(mock_keg, mock_session))

        assert result["amountLeft"] == 10.5
        assert result["kegTemperature"] == 4.2
        assert result["wifiSignalStrength"] == -65

    def test_sets_mode_co2_when_no_og_fg(self):
        """Test sets mode to 'co2' when no OG/FG"""
        mock_keg = MagicMock()
        mock_keg.id = "plaato-1"
        mock_keg.last_updated_on = datetime.now(timezone.utc)
        mock_keg.to_dict.return_value = {
            "id": "plaato-1",
            "og": None,
            "fg": None,
        }

        mock_session = AsyncMock()

        with patch("services.plaato_keg.service_handler") as mock_handler:
            mock_handler.connection_handler.get_registered_device_ids.return_value = []
            result = run_async(PlaatoKegService.transform_response(mock_keg, mock_session))

        assert result["mode"] == "co2"

    def test_sets_mode_beer_when_og_fg_present(self):
        """Test sets mode to 'beer' when OG/FG present"""
        mock_keg = MagicMock()
        mock_keg.id = "plaato-1"
        mock_keg.last_updated_on = datetime.now(timezone.utc)
        mock_keg.to_dict.return_value = {
            "id": "plaato-1",
            "og": "1.050",
            "fg": "1.010",
        }

        mock_session = AsyncMock()

        with patch("services.plaato_keg.service_handler") as mock_handler:
            mock_handler.connection_handler.get_registered_device_ids.return_value = []
            result = run_async(PlaatoKegService.transform_response(mock_keg, mock_session))

        assert result["mode"] == "beer"

    def test_sets_unit_mode_weight_metric(self):
        """Test sets unitMode='weight', unitType='metric' for unit=1, measure_unit=1"""
        mock_keg = MagicMock()
        mock_keg.id = "plaato-1"
        mock_keg.last_updated_on = datetime.now(timezone.utc)
        mock_keg.to_dict.return_value = {
            "id": "plaato-1",
            "unit": "1",
            "measure_unit": "1",
        }

        mock_session = AsyncMock()

        with patch("services.plaato_keg.service_handler") as mock_handler:
            mock_handler.connection_handler.get_registered_device_ids.return_value = []
            result = run_async(PlaatoKegService.transform_response(mock_keg, mock_session))

        assert result["unitMode"] == "weight"
        assert result["unitType"] == "metric"

    def test_sets_unit_mode_volume_us(self):
        """Test sets unitMode='volume', unitType='us' for unit=2, measure_unit=2"""
        mock_keg = MagicMock()
        mock_keg.id = "plaato-1"
        mock_keg.last_updated_on = datetime.now(timezone.utc)
        mock_keg.to_dict.return_value = {
            "id": "plaato-1",
            "unit": "2",
            "measure_unit": "2",
        }

        mock_session = AsyncMock()

        with patch("services.plaato_keg.service_handler") as mock_handler:
            mock_handler.connection_handler.get_registered_device_ids.return_value = []
            result = run_async(PlaatoKegService.transform_response(mock_keg, mock_session))

        assert result["unitMode"] == "volume"
        assert result["unitType"] == "us"

    def test_sets_unit_mode_volume_metric(self):
        """Test sets unitMode='volume', unitType='metric' for unit=1, measure_unit=2"""
        mock_keg = MagicMock()
        mock_keg.id = "plaato-1"
        mock_keg.last_updated_on = datetime.now(timezone.utc)
        mock_keg.to_dict.return_value = {
            "id": "plaato-1",
            "unit": "1",
            "measure_unit": "2",
        }

        mock_session = AsyncMock()

        with patch("services.plaato_keg.service_handler") as mock_handler:
            mock_handler.connection_handler.get_registered_device_ids.return_value = []
            result = run_async(PlaatoKegService.transform_response(mock_keg, mock_session))

        assert result["unitMode"] == "volume"
        assert result["unitType"] == "metric"

    def test_sets_unit_mode_weight_us(self):
        """Test sets unitMode='weight', unitType='us' for unit=2, measure_unit=1"""
        mock_keg = MagicMock()
        mock_keg.id = "plaato-1"
        mock_keg.last_updated_on = datetime.now(timezone.utc)
        mock_keg.to_dict.return_value = {
            "id": "plaato-1",
            "unit": "2",
            "measure_unit": "1",
        }

        mock_session = AsyncMock()

        with patch("services.plaato_keg.service_handler") as mock_handler:
            mock_handler.connection_handler.get_registered_device_ids.return_value = []
            result = run_async(PlaatoKegService.transform_response(mock_keg, mock_session))

        assert result["unitMode"] == "weight"
        assert result["unitType"] == "us"

    def test_sets_connected_true_when_registered(self):
        """Test sets connected=True when device is registered"""
        mock_keg = MagicMock()
        mock_keg.id = "plaato-1"
        mock_keg.last_updated_on = datetime.now(timezone.utc)
        mock_keg.to_dict.return_value = {"id": "plaato-1"}

        mock_session = AsyncMock()

        with patch("services.plaato_keg.service_handler") as mock_handler:
            mock_handler.connection_handler.get_registered_device_ids.return_value = ["plaato-1"]
            result = run_async(PlaatoKegService.transform_response(mock_keg, mock_session))

        assert result["connected"] is True

    def test_sets_connected_false_when_not_registered(self):
        """Test sets connected=False when device is not registered"""
        mock_keg = MagicMock()
        mock_keg.id = "plaato-1"
        mock_keg.last_updated_on = datetime.now(timezone.utc)
        mock_keg.to_dict.return_value = {"id": "plaato-1"}

        mock_session = AsyncMock()

        with patch("services.plaato_keg.service_handler") as mock_handler:
            mock_handler.connection_handler.get_registered_device_ids.return_value = ["other-device"]
            result = run_async(PlaatoKegService.transform_response(mock_keg, mock_session))

        assert result["connected"] is False

    def test_cleans_string_values(self):
        """Test cleans string values that aren't in CONVERSIONS"""
        mock_keg = MagicMock()
        mock_keg.id = "plaato-1"
        mock_keg.last_updated_on = datetime.now(timezone.utc)
        mock_keg.to_dict.return_value = {
            "id": "plaato-1",
            "name": "  Test Keg  ",
            "beer_style": "  IPA  ",
        }

        mock_session = AsyncMock()

        with patch("services.plaato_keg.service_handler") as mock_handler:
            mock_handler.connection_handler.get_registered_device_ids.return_value = []
            result = run_async(PlaatoKegService.transform_response(mock_keg, mock_session))

        assert result["name"] == "Test Keg"
        assert result["beerStyle"] == "IPA"

    def test_no_mode_when_no_last_updated(self):
        """Test no mode/unit fields when last_updated_on is None"""
        mock_keg = MagicMock()
        mock_keg.id = "plaato-1"
        mock_keg.last_updated_on = None
        mock_keg.to_dict.return_value = {"id": "plaato-1"}

        mock_session = AsyncMock()

        result = run_async(PlaatoKegService.transform_response(mock_keg, mock_session))

        assert "mode" not in result
        assert "unitMode" not in result
        assert "connected" not in result
