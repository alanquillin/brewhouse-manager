"""Tests for lib/tap_monitors/plaato_blynk.py module"""

import pytest
from unittest.mock import patch, MagicMock

from lib.tap_monitors.plaato_blynk import PlaatoBlynk
from lib.tap_monitors import InvalidDataType


class TestPlaatoBlynk:
    """Tests for PlaatoBlynk class"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config"""
        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {
            "tap_monitors.plaato_blynk.base_url": "http://plaato.blynk.cc",
        }.get(key, default)
        return config

    @pytest.fixture
    @patch('lib.tap_monitors.plaato_blynk.TapMonitorBase.__init__')
    def monitor(self, mock_init, mock_config):
        """Create a PlaatoBlynk instance with mocked dependencies"""
        mock_init.return_value = None
        monitor = PlaatoBlynk.__new__(PlaatoBlynk)
        monitor.config = mock_config
        monitor.logger = MagicMock()
        return monitor

    def test_supports_discovery(self, monitor):
        """Test supports_discovery returns False"""
        assert monitor.supports_discovery() is False

    def test_discover_raises(self, monitor):
        """Test discover raises NotImplementedError"""
        with pytest.raises(NotImplementedError):
            monitor.discover()

    def test_data_type_to_pin_mapping(self, monitor):
        """Test _data_type_to_pin has expected mappings"""
        assert monitor._data_type_to_pin["percent_beer_remaining"] == "v48"
        assert monitor._data_type_to_pin["total_beer_remaining"] == "v51"
        assert monitor._data_type_to_pin["beer_remaining_unit"] == "v74"
        assert monitor._data_type_to_pin["firmware_version"] == "v93"

    @patch('lib.tap_monitors.plaato_blynk.requests')
    def test_get_success(self, mock_requests, monitor):
        """Test get with successful response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["75.5"]
        mock_requests.get.return_value = mock_response

        meta = {"auth_token": "test_token"}
        result = monitor.get("percent_beer_remaining", meta=meta)

        assert result == ["75.5"]
        mock_requests.get.assert_called_once()

    @patch('lib.tap_monitors.plaato_blynk.requests')
    def test_get_invalid_data_type_raises(self, mock_requests, monitor):
        """Test get raises InvalidDataType for unknown data type"""
        meta = {"auth_token": "test_token"}

        with pytest.raises(InvalidDataType):
            monitor.get("unknown_data_type", meta=meta)

    @patch('lib.tap_monitors.plaato_blynk.requests')
    def test_get_non_200_returns_empty_dict(self, mock_requests, monitor):
        """Test _get returns empty dict on non-200 response"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_requests.get.return_value = mock_response

        meta = {"auth_token": "test_token"}
        result = monitor._get("v48", meta)

        assert result == {}

    @patch('lib.tap_monitors.plaato_blynk.requests')
    def test_get_all(self, mock_requests, monitor):
        """Test get_all returns all data"""
        responses = [
            MagicMock(status_code=200, json=MagicMock(return_value=["75.5"])),
            MagicMock(status_code=200, json=MagicMock(return_value=["10.5"])),
            MagicMock(status_code=200, json=MagicMock(return_value=["L"])),
            MagicMock(status_code=200, json=MagicMock(return_value=["1.2.3"])),
        ]
        mock_requests.get.side_effect = responses

        meta = {"auth_token": "test_token"}
        result = monitor.get_all(meta=meta)

        assert "percentRemaining" in result
        assert "totalVolumeRemaining" in result
        assert "displayVolumeUnit" in result
        assert "firmwareVersion" in result

    def test_get_no_args_raises(self, monitor):
        """Test get with no args raises exception"""
        with pytest.raises(Exception):
            monitor.get("percent_beer_remaining")

    def test_get_all_no_args_raises(self, monitor):
        """Test get_all with no args raises exception"""
        with pytest.raises(Exception):
            monitor.get_all()

    @patch('lib.tap_monitors.plaato_blynk.requests')
    def test_get_url_construction(self, mock_requests, monitor):
        """Test _get constructs correct URL"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = ["data"]
        mock_requests.get.return_value = mock_response

        meta = {"auth_token": "my_auth_token"}
        monitor._get("v48", meta)

        called_url = mock_requests.get.call_args[0][0]
        assert "my_auth_token" in called_url
        assert "/get/v48" in called_url
