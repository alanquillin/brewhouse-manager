"""Tests for lib/tap_monitors/kegtron.py module"""

import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from lib.tap_monitors.kegtron import KegtronPro, MONITOR_TYPE
from lib.tap_monitors.exceptions import TapMonitorDependencyError


# Helper to run async functions in sync tests
def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestKegtronConstants:
    """Tests for kegtron constants"""

    def test_monitor_type(self):
        """Test MONITOR_TYPE value"""
        assert MONITOR_TYPE == "kegtron-pro"


class TestKegtronPro:
    """Tests for KegtronPro class"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config"""
        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {
            "tap_monitors.preferred_vol_unit": "L",
            "tap_monitors.kegtron.pro.auth.customer_api_key": "test_customer_key",
            "tap_monitors.kegtron.pro.auth.username": "test_user",
            "tap_monitors.kegtron.pro.auth.password": "test_pass",
        }.get(key, default)
        return config

    @pytest.fixture
    @patch('lib.tap_monitors.kegtron.TapMonitorBase.__init__')
    def monitor(self, mock_init, mock_config):
        """Create a KegtronPro instance with mocked dependencies"""
        mock_init.return_value = None
        monitor = KegtronPro.__new__(KegtronPro)
        monitor.config = mock_config
        monitor.logger = MagicMock()
        monitor.default_vol_unit = "L"
        monitor.kegtron_customer_api_key = "test_customer_key"
        monitor.kegtron_username = "test_user"
        monitor.kegtron_password = "test_pass"
        monitor._data_type_to_key = {
            "percent_beer_remaining": monitor._get_percent_remaining,
            "total_beer_remaining": monitor._get_total_remaining,
            "beer_remaining_unit": monitor._get_vol_unit,
        }
        return monitor

    def test_supports_discovery(self, monitor):
        """Test supports_discovery returns True"""
        assert monitor.supports_discovery() is True

    def test_supported_device_keys(self, monitor):
        """Test supported_device_keys has expected values"""
        assert "beaconEna" in KegtronPro.supported_device_keys
        assert "cleanEna" in KegtronPro.supported_device_keys

    def test_supported_port_keys(self, monitor):
        """Test supported_port_keys has expected values"""
        assert "abv" in KegtronPro.supported_port_keys
        assert "userName" in KegtronPro.supported_port_keys
        assert "volSize" in KegtronPro.supported_port_keys
        assert "style" in KegtronPro.supported_port_keys

    def test_get_device_access_token(self, monitor):
        """Test _get_device_access_token extracts token from meta"""
        meta = {"access_token": "my_token_123"}
        result = monitor._get_device_access_token(meta)
        assert result == "my_token_123"

    def test_get_vol_unit_from_meta(self, monitor):
        """Test _get_vol_unit returns unit from meta"""
        meta = {"unit": "gal"}
        result = run_async(monitor._get_vol_unit(meta))
        assert result == "gal"

    def test_get_vol_unit_default(self, monitor):
        """Test _get_vol_unit returns default when not in meta"""
        meta = {}
        result = run_async(monitor._get_vol_unit(meta))
        assert result == "l"

    def test_get_port_data(self, monitor):
        """Test _get_port_data extracts correct port"""
        device = {
            "ports": [
                {"num": 0, "data": "port0_data"},
                {"num": 1, "data": "port1_data"},
            ]
        }
        meta = {"port_num": 1}

        result = monitor._get_port_data(device, meta)

        assert result["data"] == "port1_data"

    def test_get_port_data_not_found(self, monitor):
        """Test _get_port_data returns empty dict when port not found"""
        device = {"ports": [{"num": 0}]}
        meta = {"port_num": 5}

        result = monitor._get_port_data(device, meta)

        assert result == {}

    def test_parse_resp(self, monitor):
        """Test parse_resp extracts data from API response"""
        api_response = {
            "id": "device123",
            "shadow": {
                "state": {
                    "reported": {
                        "online": True,
                        "ota": {"id": "ota123"},
                        "config": {
                            "siteName": "Test Site",
                            "beaconEna": True,
                            "cleanActive": False,
                            "port0": {"abv": 5.5, "style": "IPA"},
                        },
                        "config_readonly": {
                            "portCount": 1,
                            "fwRev": "1.2.3",
                            "serialNum": "SN123",
                            "macAddr": "AA:BB:CC:DD:EE:FF",
                            "port0": {"volSize": 20000, "volStart": 20000, "volDisp": 5000},
                        }
                    }
                }
            }
        }

        result = monitor.parse_resp(api_response)

        assert result["id"] == "device123"
        assert result["online"] is True
        assert result["site_name"] == "Test Site"
        assert result["fw_rev"] == "1.2.3"
        assert result["port_count"] == 1
        assert len(result["ports"]) == 1
        assert result["ports"][0]["num"] == 0
        assert result["ports"][0]["volSize"] == 20000

    @patch('lib.tap_monitors.kegtron.AsyncClient')
    def test_get_success(self, mock_async_client, monitor):
        """Test _get with successful response"""
        api_response = {
            "id": "dev1",
            "shadow": {
                "state": {
                    "reported": {
                        "online": True,
                        "ota": {},
                        "config": {"port0": {}},
                        "config_readonly": {"portCount": 1, "port0": {}},
                    }
                }
            }
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = api_response

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        meta = {"access_token": "token123"}
        result = run_async(monitor._get(meta))

        assert result["id"] == "dev1"

    @patch('lib.tap_monitors.kegtron.AsyncClient')
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

        meta = {"access_token": "bad_token"}
        with pytest.raises(TapMonitorDependencyError):
            run_async(monitor._get(meta))

    @patch('lib.tap_monitors.kegtron.AsyncClient')
    def test_get_percent_remaining(self, mock_async_client, monitor):
        """Test _get_percent_remaining calculates correctly"""
        api_response = {
            "id": "dev1",
            "shadow": {
                "state": {
                    "reported": {
                        "online": True,
                        "ota": {},
                        "config": {"port0": {}},
                        "config_readonly": {
                            "portCount": 1,
                            "port0": {"volSize": 20000, "volStart": 20000, "volDisp": 5000}
                        },
                    }
                }
            }
        }

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = api_response

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        meta = {"access_token": "token", "port_num": 0}
        result = run_async(monitor._get_percent_remaining(meta))

        # (20000 - 5000) / 20000 * 100 = 75%
        assert result == 75.0

    @patch('lib.tap_monitors.kegtron.AsyncClient')
    def test_discover_with_customer_api_key(self, mock_async_client, monitor):
        """Test discover uses customer API key"""
        # Customer API response
        customer_response = {"pubkeys": {"key1": "device1", "key2": "device2"}}

        # Device responses
        device_response = {
            "id": "dev1",
            "shadow": {
                "state": {
                    "reported": {
                        "online": True,
                        "ota": {},
                        "config": {"siteName": "Test Site", "port0": {}},
                        "config_readonly": {
                            "portCount": 1,
                            "modelNum": "KT-100",
                            "port0": {}
                        },
                    }
                }
            }
        }

        mock_response1 = MagicMock()
        mock_response1.status_code = 200
        mock_response1.json.return_value = customer_response

        mock_response2 = MagicMock()
        mock_response2.status_code = 200
        mock_response2.json.return_value = device_response

        mock_client = MagicMock()
        mock_client.get = AsyncMock(side_effect=[mock_response1, mock_response2, mock_response2])
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        result = run_async(monitor.discover())

        assert len(result) == 2
        assert result[0]["name"] == "Test Site"

    @patch('lib.tap_monitors.kegtron.AsyncClient')
    def test_discover_401_raises_dependency_error(self, mock_async_client, monitor):
        """Test discover raises TapMonitorDependencyError on 401"""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"error": "Unauthorized"}

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        with pytest.raises(TapMonitorDependencyError):
            run_async(monitor.discover())

    def test_get_no_args_raises(self, monitor):
        """Test get with no args raises exception"""
        with pytest.raises(Exception):
            run_async(monitor.get("percent_beer_remaining"))

    def test_update_device_no_args_raises(self, monitor):
        """Test update_device with no args raises exception"""
        with pytest.raises(Exception):
            run_async(monitor.update_device({}))

    def test_update_port_no_args_raises(self, monitor):
        """Test update_port with no args raises exception"""
        with pytest.raises(Exception):
            run_async(monitor.update_port(0, {}))
