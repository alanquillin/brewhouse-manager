"""Tests for lib/tap_monitors/kegtron.py module"""

import asyncio
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lib.tap_monitors.exceptions import TapMonitorDependencyError
from lib.tap_monitors.kegtron import MONITOR_TYPE, KegtronPro

RESOURCES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "_resources")


# Helper to run async functions in sync tests
def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def _load_sample_json(filename):
    with open(os.path.join(RESOURCES_DIR, filename)) as f:
        return json.load(f)


def _make_mock_http_client(mock_async_client, response_or_responses):
    """Helper to wire up a mock AsyncClient with one or more responses."""
    if isinstance(response_or_responses, list):
        responses = response_or_responses
    else:
        responses = [response_or_responses]

    mock_client = MagicMock()
    mock_client.get = AsyncMock(side_effect=responses if len(responses) > 1 else responses * 1)
    mock_client.post = AsyncMock(side_effect=responses if len(responses) > 1 else responses * 1)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_async_client.return_value = mock_client
    return mock_client


def _make_mock_response(status_code=200, json_data=None):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    return resp


class TestKegtronConstants:
    """Tests for kegtron constants"""

    def test_monitor_type(self):
        assert MONITOR_TYPE == "kegtron-pro"


class TestKegtronPro:
    """Tests for KegtronPro class"""

    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {
            "tap_monitors.preferred_vol_unit": "L",
            "tap_monitors.kegtron.pro.auth.customer_api_key": "test_customer_key",
            "tap_monitors.kegtron.pro.auth.username": "test_user",
            "tap_monitors.kegtron.pro.auth.password": "test_pass",
        }.get(key, default)
        return config

    @pytest.fixture
    @patch("lib.tap_monitors.kegtron.TapMonitorBase.__init__")
    def monitor(self, mock_init, mock_config):
        mock_init.return_value = None
        monitor = KegtronPro.__new__(KegtronPro)
        monitor.config = mock_config
        monitor.logger = MagicMock()
        monitor.default_vol_unit = "L"
        monitor.kegtron_customer_api_key = "test_customer_key"
        monitor.kegtron_username = "test_user"
        monitor.kegtron_password = "test_pass"
        monitor.monitor_data_included = True
        monitor._data_type_to_key = {
            "percent_beer_remaining": monitor._get_percent_remaining,
            "total_beer_remaining": monitor._get_total_remaining,
            "beer_remaining_unit": monitor._get_vol_unit,
        }
        return monitor

    # ------------------------------------------------------------------
    # Static methods & class attributes
    # ------------------------------------------------------------------

    def test_supports_discovery(self, monitor):
        assert monitor.supports_discovery() is True

    def test_reports_online_status(self, monitor):
        assert monitor.reports_online_status() is True

    def test_monitor_data_included(self, monitor):
        assert monitor.monitor_data_included is True

    def test_supported_device_keys(self):
        assert "beaconEna" in KegtronPro.supported_device_keys
        assert "cleanEna" in KegtronPro.supported_device_keys
        assert len(KegtronPro.supported_device_keys) == 2

    def test_supported_port_keys(self):
        expected = {"abv", "beaconEna", "userName", "userDesc", "ibu", "maker", "style", "volSize"}
        assert set(KegtronPro.supported_port_keys) == expected

    # ------------------------------------------------------------------
    # _get_device_access_token
    # ------------------------------------------------------------------

    def test_get_device_access_token(self, monitor):
        assert monitor._get_device_access_token({"access_token": "my_token_123"}) == "my_token_123"

    def test_get_device_access_token_missing(self, monitor):
        assert monitor._get_device_access_token({}) is None

    # ------------------------------------------------------------------
    # _get_vol_unit
    # ------------------------------------------------------------------

    def test_get_vol_unit_from_meta(self, monitor):
        result = run_async(monitor._get_vol_unit({"unit": "GAL"}))
        assert result == "gal"

    def test_get_vol_unit_default(self, monitor):
        result = run_async(monitor._get_vol_unit({}))
        assert result == "l"

    # ------------------------------------------------------------------
    # _get_port_data
    # ------------------------------------------------------------------

    def test_get_port_data(self, monitor):
        device = {"ports": [{"num": 0, "data": "p0"}, {"num": 1, "data": "p1"}]}
        result = monitor._get_port_data(device, {"port_num": 1})
        assert result["data"] == "p1"

    def test_get_port_data_first_port(self, monitor):
        device = {"ports": [{"num": 0, "data": "p0"}, {"num": 1, "data": "p1"}]}
        result = monitor._get_port_data(device, {"port_num": 0})
        assert result["data"] == "p0"

    def test_get_port_data_not_found(self, monitor):
        device = {"ports": [{"num": 0}]}
        result = monitor._get_port_data(device, {"port_num": 5})
        assert result == {}

    def test_get_port_data_empty_ports(self, monitor):
        device = {"ports": []}
        result = monitor._get_port_data(device, {"port_num": 0})
        assert result == {}

    # ------------------------------------------------------------------
    # parse_resp – inline data
    # ------------------------------------------------------------------

    def test_parse_resp_basic(self, monitor):
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
                            "temp": 4.5,
                            "humidity": 55.0,
                            "hwRev": 20200101,
                            "modelNum": "KT-100",
                            "port0": {"volSize": 20000, "volStart": 20000, "volDisp": 5000},
                        },
                    }
                }
            },
        }

        result = monitor.parse_resp(api_response)

        assert result["id"] == "device123"
        assert result["online"] is True
        assert result["ota"] == "ota123"
        assert result["site_name"] == "Test Site"
        assert result["beacon_enabled"] is True
        assert result["fw_rev"] == "1.2.3"
        assert result["serial_num"] == "SN123"
        assert result["mac"] == "AA:BB:CC:DD:EE:FF"
        assert result["temp"] == 4.5
        assert result["humidity"] == 55.0
        assert result["hw_rev"] == 20200101
        assert result["model_num"] == "KT-100"
        assert result["port_count"] == 1
        assert len(result["ports"]) == 1
        assert result["ports"][0]["num"] == 0
        assert result["ports"][0]["key"] == "port0"
        assert result["ports"][0]["volSize"] == 20000
        assert result["ports"][0]["volStart"] == 20000
        assert result["ports"][0]["volDisp"] == 5000
        assert result["ports"][0]["abv"] == 5.5
        assert result["ports"][0]["style"] == "IPA"

    def test_parse_resp_offline_device(self, monitor):
        api_response = {
            "id": "offline1",
            "shadow": {
                "state": {
                    "reported": {
                        "online": False,
                        "ota": {},
                        "config": {"port0": {}},
                        "config_readonly": {"portCount": 1, "port0": {}},
                    }
                }
            },
        }

        result = monitor.parse_resp(api_response)
        assert result["online"] is False

    def test_parse_resp_missing_shadow(self, monitor):
        """parse_resp handles a response with no shadow key gracefully."""
        result = monitor.parse_resp({"id": "x"})
        assert result["id"] == "x"
        assert result["online"] is False
        assert result["port_count"] == 0
        assert result["ports"] == []

    def test_parse_resp_empty_reported(self, monitor):
        result = monitor.parse_resp({"id": "y", "shadow": {"state": {"reported": {}}}})
        assert result["port_count"] == 0
        assert result["ports"] == []

    # ------------------------------------------------------------------
    # parse_resp – using kegtron_pro_sample.json
    # ------------------------------------------------------------------

    def test_parse_resp_sample_device_fields(self, monitor):
        sample = _load_sample_json("kegtron_pro_sample.json")
        result = monitor.parse_resp(sample)

        assert result["id"] == "device2"
        assert result["online"] is True
        assert result["ota"] == "867a4c0e6e721e57"
        assert result["port_count"] == 4
        assert result["temp"] == 8.2346
        assert result["fw_rev"] == "20200507"
        assert result["humidity"] == 66.5665
        assert result["hw_rev"] == 20200101
        assert result["model_num"] == "KT-420"
        assert result["mac"] == "30AEA4426928"
        assert result["serial_num"] == "2001011234"
        assert result["site_name"] == "Moe's Tavern"
        assert result["beacon_enabled"] == 0

    def test_parse_resp_sample_port_count(self, monitor):
        sample = _load_sample_json("kegtron_pro_sample.json")
        result = monitor.parse_resp(sample)
        assert len(result["ports"]) == 4

    def test_parse_resp_sample_port0(self, monitor):
        sample = _load_sample_json("kegtron_pro_sample.json")
        port = monitor.parse_resp(sample)["ports"][0]

        assert port["num"] == 0
        assert port["key"] == "port0"
        # From config
        assert port["abv"] == 6
        assert port["ibu"] == 11
        assert port["userName"] == "King Cobra"
        assert port["userDesc"] == "Don't let the smooth taste fool ya"
        assert port["maker"] == "Anheuser-Busch"
        assert port["style"] == "Malt Liquor"
        assert port["volSize"] == 58670
        # From config_readonly
        assert port["volDisp"] == 6934
        assert port["volStart"] == 10376
        assert port["kegsServed"] == 1
        assert port["dateTapped"] == "2020/03/28"
        assert port["dateCleaned"] == "2020/03/01"

    def test_parse_resp_sample_port1(self, monitor):
        sample = _load_sample_json("kegtron_pro_sample.json")
        port = monitor.parse_resp(sample)["ports"][1]

        assert port["num"] == 1
        assert port["userName"] == "Old Milwaukee"
        assert port["maker"] == "Pabst Brewing"
        assert port["volSize"] == 58670
        assert port["volDisp"] == 15287
        assert port["volStart"] == 58670

    def test_parse_resp_sample_port2(self, monitor):
        sample = _load_sample_json("kegtron_pro_sample.json")
        port = monitor.parse_resp(sample)["ports"][2]

        assert port["num"] == 2
        assert port["userName"] == "Schlitz"
        assert port["volSize"] == 29340
        assert port["volDisp"] == 10650
        assert port["volStart"] == 29340

    def test_parse_resp_sample_port3(self, monitor):
        sample = _load_sample_json("kegtron_pro_sample.json")
        port = monitor.parse_resp(sample)["ports"][3]

        assert port["num"] == 3
        assert port["userName"] == "Olde English 800"
        assert port["maker"] == "Miller Brewing"
        assert port["volSize"] == 58670
        assert port["volDisp"] == 20481
        assert port["volStart"] == 58670

    def test_parse_resp_sample_port_config_overrides_readonly(self, monitor):
        """config is merged on top of config_readonly, so config values win for shared keys."""
        sample = _load_sample_json("kegtron_pro_sample.json")
        port0 = monitor.parse_resp(sample)["ports"][0]
        # volSize comes from config (58670), config_readonly has no volSize for port
        assert port0["volSize"] == 58670

    # ------------------------------------------------------------------
    # _get_served_data
    # ------------------------------------------------------------------

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_get_served_data(self, mock_async_client, monitor):
        sample = _load_sample_json("kegtron_pro_sample.json")
        resp = _make_mock_response(200, sample)
        _make_mock_http_client(mock_async_client, resp)

        meta = {"access_token": "tok", "port_num": 0}
        _max, start, disp = run_async(monitor._get_served_data(meta))

        assert _max == 58670
        assert start == 10376
        assert disp == 6934

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_get_served_data_port1(self, mock_async_client, monitor):
        sample = _load_sample_json("kegtron_pro_sample.json")
        resp = _make_mock_response(200, sample)
        _make_mock_http_client(mock_async_client, resp)

        meta = {"access_token": "tok", "port_num": 1}
        _max, start, disp = run_async(monitor._get_served_data(meta))

        assert _max == 58670
        assert start == 58670
        assert disp == 15287

    def test_get_served_data_with_device(self, monitor):
        """_get_served_data can use a pre-fetched device without calling the API."""
        sample = _load_sample_json("kegtron_pro_sample.json")
        device = monitor.parse_resp(sample)

        meta = {"port_num": 2}
        _max, start, disp = run_async(monitor._get_served_data(meta, device=device))

        assert _max == 29340
        assert start == 29340
        assert disp == 10650

    # ------------------------------------------------------------------
    # _get_percent_remaining
    # ------------------------------------------------------------------

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_get_percent_remaining(self, mock_async_client, monitor):
        api_response = {
            "id": "dev1",
            "shadow": {
                "state": {
                    "reported": {
                        "online": True,
                        "ota": {},
                        "config": {"port0": {}},
                        "config_readonly": {"portCount": 1, "port0": {"volSize": 20000, "volStart": 20000, "volDisp": 5000}},
                    }
                }
            },
        }
        resp = _make_mock_response(200, api_response)
        _make_mock_http_client(mock_async_client, resp)

        meta = {"access_token": "token", "port_num": 0}
        result = run_async(monitor._get_percent_remaining(meta))
        # (20000 - 5000) / 20000 * 100 = 75%
        assert result == 75.0

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_get_percent_remaining_sample_port0(self, mock_async_client, monitor):
        sample = _load_sample_json("kegtron_pro_sample.json")
        resp = _make_mock_response(200, sample)
        _make_mock_http_client(mock_async_client, resp)

        meta = {"access_token": "tok", "port_num": 0}
        result = run_async(monitor._get_percent_remaining(meta))
        # port0: volSize=58670, volStart=10376, volDisp=6934 => (10376-6934)/58670*100
        expected = round(((10376 - 6934) / 58670) * 100, 2)
        assert result == expected

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_get_percent_remaining_sample_port2(self, mock_async_client, monitor):
        sample = _load_sample_json("kegtron_pro_sample.json")
        resp = _make_mock_response(200, sample)
        _make_mock_http_client(mock_async_client, resp)

        meta = {"access_token": "tok", "port_num": 2}
        result = run_async(monitor._get_percent_remaining(meta))
        # port2: volSize=29340, volStart=29340, volDisp=10650 => (29340-10650)/29340*100
        expected = round(((29340 - 10650) / 29340) * 100, 2)
        assert result == expected

    # ------------------------------------------------------------------
    # _get_total_remaining
    # ------------------------------------------------------------------

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_get_total_remaining_liters(self, mock_async_client, monitor):
        sample = _load_sample_json("kegtron_pro_sample.json")
        resp = _make_mock_response(200, sample)
        _make_mock_http_client(mock_async_client, resp)

        meta = {"access_token": "tok", "port_num": 1, "unit": "L"}
        result = run_async(monitor._get_total_remaining(meta))
        # port1: volStart=58670, volDisp=15287 => remaining=43383 ml => /1000 = 43.383 L
        expected = (58670 - 15287) / 1000
        assert result == expected

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_get_total_remaining_gallons(self, mock_async_client, monitor):
        sample = _load_sample_json("kegtron_pro_sample.json")
        resp = _make_mock_response(200, sample)
        _make_mock_http_client(mock_async_client, resp)

        meta = {"access_token": "tok", "port_num": 1, "unit": "gal"}
        result = run_async(monitor._get_total_remaining(meta))
        remaining_ml = 58670 - 15287
        expected = remaining_ml * 0.0002641721
        assert abs(result - expected) < 0.001

    # ------------------------------------------------------------------
    # _get_from_key
    # ------------------------------------------------------------------

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_get_from_key(self, mock_async_client, monitor):
        sample = _load_sample_json("kegtron_pro_sample.json")
        resp = _make_mock_response(200, sample)
        _make_mock_http_client(mock_async_client, resp)

        meta = {"access_token": "tok", "port_num": 0}
        result = run_async(monitor._get_from_key("userName", meta))
        assert result == "King Cobra"

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_get_from_key_missing(self, mock_async_client, monitor):
        sample = _load_sample_json("kegtron_pro_sample.json")
        resp = _make_mock_response(200, sample)
        _make_mock_http_client(mock_async_client, resp)

        meta = {"access_token": "tok", "port_num": 0}
        result = run_async(monitor._get_from_key("nonexistentKey", meta))
        assert result is None

    # ------------------------------------------------------------------
    # _get (HTTP layer)
    # ------------------------------------------------------------------

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_get_success(self, mock_async_client, monitor):
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
            },
        }
        resp = _make_mock_response(200, api_response)
        mock_client = _make_mock_http_client(mock_async_client, resp)

        meta = {"access_token": "token123"}
        result = run_async(monitor._get(meta))

        assert result["id"] == "dev1"
        mock_client.get.assert_called_once()
        call_kwargs = mock_client.get.call_args
        assert call_kwargs.kwargs["params"]["access_token"] == "token123"

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_get_passes_extra_params(self, mock_async_client, monitor):
        api_response = {
            "id": "dev1",
            "shadow": {"state": {"reported": {"ota": {}, "config": {"port0": {}}, "config_readonly": {"portCount": 1, "port0": {}}}}},
        }
        resp = _make_mock_response(200, api_response)
        mock_client = _make_mock_http_client(mock_async_client, resp)

        meta = {"access_token": "tok"}
        run_async(monitor._get(meta, params={"extra": "val"}))

        call_kwargs = mock_client.get.call_args
        assert call_kwargs.kwargs["params"]["extra"] == "val"
        assert call_kwargs.kwargs["params"]["access_token"] == "tok"

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_get_401_raises_dependency_error(self, mock_async_client, monitor):
        resp = _make_mock_response(401, {"error": "Unauthorized"})
        _make_mock_http_client(mock_async_client, resp)

        with pytest.raises(TapMonitorDependencyError):
            run_async(monitor._get({"access_token": "bad_token"}))

    # ------------------------------------------------------------------
    # is_online
    # ------------------------------------------------------------------

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_is_online_true(self, mock_async_client, monitor):
        sample = _load_sample_json("kegtron_pro_sample.json")
        resp = _make_mock_response(200, sample)
        _make_mock_http_client(mock_async_client, resp)

        meta = {"access_token": "tok", "port_num": 0}
        result = run_async(monitor.is_online(meta=meta))
        assert result is True

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_is_online_false(self, mock_async_client, monitor):
        offline_resp = {
            "id": "dev1",
            "shadow": {"state": {"reported": {"online": False, "ota": {}, "config": {"port0": {}}, "config_readonly": {"portCount": 1, "port0": {}}}}},
        }
        resp = _make_mock_response(200, offline_resp)
        _make_mock_http_client(mock_async_client, resp)

        meta = {"access_token": "tok", "port_num": 0}
        result = run_async(monitor.is_online(meta=meta))
        assert result is False

    def test_is_online_with_prefetched_device(self, monitor):
        device = {"online": True}
        result = run_async(monitor.is_online(meta={"access_token": "x"}, device=device))
        assert result is True

    def test_is_online_with_prefetched_device_false(self, monitor):
        device = {"online": False}
        result = run_async(monitor.is_online(meta={"access_token": "x"}, device=device))
        assert result is False

    def test_is_online_with_prefetched_device_missing_key(self, monitor):
        device = {"some_other_key": "val"}
        result = run_async(monitor.is_online(meta={"access_token": "x"}, device=device))
        assert result is False

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_is_online_no_device_returns_false(self, mock_async_client, monitor):
        """When _get returns None, is_online returns False."""
        resp = _make_mock_response(200, None)
        mock_client = _make_mock_http_client(mock_async_client, resp)
        # Make _get return None by patching parse_resp
        monitor.parse_resp = MagicMock(return_value=None)

        meta = {"access_token": "tok"}
        result = run_async(monitor.is_online(meta=meta))
        assert result is False

    def test_is_online_no_args_raises(self, monitor):
        with pytest.raises(Exception, match="monitor_id, monitor, or meta must be provided"):
            run_async(monitor.is_online())

    def test_is_online_with_monitor_object(self, monitor):
        mock_monitor = MagicMock()
        mock_monitor.meta = {"access_token": "x"}
        device = {"online": True}
        result = run_async(monitor.is_online(monitor=mock_monitor, device=device))
        assert result is True

    # ------------------------------------------------------------------
    # get
    # ------------------------------------------------------------------

    def test_get_no_args_raises(self, monitor):
        with pytest.raises(Exception, match="monitor_id, monitor, or meta must be provided"):
            run_async(monitor.get("percent_beer_remaining"))

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_get_percent_remaining_via_get(self, mock_async_client, monitor):
        api_response = {
            "id": "dev1",
            "shadow": {
                "state": {
                    "reported": {
                        "online": True,
                        "ota": {},
                        "config": {"port0": {}},
                        "config_readonly": {"portCount": 1, "port0": {"volSize": 10000, "volStart": 10000, "volDisp": 2500}},
                    }
                }
            },
        }
        resp = _make_mock_response(200, api_response)
        _make_mock_http_client(mock_async_client, resp)

        meta = {"access_token": "tok", "port_num": 0}
        result = run_async(monitor.get("percent_beer_remaining", meta=meta))
        assert result == 75.0

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_get_vol_unit_via_get(self, mock_async_client, monitor):
        meta = {"access_token": "tok", "port_num": 0, "unit": "oz"}
        result = run_async(monitor.get("beer_remaining_unit", meta=meta))
        assert result == "oz"

    def test_get_with_monitor_object(self, monitor):
        mock_mon = MagicMock()
        mock_mon.meta = {"access_token": "tok", "port_num": 0, "unit": "gal"}
        result = run_async(monitor.get("beer_remaining_unit", monitor=mock_mon))
        assert result == "gal"

    # ------------------------------------------------------------------
    # get_all
    # ------------------------------------------------------------------

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_get_all(self, mock_async_client, monitor):
        sample = _load_sample_json("kegtron_pro_sample.json")
        resp1 = _make_mock_response(200, sample)
        resp2 = _make_mock_response(200, sample)
        _make_mock_http_client(mock_async_client, [resp1, resp2])

        meta = {"access_token": "tok", "port_num": 1, "unit": "L"}
        result = run_async(monitor.get_all(meta=meta))

        assert "percentRemaining" in result
        assert "totalVolumeRemaining" in result
        assert "displayVolumeUnit" in result
        assert "online" in result
        assert result["online"] is True

    def test_get_all_no_args_raises(self, monitor):
        with pytest.raises(Exception, match="monitor_id, monitor, or meta must be provided"):
            run_async(monitor.get_all())

    # ------------------------------------------------------------------
    # discover
    # ------------------------------------------------------------------

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_discover_with_customer_api_key(self, mock_async_client, monitor):
        customer_response = {"pubkeys": {"key1": "device1", "key2": "device2"}}
        device_response = {
            "id": "dev1",
            "shadow": {
                "state": {
                    "reported": {
                        "online": True,
                        "ota": {},
                        "config": {"siteName": "Test Site", "port0": {}},
                        "config_readonly": {"portCount": 1, "modelNum": "KT-100", "port0": {}},
                    }
                }
            },
        }

        resp_customer = _make_mock_response(200, customer_response)
        resp_device = _make_mock_response(200, device_response)
        _make_mock_http_client(mock_async_client, [resp_customer, resp_device, resp_device])

        result = run_async(monitor.discover())
        assert len(result) == 2
        assert result[0]["name"] == "Test Site"
        assert result[0]["model"] == "KT-100"
        assert result[0]["id"] == "dev1"

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_discover_with_username_password(self, mock_async_client, monitor):
        """When no customer API key is set, discover falls back to basic auth."""
        monitor.kegtron_customer_api_key = None

        customer_response = {"pubkeys": {"key1": "device1"}}
        device_response = {
            "id": "dev1",
            "shadow": {
                "state": {
                    "reported": {
                        "online": True,
                        "ota": {},
                        "config": {"siteName": "My Bar", "port0": {}},
                        "config_readonly": {"portCount": 1, "modelNum": "KT-200", "port0": {}},
                    }
                }
            },
        }

        resp_customer = _make_mock_response(200, customer_response)
        resp_device = _make_mock_response(200, device_response)
        mock_client = _make_mock_http_client(mock_async_client, [resp_customer, resp_device])

        result = run_async(monitor.discover())

        assert len(result) == 1
        assert result[0]["name"] == "My Bar"
        # Verify basic auth was used on the customer call
        first_call_kwargs = mock_client.get.call_args_list[0].kwargs
        assert "auth" in first_call_kwargs

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_discover_multi_port_device(self, mock_async_client, monitor):
        """Discover returns an entry per port on multi-port devices."""
        customer_response = {"pubkeys": {"key1": "device1"}}
        device_response = {
            "id": "dev1",
            "shadow": {
                "state": {
                    "reported": {
                        "online": True,
                        "ota": {},
                        "config": {"siteName": "Multi Tap", "port0": {}, "port1": {}},
                        "config_readonly": {"portCount": 2, "modelNum": "KT-420", "port0": {}, "port1": {}},
                    }
                }
            },
        }

        resp_customer = _make_mock_response(200, customer_response)
        resp_device = _make_mock_response(200, device_response)
        _make_mock_http_client(mock_async_client, [resp_customer, resp_device])

        result = run_async(monitor.discover())
        assert len(result) == 2
        assert result[0]["port_num"] == 0
        assert result[1]["port_num"] == 1
        assert result[0]["token"] == "key1"
        assert result[1]["token"] == "key1"

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_discover_401_raises_dependency_error(self, mock_async_client, monitor):
        resp = _make_mock_response(401, {"error": "Unauthorized"})
        _make_mock_http_client(mock_async_client, resp)

        with pytest.raises(TapMonitorDependencyError):
            run_async(monitor.discover())

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_discover_empty_pubkeys(self, mock_async_client, monitor):
        resp = _make_mock_response(200, {"pubkeys": {}})
        _make_mock_http_client(mock_async_client, resp)

        result = run_async(monitor.discover())
        assert result == []

    # ------------------------------------------------------------------
    # update_device
    # ------------------------------------------------------------------

    def test_update_device_no_args_raises(self, monitor):
        with pytest.raises(ValueError, match="monitor_id, monitor, or meta must be provided"):
            run_async(monitor.update_device({}))

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_update_device_filters_unsupported_keys(self, mock_async_client, monitor):
        resp = _make_mock_response(200)
        mock_client = _make_mock_http_client(mock_async_client, resp)

        meta = {"access_token": "tok"}
        data = {"beaconEna": True, "unsupportedKey": "val", "cleanEna": False}
        result = run_async(monitor.update_device(data, meta=meta))

        assert result is True
        posted_data = mock_client.post.call_args.kwargs["json"]
        desired_config = posted_data["shadow"]["state"]["desired"]["config"]
        assert desired_config == {"beaconEna": True, "cleanEna": False}
        assert "unsupportedKey" not in desired_config

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_update_device_with_monitor_object(self, mock_async_client, monitor):
        resp = _make_mock_response(200)
        _make_mock_http_client(mock_async_client, resp)

        mock_mon = MagicMock()
        mock_mon.meta = {"access_token": "tok"}
        result = run_async(monitor.update_device({"beaconEna": True}, monitor=mock_mon))
        assert result is True

    # ------------------------------------------------------------------
    # update_port
    # ------------------------------------------------------------------

    def test_update_port_no_args_raises(self, monitor):
        with pytest.raises(ValueError, match="monitor_id, monitor, or meta must be provided"):
            run_async(monitor.update_port(0, {}))

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_update_port_filters_unsupported_keys(self, mock_async_client, monitor):
        resp = _make_mock_response(200)
        mock_client = _make_mock_http_client(mock_async_client, resp)

        meta = {"access_token": "tok", "port_num": 2}
        data = {"userName": "New IPA", "abv": 7.5, "badKey": "nope"}
        result = run_async(monitor.update_port(2, data, meta=meta))

        assert result is True
        posted_data = mock_client.post.call_args.kwargs["json"]
        desired_port = posted_data["shadow"]["state"]["desired"]["config"]["port2"]
        assert desired_port == {"userName": "New IPA", "abv": 7.5}
        assert "badKey" not in desired_port

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_update_port_missing_port_num_in_meta_raises(self, mock_async_client, monitor):
        meta = {"access_token": "tok"}
        with pytest.raises(ValueError, match="port_num not found"):
            run_async(monitor.update_port(0, {"abv": 5}, meta=meta))

    # ------------------------------------------------------------------
    # _update
    # ------------------------------------------------------------------

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_update_returns_false_on_non_200(self, mock_async_client, monitor):
        resp = _make_mock_response(500)
        _make_mock_http_client(mock_async_client, resp)

        meta = {"access_token": "tok"}
        result = run_async(monitor._update({"some": "data"}, meta))
        assert result is False

    @patch("lib.tap_monitors.kegtron.AsyncClient")
    def test_update_sends_access_token(self, mock_async_client, monitor):
        resp = _make_mock_response(200)
        mock_client = _make_mock_http_client(mock_async_client, resp)

        meta = {"access_token": "my_token"}
        run_async(monitor._update({"d": 1}, meta))

        call_kwargs = mock_client.post.call_args.kwargs
        assert call_kwargs["params"]["access_token"] == "my_token"
