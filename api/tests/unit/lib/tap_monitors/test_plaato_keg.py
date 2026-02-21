"""Tests for lib/tap_monitors/plaato_keg.py module"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lib.tap_monitors import InvalidDataType
from lib.tap_monitors.plaato_keg import KEYMAP, PlaatoKeg


# Helper to run async functions in sync tests
def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestPlaatoKegKeymap:
    """Tests for KEYMAP"""

    def test_keymap_has_expected_keys(self):
        """Test KEYMAP has expected mappings"""
        assert KEYMAP["percent_beer_remaining"] == "percent_of_beer_left"
        assert KEYMAP["total_beer_remaining"] == "amount_left"
        assert KEYMAP["beer_remaining_unit"] == "beer_left_unit"
        assert KEYMAP["firmware_version"] == "firmware_version"


class TestPlaatoKeg:
    """Tests for PlaatoKeg class"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config"""
        config = MagicMock()
        return config

    @pytest.fixture
    @patch("lib.tap_monitors.plaato_keg.TapMonitorBase.__init__")
    def monitor(self, mock_init, mock_config):
        """Create a PlaatoKeg instance with mocked dependencies"""
        mock_init.return_value = None
        monitor = PlaatoKeg.__new__(PlaatoKeg)
        monitor.config = mock_config
        monitor.logger = MagicMock()
        return monitor

    def test_supports_discovery(self, monitor):
        """Test supports_discovery returns True"""
        assert monitor.supports_discovery() is True

    @patch("lib.tap_monitors.plaato_keg.PlaatoDataDB")
    @patch("lib.tap_monitors.plaato_keg.async_session_scope")
    def test_get_success(self, mock_session_scope, mock_plaato_db, monitor):
        """Test get with successful data retrieval"""
        mock_data = MagicMock()
        mock_data.to_dict.return_value = {"percent_of_beer_left": 75.5, "amount_left": 10.5, "beer_left_unit": "L", "firmware_version": "1.2.3"}
        mock_plaato_db.get_by_pkey = AsyncMock(return_value=mock_data)

        meta = {"device_id": "device123"}
        result = run_async(monitor.get("percent_beer_remaining", meta=meta, db_session=MagicMock()))

        assert result == 75.5

    @patch("lib.tap_monitors.plaato_keg.PlaatoDataDB")
    def test_get_invalid_data_key_raises(self, mock_plaato_db, monitor):
        """Test get raises InvalidDataType for unknown key"""
        mock_data = MagicMock()
        mock_data.to_dict.return_value = {}
        mock_plaato_db.get_by_pkey = AsyncMock(return_value=mock_data)

        meta = {"device_id": "device123"}
        with pytest.raises(InvalidDataType):
            run_async(monitor.get("unknown_key", meta=meta, db_session=MagicMock()))

    @patch("lib.tap_monitors.plaato_keg.PlaatoDataDB")
    def test_get_all(self, mock_plaato_db, monitor):
        """Test get_all returns all data"""
        mock_data = MagicMock()
        mock_data.to_dict.return_value = {"percent_of_beer_left": 80, "amount_left": 15, "beer_left_unit": "gal", "firmware_version": "2.0.0"}
        mock_plaato_db.get_by_pkey = AsyncMock(return_value=mock_data)

        meta = {"device_id": "device456"}
        result = run_async(monitor.get_all(meta=meta, db_session=MagicMock()))

        assert result["percentRemaining"] == 80
        assert result["totalVolumeRemaining"] == 15
        assert result["displayVolumeUnit"] == "gal"
        assert result["firmwareVersion"] == "2.0.0"

    @patch("lib.tap_monitors.plaato_keg.PlaatoDataDB")
    @patch("lib.tap_monitors.plaato_keg.async_session_scope")
    def test_discover(self, mock_session_scope, mock_plaato_db, monitor):
        """Test discover returns list of devices"""
        mock_device1 = MagicMock()
        mock_device1.id = "dev1"
        mock_device1.name = "Keg 1"
        mock_device1.last_updated_on = "2024-01-01"

        mock_device2 = MagicMock()
        mock_device2.id = "dev2"
        mock_device2.name = "Keg 2"
        mock_device2.last_updated_on = "2024-01-02"

        mock_plaato_db.query = AsyncMock(return_value=[mock_device1, mock_device2])

        mock_session = MagicMock()
        result = run_async(monitor.discover(db_session=mock_session))

        assert len(result) == 2
        assert {"id": "dev1", "name": "Keg 1"} in result
        assert {"id": "dev2", "name": "Keg 2"} in result

    @patch("lib.tap_monitors.plaato_keg.PlaatoDataDB")
    def test_discover_excludes_devices_without_last_updated(self, mock_plaato_db, monitor):
        """Test discover excludes devices without last_updated_on"""
        mock_device = MagicMock()
        mock_device.id = "dev1"
        mock_device.name = "Keg 1"
        mock_device.last_updated_on = None  # No last update

        mock_plaato_db.query = AsyncMock(return_value=[mock_device])

        result = run_async(monitor.discover(db_session=MagicMock()))

        assert len(result) == 0

    @patch("lib.tap_monitors.plaato_keg.PlaatoDataDB")
    def test_get_data_no_data_returns_empty_dict(self, mock_plaato_db, monitor):
        """Test _get returns empty dict when no data found"""
        mock_plaato_db.get_by_pkey = AsyncMock(return_value=None)

        result = run_async(monitor._get(MagicMock(), "device_id"))

        assert result == {}

    def test_get_data_no_args_raises(self, monitor):
        """Test _get_data with no args raises exception"""
        with pytest.raises(Exception):
            run_async(monitor._get_data())
