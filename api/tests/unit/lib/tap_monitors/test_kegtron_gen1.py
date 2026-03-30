"""Tests for lib/tap_monitors/kegtron_gen1.py module"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from lib.tap_monitors.exceptions import TapMonitorDependencyError
from lib.tap_monitors.kegtron_gen1 import MONITOR_TYPE, KegtronGen1


# Helper to run async functions in sync tests
def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


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


class TestKegtronGen1Constants:
    """Tests for kegtron gen1 constants"""

    def test_monitor_type(self):
        assert MONITOR_TYPE == "kegtron-gen1"


class TestKegtronGen1Init:
    """Tests for KegtronGen1.__init__ when optional config keys are absent."""

    @patch("lib.tap_monitors.Config")
    def test_init_missing_api_key_sets_bearer_token_none(self, mock_config_class):
        cfg = MagicMock()
        cfg.get.side_effect = lambda key, default=None: {
            "tap_monitors.preferred_vol_unit": "gal",
            "tap_monitors.kegtron.gen1.base_url": "http://localhost:8080",
            "tap_monitors.kegtron.gen1.api_key": None,
            "tap_monitors.kegtron.gen1.insecure": False,
        }.get(key, default)
        mock_config_class.return_value = cfg
        kg = KegtronGen1()
        assert kg.bearer_token is None

    @patch("lib.tap_monitors.Config")
    def test_init_missing_base_url_with_insecure_true_does_not_crash(self, mock_config_class):
        cfg = MagicMock()
        cfg.get.side_effect = lambda key, default=None: {
            "tap_monitors.preferred_vol_unit": "gal",
            "tap_monitors.kegtron.gen1.base_url": None,
            "tap_monitors.kegtron.gen1.api_key": "k",
            "tap_monitors.kegtron.gen1.insecure": True,
        }.get(key, default)
        mock_config_class.return_value = cfg
        kg = KegtronGen1()
        assert kg.client_args == {}


class TestKegtronGen1:
    """Tests for KegtronGen1 class"""

    @pytest.fixture
    def mock_config(self):
        config = MagicMock()
        config.get.side_effect = lambda key, default=None: {
            "tap_monitors.preferred_vol_unit": "gal",
            "tap_monitors.kegtron.gen1.base_url": "http://localhost:8080",
            "tap_monitors.kegtron.gen1.api_key": "test_api_key",
            "tap_monitors.kegtron.gen1.insecure": False,
        }.get(key, default)
        return config

    @pytest.fixture
    @patch("lib.tap_monitors.kegtron_gen1.TapMonitorBase.__init__")
    def monitor(self, mock_init, mock_config):
        mock_init.return_value = None
        monitor = KegtronGen1.__new__(KegtronGen1)
        monitor.config = mock_config
        monitor.logger = MagicMock()
        monitor.default_vol_unit = "gal"
        monitor.base_url = "http://localhost:8080"
        monitor.bearer_token = "dGVzdF9hcGlfa2V5"
        monitor.insecure = False
        monitor.client_args = {}
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

    # ------------------------------------------------------------------
    # _calc_percent_remaining
    # ------------------------------------------------------------------

    def test_calc_percent_remaining(self, monitor):
        port = {"kegSize": 5.0, "startVolume": 5.0, "volumeDispensed": 1.0}
        result = monitor._calc_percent_remaining(port)
        assert result == 80.0

    def test_calc_percent_remaining_zero_keg_size(self, monitor):
        port = {"kegSize": 0, "startVolume": 0, "volumeDispensed": 0}
        result = monitor._calc_percent_remaining(port)
        assert result == 0.0

    def test_calc_percent_remaining_empty_port(self, monitor):
        result = monitor._calc_percent_remaining({})
        assert result == 0.0

    def test_calc_percent_remaining_full_keg(self, monitor):
        port = {"kegSize": 5.0, "startVolume": 5.0, "volumeDispensed": 0}
        result = monitor._calc_percent_remaining(port)
        assert result == 100.0

    def test_calc_percent_remaining_partial_start_volume(self, monitor):
        port = {"kegSize": 10.0, "startVolume": 8.0, "volumeDispensed": 2.0}
        result = monitor._calc_percent_remaining(port)
        assert result == 60.0

    # ------------------------------------------------------------------
    # _calc_total_remaining
    # ------------------------------------------------------------------

    def test_calc_total_remaining(self, monitor):
        port = {"startVolume": 5.0, "volumeDispensed": 1.5}
        result = monitor._calc_total_remaining(port)
        assert result == 3.5

    def test_calc_total_remaining_empty_port(self, monitor):
        result = monitor._calc_total_remaining({})
        assert result == 0.0

    def test_calc_total_remaining_nothing_dispensed(self, monitor):
        port = {"startVolume": 5.0, "volumeDispensed": 0}
        result = monitor._calc_total_remaining(port)
        assert result == 5.0

    # ------------------------------------------------------------------
    # _get_display_unit
    # ------------------------------------------------------------------

    def test_get_display_unit_from_port(self, monitor):
        port = {"displayUnit": "L"}
        result = monitor._get_display_unit(port)
        assert result == "l"

    def test_get_display_unit_default(self, monitor):
        result = monitor._get_display_unit({})
        assert result == "gal"

    def test_get_display_unit_no_default(self, monitor):
        monitor.default_vol_unit = None
        result = monitor._get_display_unit({})
        assert result == "gal"

    # ------------------------------------------------------------------
    # _get_port_data
    # ------------------------------------------------------------------

    def test_get_port_data(self, monitor):
        device = {"ports": {"0": {"kegSize": 5.0}, "1": {"kegSize": 10.0}}}
        result = monitor._get_port_data(device, {"port_index": 1})
        assert result["kegSize"] == 10.0

    def test_get_port_data_first_port(self, monitor):
        device = {"ports": {"0": {"kegSize": 5.0}}}
        result = monitor._get_port_data(device, {"port_index": 0})
        assert result["kegSize"] == 5.0

    def test_get_port_data_not_found(self, monitor):
        device = {"ports": {"0": {"kegSize": 5.0}}}
        result = monitor._get_port_data(device, {"port_index": 5})
        assert result == {}

    def test_get_port_data_empty_ports(self, monitor):
        device = {"ports": {}}
        result = monitor._get_port_data(device, {"port_index": 0})
        assert result == {}

    def test_get_port_data_no_ports_key(self, monitor):
        device = {}
        result = monitor._get_port_data(device, {"port_index": 0})
        assert result == {}

    # ------------------------------------------------------------------
    # is_online
    # ------------------------------------------------------------------

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_is_online_returns_true(self, mock_async_client, monitor):
        mock_client = _make_mock_http_client(mock_async_client, _make_mock_response(200, {"online": True}))
        result = run_async(monitor.is_online(meta={"device_id": "dev-1"}))
        assert result is True
        mock_client.get.assert_called_once()

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_is_online_returns_false(self, mock_async_client, monitor):
        _make_mock_http_client(mock_async_client, _make_mock_response(200, {"online": False}))
        result = run_async(monitor.is_online(meta={"device_id": "dev-1"}))
        assert result is False

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_is_online_defaults_to_false(self, mock_async_client, monitor):
        _make_mock_http_client(mock_async_client, _make_mock_response(200, {}))
        result = run_async(monitor.is_online(meta={"device_id": "dev-1"}))
        assert result is False

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_is_online_404_raises_dependency_error(self, mock_async_client, monitor):
        _make_mock_http_client(mock_async_client, _make_mock_response(404))
        with pytest.raises(TapMonitorDependencyError):
            run_async(monitor.is_online(meta={"device_id": "dev-1"}))

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_is_online_500_raises_dependency_error(self, mock_async_client, monitor):
        _make_mock_http_client(mock_async_client, _make_mock_response(500))
        with pytest.raises(TapMonitorDependencyError):
            run_async(monitor.is_online(meta={"device_id": "dev-1"}))

    def test_is_online_missing_base_url_raises(self, monitor):
        monitor.base_url = None
        with pytest.raises(TapMonitorDependencyError, match="base URL"):
            run_async(monitor.is_online(meta={"device_id": "dev-1"}))

    # ------------------------------------------------------------------
    # get
    # ------------------------------------------------------------------

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_get_percent_beer_remaining(self, mock_async_client, monitor):
        device_data = {"ports": {"0": {"kegSize": 5.0, "startVolume": 5.0, "volumeDispensed": 1.0}}}
        _make_mock_http_client(mock_async_client, _make_mock_response(200, device_data))
        result = run_async(monitor.get("percent_beer_remaining", meta={"device_id": "dev-1", "port_index": 0}))
        assert result == 80.0

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_get_total_beer_remaining(self, mock_async_client, monitor):
        device_data = {"ports": {"0": {"startVolume": 5.0, "volumeDispensed": 1.5}}}
        _make_mock_http_client(mock_async_client, _make_mock_response(200, device_data))
        result = run_async(monitor.get("total_beer_remaining", meta={"device_id": "dev-1", "port_index": 0}))
        assert result == 3.5

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_get_beer_remaining_unit(self, mock_async_client, monitor):
        device_data = {"ports": {"0": {"displayUnit": "L"}}}
        _make_mock_http_client(mock_async_client, _make_mock_response(200, device_data))
        result = run_async(monitor.get("beer_remaining_unit", meta={"device_id": "dev-1", "port_index": 0}))
        assert result == "l"

    def test_get_invalid_data_type(self, monitor):
        from lib.tap_monitors import InvalidDataType

        with pytest.raises(InvalidDataType):
            run_async(monitor.get("invalid_type", meta={"device_id": "dev-1", "port_index": 0}))

    # ------------------------------------------------------------------
    # get_all
    # ------------------------------------------------------------------

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_get_all(self, mock_async_client, monitor):
        device_data = {
            "ports": {
                "0": {
                    "kegSize": 5.0,
                    "startVolume": 5.0,
                    "volumeDispensed": 1.0,
                    "displayUnit": "GAL",
                }
            }
        }
        _make_mock_http_client(mock_async_client, _make_mock_response(200, device_data))
        result = run_async(monitor.get_all(meta={"device_id": "dev-1", "port_index": 0}))
        assert result["percentRemaining"] == 80.0
        assert result["totalVolumeRemaining"] == 4.0
        assert result["displayVolumeUnit"] == "gal"
        assert result["onlineStatusType"] == "async"

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_get_all_empty_port(self, mock_async_client, monitor):
        device_data = {"ports": {}}
        _make_mock_http_client(mock_async_client, _make_mock_response(200, device_data))
        result = run_async(monitor.get_all(meta={"device_id": "dev-1", "port_index": 0}))
        assert result["percentRemaining"] == 0.0
        assert result["totalVolumeRemaining"] == 0.0

    # ------------------------------------------------------------------
    # discover
    # ------------------------------------------------------------------

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_discover(self, mock_async_client, monitor):
        devices = [
            {"id": "dev-1", "name": "Device 1", "model": "KT-100", "ports": {"0": {}, "1": {}}},
            {"id": "dev-2", "name": "Device 2", "model": "KT-200", "ports": {"0": {}}},
        ]
        _make_mock_http_client(mock_async_client, _make_mock_response(200, devices))
        result = run_async(monitor.discover())
        assert len(result) == 3
        assert result[0]["id"] == "dev-1"
        assert result[0]["port_num"] == 0
        assert result[1]["id"] == "dev-1"
        assert result[1]["port_num"] == 1
        assert result[2]["id"] == "dev-2"
        assert result[2]["port_num"] == 0

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_discover_empty(self, mock_async_client, monitor):
        _make_mock_http_client(mock_async_client, _make_mock_response(200, []))
        result = run_async(monitor.discover())
        assert result == []

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_discover_missing_name_and_model(self, mock_async_client, monitor):
        devices = [{"id": "dev-1", "ports": {"0": {}}}]
        _make_mock_http_client(mock_async_client, _make_mock_response(200, devices))
        result = run_async(monitor.discover())
        assert result[0]["name"] == "Unknown"
        assert result[0]["model"] == "Unknown"

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_discover_api_error_raises(self, mock_async_client, monitor):
        _make_mock_http_client(mock_async_client, _make_mock_response(500))
        with pytest.raises(TapMonitorDependencyError):
            run_async(monitor.discover())

    # ------------------------------------------------------------------
    # reset_volume
    # ------------------------------------------------------------------

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_reset_volume_success(self, mock_async_client, monitor):
        mock_client = _make_mock_http_client(mock_async_client, _make_mock_response(200))
        result = run_async(monitor.reset_volume(5.0, 5.0, "gal", meta={"device_id": "dev-1", "port_index": 0}))
        assert result is True
        mock_client.post.assert_called_once()
        call_kwargs = mock_client.post.call_args
        assert "Authorization" in call_kwargs.kwargs.get("headers", call_kwargs[1].get("headers", {}))

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_reset_volume_sends_correct_payload(self, mock_async_client, monitor):
        mock_client = _make_mock_http_client(mock_async_client, _make_mock_response(200))
        run_async(monitor.reset_volume(5.0, 4.5, "l", meta={"device_id": "dev-1", "port_index": 1}))
        call_args = mock_client.post.call_args
        assert call_args[1]["json"] == {"kegSize": 5.0, "startVolume": 4.5, "unit": "l"}
        assert "dev-1" in call_args[0][0]
        assert "/port/1/" in call_args[0][0]

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_reset_volume_401_raises_dependency_error(self, mock_async_client, monitor):
        _make_mock_http_client(mock_async_client, _make_mock_response(401))
        with pytest.raises(TapMonitorDependencyError) as exc_info:
            run_async(monitor.reset_volume(5.0, 5.0, "gal", meta={"device_id": "dev-1", "port_index": 0}))
        assert "unauthorized" in str(exc_info.value).lower()

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_reset_volume_500_raises_dependency_error(self, mock_async_client, monitor):
        _make_mock_http_client(mock_async_client, _make_mock_response(500))
        with pytest.raises(TapMonitorDependencyError):
            run_async(monitor.reset_volume(5.0, 5.0, "gal", meta={"device_id": "dev-1", "port_index": 0}))

    def test_reset_volume_missing_device_id_raises(self, monitor):
        with pytest.raises(ValueError, match="device_id and port_index"):
            run_async(monitor.reset_volume(5.0, 5.0, "gal", meta={"port_index": 0}))

    def test_reset_volume_missing_port_index_raises(self, monitor):
        with pytest.raises(ValueError, match="device_id and port_index"):
            run_async(monitor.reset_volume(5.0, 5.0, "gal", meta={"device_id": "dev-1"}))

    def test_reset_volume_missing_api_key_raises(self, monitor):
        monitor.bearer_token = None
        with pytest.raises(TapMonitorDependencyError, match="API key"):
            run_async(monitor.reset_volume(5.0, 5.0, "gal", meta={"device_id": "dev-1", "port_index": 0}))

    # ------------------------------------------------------------------
    # _get_device
    # ------------------------------------------------------------------

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_get_device_success(self, mock_async_client, monitor):
        device_data = {"id": "dev-1", "ports": {"0": {}}}
        _make_mock_http_client(mock_async_client, _make_mock_response(200, device_data))
        result = run_async(monitor._get_device({"device_id": "dev-1"}))
        assert result["id"] == "dev-1"

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_get_device_404_raises(self, mock_async_client, monitor):
        _make_mock_http_client(mock_async_client, _make_mock_response(404))
        with pytest.raises(TapMonitorDependencyError) as exc_info:
            run_async(monitor._get_device({"device_id": "dev-1"}))
        assert "not found" in str(exc_info.value).lower()

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_get_device_500_raises(self, mock_async_client, monitor):
        _make_mock_http_client(mock_async_client, _make_mock_response(500))
        with pytest.raises(TapMonitorDependencyError):
            run_async(monitor._get_device({"device_id": "dev-1"}))

    # ------------------------------------------------------------------
    # _list_devices
    # ------------------------------------------------------------------

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_list_devices_success(self, mock_async_client, monitor):
        devices = [{"id": "dev-1"}, {"id": "dev-2"}]
        _make_mock_http_client(mock_async_client, _make_mock_response(200, devices))
        result = run_async(monitor._list_devices())
        assert len(result) == 2

    @patch("lib.tap_monitors.kegtron_gen1.AsyncClient")
    def test_list_devices_error_raises(self, mock_async_client, monitor):
        _make_mock_http_client(mock_async_client, _make_mock_response(500))
        with pytest.raises(TapMonitorDependencyError):
            run_async(monitor._list_devices())
