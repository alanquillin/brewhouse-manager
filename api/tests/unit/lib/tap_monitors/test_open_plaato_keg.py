"""Tests for lib/tap_monitors/open_plaato_keg.py module"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lib.tap_monitors import InvalidDataType
from lib.tap_monitors.open_plaato_keg import KEYMAP, OpenPlaatoKeg


# Helper to run async functions in sync tests
def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestOpenPlaatoKegKeymap:
    """Tests for KEYMAP"""

    def test_keymap_has_expected_keys(self):
        """Test KEYMAP has expected mappings"""
        assert KEYMAP["percent_beer_remaining"] == "percent_of_beer_left"
        assert KEYMAP["total_beer_remaining"] == "amount_left"
        assert KEYMAP["beer_remaining_unit"] == "beer_left_unit"
        assert KEYMAP["firmware_version"] == "firmware_version"


class TestOpenPlaatoKeg:
    """Tests for OpenPlaatoKeg class"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config"""
        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {
            "tap_monitors.open_plaato_keg.base_url": "http://localhost:5000",
            "tap_monitors.open_plaato_keg.insecure": False,
        }.get(key, default)
        return config

    @pytest.fixture
    @patch("lib.tap_monitors.open_plaato_keg.TapMonitorBase.__init__")
    def monitor(self, mock_init, mock_config):
        """Create an OpenPlaatoKeg instance with mocked dependencies"""
        mock_init.return_value = None
        monitor = OpenPlaatoKeg.__new__(OpenPlaatoKeg)
        monitor.config = mock_config
        monitor.logger = MagicMock()
        return monitor

    def test_supports_discovery(self, monitor):
        """Test supports_discovery returns True"""
        assert monitor.supports_discovery() is True

    @patch("lib.tap_monitors.open_plaato_keg.AsyncClient")
    def test_get_success(self, mock_async_client, monitor):
        """Test get with successful response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "percent_of_beer_left": 75.5,
            "amount_left": 10.5,
            "beer_left_unit": "L",
        }

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        meta = {"device_id": "device123"}
        result = run_async(monitor.get("percent_beer_remaining", meta=meta))

        assert result == 75.5

    @patch("lib.tap_monitors.open_plaato_keg.AsyncClient")
    def test_get_invalid_data_key_raises(self, mock_async_client, monitor):
        """Test get raises InvalidDataType for unknown key"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        meta = {"device_id": "device123"}
        with pytest.raises(InvalidDataType):
            run_async(monitor.get("unknown_key", meta=meta))

    @patch("lib.tap_monitors.open_plaato_keg.AsyncClient")
    def test_get_all(self, mock_async_client, monitor):
        """Test get_all returns all data"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"percent_of_beer_left": 80, "amount_left": 15, "beer_left_unit": "gal", "firmware_version": "2.0.0"}

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        meta = {"device_id": "device456"}
        result = run_async(monitor.get_all(meta=meta))

        assert result["percentRemaining"] == 80
        assert result["totalVolumeRemaining"] == 15
        assert result["displayVolumeUnit"] == "gal"
        assert result["firmwareVersion"] == "2.0.0"

    @patch("lib.tap_monitors.open_plaato_keg.AsyncClient")
    def test_discover(self, mock_async_client, monitor):
        """Test discover returns list of devices"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": "keg1", "name": "Kitchen Keg"},
            {"id": "keg2", "name": "Garage Keg"},
        ]

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        result = run_async(monitor.discover())

        assert len(result) == 2
        assert {"id": "keg1", "name": "Kitchen Keg"} in result

    @patch("lib.tap_monitors.open_plaato_keg.AsyncClient")
    def test_discover_unknown_name(self, mock_async_client, monitor):
        """Test discover uses 'unknown' for missing name"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": "keg1"},  # No name
        ]

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        result = run_async(monitor.discover())

        assert result[0]["name"] == "unknown"

    @patch("lib.tap_monitors.open_plaato_keg.AsyncClient")
    def test_insecure_mode(self, mock_async_client, monitor, mock_config):
        """Test insecure mode disables SSL verification"""
        mock_config.get.side_effect = lambda key, default=None: {
            "tap_monitors.open_plaato_keg.base_url": "https://localhost:5000",
            "tap_monitors.open_plaato_keg.insecure": True,
        }.get(key, default)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        run_async(monitor._get("kegs"))

        # Verify AsyncClient was called with verify=False
        call_kwargs = mock_async_client.call_args[1]
        assert call_kwargs.get("verify") is False

    def test_get_data_no_args_raises(self, monitor):
        """Test _get_data with no args raises exception"""
        with pytest.raises(Exception):
            run_async(monitor._get_data())
