"""Tests for lib/tap_monitors/keg_volume_monitor.py module"""

import asyncio
import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lib.tap_monitors.exceptions import TapMonitorDependencyError
from lib.tap_monitors.keg_volume_monitor import KEYMAP, KegVolumeMonitor


# Helper to run async functions in sync tests
def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestKegVolumeMonitorKeymap:
    """Tests for KEYMAP"""

    def test_keymap_has_expected_keys(self):
        """Test KEYMAP has expected mappings"""
        assert KEYMAP["percent_beer_remaining"] == "percentRemaining"
        assert KEYMAP["total_beer_remaining"] == "totalVolumeRemaining"
        assert KEYMAP["beer_remaining_unit"] == "displayVolumeUnit"
        assert KEYMAP["firmware_version"] == "firmwareVersion"


class TestKegVolumeMonitor:
    """Tests for KegVolumeMonitor class"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config"""
        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {
            "tap_monitors.keg_volume_monitors.base_url": "http://localhost:8080",
            "tap_monitors.keg_volume_monitors.api_key": "test_api_key",
        }.get(key, default)
        return config

    @pytest.fixture
    @patch("lib.tap_monitors.keg_volume_monitor.TapMonitorBase.__init__")
    def monitor(self, mock_init, mock_config):
        """Create a KegVolumeMonitor instance with mocked dependencies"""
        mock_init.return_value = None
        monitor = KegVolumeMonitor.__new__(KegVolumeMonitor)
        monitor.config = mock_config
        monitor.logger = MagicMock()
        return monitor

    def test_supports_discovery(self, monitor):
        """Test supports_discovery returns True"""
        assert monitor.supports_discovery() is True

    def test_get_auth_header_val(self, monitor):
        """Test _get_auth_header_val generates correct Bearer token"""
        result = monitor._get_auth_header_val()

        assert result.startswith("Bearer ")
        # Decode and verify format
        token_b64 = result.replace("Bearer ", "")
        decoded = base64.b64decode(token_b64).decode("ascii")
        assert decoded == "svc|test_api_key"

    @patch("lib.tap_monitors.keg_volume_monitor.AsyncClient")
    def test_get_success(self, mock_async_client, monitor):
        """Test get with successful response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"percentRemaining": 75.5, "totalVolumeRemaining": 10.5, "displayVolumeUnit": "L", "firmwareVersion": "1.2.3"}

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        meta = {"device_id": "device123"}
        result = run_async(monitor.get("percent_beer_remaining", meta=meta))

        assert result == 75.5

    @patch("lib.tap_monitors.keg_volume_monitor.AsyncClient")
    def test_get_all(self, mock_async_client, monitor):
        """Test get_all returns all data"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"percentRemaining": 80, "totalVolumeRemaining": 15, "displayVolumeUnit": "gal", "firmwareVersion": "2.0.0"}

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

    @patch("lib.tap_monitors.keg_volume_monitor.AsyncClient")
    def test_discover(self, mock_async_client, monitor):
        """Test discover returns list of devices"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": "dev1", "name": "Device 1"},
            {"id": "dev2", "name": "Device 2"},
        ]

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        result = run_async(monitor.discover())

        assert len(result) == 2
        assert {"id": "dev1", "name": "Device 1"} in result

    @patch("lib.tap_monitors.keg_volume_monitor.AsyncClient")
    def test_get_401_raises_dependency_error(self, mock_async_client, monitor):
        """Test _get raises TapMonitorDependencyError on 401"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Unauthorized"}

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        with pytest.raises(TapMonitorDependencyError):
            run_async(monitor._get("devices"))

    @patch("lib.tap_monitors.keg_volume_monitor.AsyncClient")
    def test_get_includes_auth_header(self, mock_async_client, monitor):
        """Test _get includes Authorization header"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = []

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        run_async(monitor._get("devices"))

        # Check that headers were passed
        call_kwargs = mock_client.get.call_args[1]
        assert "headers" in call_kwargs
        assert "Authorization" in call_kwargs["headers"]
        assert call_kwargs["headers"]["Authorization"].startswith("Bearer ")

    def test_get_no_args_raises(self, monitor):
        """Test get with no args raises exception"""
        with pytest.raises(Exception):
            run_async(monitor.get("percent_beer_remaining"))

    def test_get_all_no_args_raises(self, monitor):
        """Test get_all with no args raises exception"""
        with pytest.raises(Exception):
            run_async(monitor.get_all())
