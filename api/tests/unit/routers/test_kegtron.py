"""Tests for routers/kegtron.py module - Kegtron Device Management router"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestGetBeerData:
    """Tests for get_beer_data helper"""

    def test_returns_value_from_batch_ext_details(self):
        from routers.kegtron import get_beer_data

        batch_d = {"external_brewing_tool_meta": {"details": {"abv": 5.5}}}
        beer_d = {}
        assert get_beer_data(batch_d, beer_d, "abv") == 5.5

    def test_falls_back_to_beer_ext_details(self):
        from routers.kegtron import get_beer_data

        batch_d = {"external_brewing_tool_meta": {"details": {}}}
        beer_d = {"external_brewing_tool_meta": {"details": {"abv": 6.2}}}
        assert get_beer_data(batch_d, beer_d, "abv") == 6.2

    def test_returns_none_when_not_found(self):
        from routers.kegtron import get_beer_data

        batch_d = {}
        beer_d = {}
        assert get_beer_data(batch_d, beer_d, "abv") is None

    def test_handles_none_external_brewing_tool_meta_on_batch(self):
        from routers.kegtron import get_beer_data

        batch_d = {"external_brewing_tool_meta": None}
        beer_d = {"external_brewing_tool_meta": {"details": {"style": "IPA"}}}
        assert get_beer_data(batch_d, beer_d, "style") == "IPA"

    def test_handles_none_external_brewing_tool_meta_on_beer(self):
        from routers.kegtron import get_beer_data

        batch_d = {}
        beer_d = {"external_brewing_tool_meta": None}
        assert get_beer_data(batch_d, beer_d, "abv") is None

    def test_handles_missing_details_key(self):
        from routers.kegtron import get_beer_data

        batch_d = {"external_brewing_tool_meta": {}}
        beer_d = {"external_brewing_tool_meta": {}}
        assert get_beer_data(batch_d, beer_d, "ibu") is None

    def test_prefers_batch_ext_details_over_beer(self):
        from routers.kegtron import get_beer_data

        batch_d = {"external_brewing_tool_meta": {"details": {"abv": 5.0}}}
        beer_d = {"external_brewing_tool_meta": {"details": {"abv": 7.0}}}
        assert get_beer_data(batch_d, beer_d, "abv") == 5.0


class TestGetMonitorFromDeviceAndPort:
    """Tests for get_monitor_from_device_and_port helper"""

    def test_returns_matching_monitor(self):
        from routers.kegtron import get_monitor_from_device_and_port

        mock_monitor = MagicMock()
        mock_monitor.meta = {"device_id": "dev-1", "port_num": 0}

        mock_session = AsyncMock()
        with patch("routers.kegtron.TapMonitorsDB") as mock_db:
            mock_db.query = AsyncMock(return_value=[mock_monitor])
            result = run_async(get_monitor_from_device_and_port("dev-1", 0, mock_session))

        assert result == mock_monitor

    def test_raises_404_when_no_monitor_found(self):
        from routers.kegtron import get_monitor_from_device_and_port

        mock_session = AsyncMock()
        with patch("routers.kegtron.TapMonitorsDB") as mock_db:
            mock_db.query = AsyncMock(return_value=[])
            with pytest.raises(HTTPException) as exc_info:
                run_async(get_monitor_from_device_and_port("nonexistent", 0, mock_session))

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    def test_raises_404_when_port_num_does_not_match(self):
        from routers.kegtron import get_monitor_from_device_and_port

        mock_monitor = MagicMock()
        mock_monitor.meta = {"device_id": "dev-1", "port_num": 1}

        mock_session = AsyncMock()
        with patch("routers.kegtron.TapMonitorsDB") as mock_db:
            mock_db.query = AsyncMock(return_value=[mock_monitor])
            with pytest.raises(HTTPException) as exc_info:
                run_async(get_monitor_from_device_and_port("dev-1", 0, mock_session))

        assert exc_info.value.status_code == 404


class TestResetPort:
    """Tests for reset_port endpoint"""

    def _create_mock_request(self, query_params=None):
        mock_request = MagicMock()
        mock_request.query_params = query_params or {}
        return mock_request

    def test_rejects_invalid_volume_unit(self):
        from routers.kegtron import ResetPortRequest, reset_port

        request_data = ResetPortRequest(volume_size=5.0, volume_unit="invalid")
        mock_request = self._create_mock_request()
        mock_user = MagicMock()
        mock_session = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            run_async(reset_port("dev-1", 0, request_data, mock_request, mock_user, mock_session))

        assert exc_info.value.status_code == 400
        assert "Invalid volume unit" in exc_info.value.detail

    def test_rejects_empty_volume_unit(self):
        from routers.kegtron import ResetPortRequest, reset_port

        request_data = ResetPortRequest(volume_size=5.0, volume_unit="")
        mock_request = self._create_mock_request()
        mock_user = MagicMock()
        mock_session = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            run_async(reset_port("dev-1", 0, request_data, mock_request, mock_user, mock_session))

        assert exc_info.value.status_code == 400

    def test_raises_400_when_kegtron_lib_not_enabled(self):
        from routers.kegtron import ResetPortRequest, reset_port

        request_data = ResetPortRequest(volume_size=5.0, volume_unit="gal")
        mock_request = self._create_mock_request()
        mock_user = MagicMock()
        mock_session = AsyncMock()

        with patch("routers.kegtron.get_tap_monitor_lib", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                run_async(reset_port("dev-1", 0, request_data, mock_request, mock_user, mock_session))

        assert exc_info.value.status_code == 400
        assert "not enabled" in exc_info.value.detail.lower()

    def test_successful_reset_returns_true(self):
        from routers.kegtron import ResetPortRequest, reset_port

        request_data = ResetPortRequest(volume_size=5.0, volume_unit="gal")
        mock_request = self._create_mock_request()
        mock_user = MagicMock()
        mock_session = AsyncMock()

        mock_monitor = MagicMock()
        mock_monitor.meta = {"device_id": "dev-1", "port_num": 0}

        mock_lib = MagicMock()
        mock_lib.update_user_overrides = AsyncMock(return_value=True)
        mock_lib.reset_volume = AsyncMock(return_value=True)
        mock_lib.reset_kegs_served = AsyncMock(return_value=True)

        with (
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
        ):
            result = run_async(reset_port("dev-1", 0, request_data, mock_request, mock_user, mock_session))

        assert result is True

    def test_calls_update_user_overrides_with_vol_start(self):
        from routers.kegtron import ResetPortRequest, reset_port

        request_data = ResetPortRequest(volume_size=5.0, volume_unit="gal")
        mock_request = self._create_mock_request()
        mock_user = MagicMock()
        mock_session = AsyncMock()

        mock_monitor = MagicMock()
        mock_monitor.meta = {"device_id": "dev-1", "port_num": 0}

        mock_lib = MagicMock()
        mock_lib.update_user_overrides = AsyncMock(return_value=True)
        mock_lib.reset_volume = AsyncMock(return_value=True)
        mock_lib.reset_kegs_served = AsyncMock(return_value=True)

        with (
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
            patch("routers.kegtron.to_ml", return_value=18927.0),
        ):
            run_async(reset_port("dev-1", 0, request_data, mock_request, mock_user, mock_session))

        call_args = mock_lib.update_user_overrides.call_args
        assert call_args[0][0]["volStart"] == 18927
        assert call_args[1]["meta"] == mock_monitor.meta

    def test_includes_date_tapped_when_update_date_tapped_is_true(self):
        from routers.kegtron import ResetPortRequest, reset_port

        request_data = ResetPortRequest(volume_size=5.0, volume_unit="gal")
        mock_request = self._create_mock_request({"update_date_tapped": "true"})
        mock_user = MagicMock()
        mock_session = AsyncMock()

        mock_monitor = MagicMock()
        mock_monitor.meta = {"device_id": "dev-1", "port_num": 0}

        mock_lib = MagicMock()
        mock_lib.update_user_overrides = AsyncMock(return_value=True)
        mock_lib.reset_volume = AsyncMock(return_value=True)
        mock_lib.reset_kegs_served = AsyncMock(return_value=True)

        with (
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
        ):
            run_async(reset_port("dev-1", 0, request_data, mock_request, mock_user, mock_session))

        call_args = mock_lib.update_user_overrides.call_args
        assert "dateTapped" in call_args[0][0]

    def test_does_not_include_date_tapped_when_false(self):
        from routers.kegtron import ResetPortRequest, reset_port

        request_data = ResetPortRequest(volume_size=5.0, volume_unit="gal")
        mock_request = self._create_mock_request({"update_date_tapped": "false"})
        mock_user = MagicMock()
        mock_session = AsyncMock()

        mock_monitor = MagicMock()
        mock_monitor.meta = {"device_id": "dev-1", "port_num": 0}

        mock_lib = MagicMock()
        mock_lib.update_user_overrides = AsyncMock(return_value=True)
        mock_lib.reset_volume = AsyncMock(return_value=True)
        mock_lib.reset_kegs_served = AsyncMock(return_value=True)

        with (
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
        ):
            run_async(reset_port("dev-1", 0, request_data, mock_request, mock_user, mock_session))

        call_args = mock_lib.update_user_overrides.call_args
        assert "dateTapped" not in call_args[0][0]

    def test_raises_502_when_device_update_fails(self):
        from routers.kegtron import ResetPortRequest, reset_port

        request_data = ResetPortRequest(volume_size=5.0, volume_unit="gal")
        mock_request = self._create_mock_request()
        mock_user = MagicMock()
        mock_session = AsyncMock()

        mock_monitor = MagicMock()
        mock_monitor.meta = {"device_id": "dev-1", "port_num": 0}

        mock_lib = MagicMock()
        mock_lib.update_user_overrides = AsyncMock(return_value=False)
        mock_lib.reset_volume = AsyncMock(return_value=True)
        mock_lib.reset_kegs_served = AsyncMock(return_value=True)

        with (
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
        ):
            with pytest.raises(HTTPException) as exc_info:
                run_async(reset_port("dev-1", 0, request_data, mock_request, mock_user, mock_session))

        assert exc_info.value.status_code == 502

    def test_raises_400_for_nonexistent_batch(self):
        from routers.kegtron import ResetPortRequest, reset_port

        request_data = ResetPortRequest(volume_size=5.0, volume_unit="gal", batch_id="missing-batch")
        mock_request = self._create_mock_request()
        mock_user = MagicMock()
        mock_session = AsyncMock()

        mock_monitor = MagicMock()
        mock_monitor.meta = {"device_id": "dev-1", "port_num": 0}

        mock_lib = MagicMock()
        mock_lib.update_user_overrides = AsyncMock(return_value=True)
        mock_lib.reset_volume = AsyncMock(return_value=True)
        mock_lib.reset_kegs_served = AsyncMock(return_value=True)

        with (
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
            patch("routers.kegtron.BatchesDB") as mock_batches_db,
        ):
            mock_batches_db.get_by_pkey = AsyncMock(return_value=None)
            with pytest.raises(HTTPException) as exc_info:
                run_async(reset_port("dev-1", 0, request_data, mock_request, mock_user, mock_session))

        assert exc_info.value.status_code == 400
        assert "not found" in exc_info.value.detail.lower()

    def test_sends_beer_data_to_update_port_when_batch_has_beer(self):
        from routers.kegtron import ResetPortRequest, reset_port

        request_data = ResetPortRequest(volume_size=5.0, volume_unit="gal", batch_id="batch-1")
        mock_request = self._create_mock_request()
        mock_user = MagicMock()
        mock_session = AsyncMock()

        mock_monitor = MagicMock()
        mock_monitor.meta = {"device_id": "dev-1", "port_num": 0}

        mock_beer = MagicMock()
        mock_beer.to_dict.return_value = {
            "name": "Test IPA",
            "external_brewing_tool_meta": {"details": {"abv": 6.5, "ibu": 55}},
        }

        mock_batch = MagicMock()
        mock_batch.beer_id = "beer-1"
        mock_batch.beverage_id = None
        mock_batch.beer = mock_beer
        mock_batch.awaitable_attrs = MagicMock()
        mock_batch.awaitable_attrs.beer = AsyncMock(return_value=mock_beer)()
        mock_batch.to_dict.return_value = {
            "name": "Batch 1",
            "external_brewing_tool_meta": {"details": {}},
        }

        mock_lib = MagicMock()
        mock_lib.update_user_overrides = AsyncMock(return_value=True)
        mock_lib.reset_volume = AsyncMock(return_value=True)
        mock_lib.reset_kegs_served = AsyncMock(return_value=True)
        mock_lib.update_port = AsyncMock(return_value=True)

        with (
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
            patch("routers.kegtron.BatchesDB") as mock_batches_db,
        ):
            mock_batches_db.get_by_pkey = AsyncMock(return_value=mock_batch)
            run_async(reset_port("dev-1", 0, request_data, mock_request, mock_user, mock_session))

        mock_lib.update_port.assert_called_once()
        port_data = mock_lib.update_port.call_args[0][0]
        assert port_data["abv"] == 6.5
        assert port_data["ibu"] == 55

    def test_sends_beverage_data_to_update_port_when_batch_has_beverage(self):
        from routers.kegtron import ResetPortRequest, reset_port

        request_data = ResetPortRequest(volume_size=5.0, volume_unit="gal", batch_id="batch-2")
        mock_request = self._create_mock_request()
        mock_user = MagicMock()
        mock_session = AsyncMock()

        mock_monitor = MagicMock()
        mock_monitor.meta = {"device_id": "dev-1", "port_num": 0}

        mock_beverage = MagicMock()
        mock_beverage.type = "cold-brew"
        mock_beverage.description = "Test Coffee"
        mock_beverage.name = "Cold Brew"
        mock_beverage.img_url = "http://example.com/coffee.png"

        mock_batch = MagicMock()
        mock_batch.beer_id = None
        mock_batch.beverage_id = "bev-1"
        mock_batch.beverage = mock_beverage
        mock_batch.img_url = None
        mock_batch.awaitable_attrs = MagicMock()
        mock_batch.awaitable_attrs.beverage = AsyncMock(return_value=mock_beverage)()

        mock_lib = MagicMock()
        mock_lib.update_user_overrides = AsyncMock(return_value=True)
        mock_lib.reset_volume = AsyncMock(return_value=True)
        mock_lib.reset_kegs_served = AsyncMock(return_value=True)
        mock_lib.update_port = AsyncMock(return_value=True)

        with (
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
            patch("routers.kegtron.BatchesDB") as mock_batches_db,
        ):
            mock_batches_db.get_by_pkey = AsyncMock(return_value=mock_batch)
            run_async(reset_port("dev-1", 0, request_data, mock_request, mock_user, mock_session))

        mock_lib.update_port.assert_called_once()
        port_data = mock_lib.update_port.call_args[0][0]
        assert port_data["abv"] == 0.0
        assert port_data["srm"] == 40
        assert port_data["userName"] == "Cold Brew"
        assert port_data["style"] == "cold-brew"

    def test_does_not_call_update_port_when_no_batch(self):
        from routers.kegtron import ResetPortRequest, reset_port

        request_data = ResetPortRequest(volume_size=5.0, volume_unit="gal")
        mock_request = self._create_mock_request()
        mock_user = MagicMock()
        mock_session = AsyncMock()

        mock_monitor = MagicMock()
        mock_monitor.meta = {"device_id": "dev-1", "port_num": 0}

        mock_lib = MagicMock()
        mock_lib.update_user_overrides = AsyncMock(return_value=True)
        mock_lib.reset_volume = AsyncMock(return_value=True)
        mock_lib.reset_kegs_served = AsyncMock(return_value=True)
        mock_lib.update_port = AsyncMock(return_value=True)

        with (
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
        ):
            run_async(reset_port("dev-1", 0, request_data, mock_request, mock_user, mock_session))

        mock_lib.update_port.assert_not_called()

    def test_accepts_gal_volume_unit(self):
        from routers.kegtron import ResetPortRequest, reset_port

        request_data = ResetPortRequest(volume_size=5.0, volume_unit="gal")
        mock_request = self._create_mock_request()
        mock_user = MagicMock()
        mock_session = AsyncMock()

        mock_monitor = MagicMock()
        mock_monitor.meta = {"device_id": "dev-1", "port_num": 0}

        mock_lib = MagicMock()
        mock_lib.update_user_overrides = AsyncMock(return_value=True)
        mock_lib.reset_volume = AsyncMock(return_value=True)
        mock_lib.reset_kegs_served = AsyncMock(return_value=True)

        with (
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
        ):
            result = run_async(reset_port("dev-1", 0, request_data, mock_request, mock_user, mock_session))

        assert result is True

    def test_accepts_l_volume_unit(self):
        from routers.kegtron import ResetPortRequest, reset_port

        request_data = ResetPortRequest(volume_size=19.0, volume_unit="l")
        mock_request = self._create_mock_request()
        mock_user = MagicMock()
        mock_session = AsyncMock()

        mock_monitor = MagicMock()
        mock_monitor.meta = {"device_id": "dev-1", "port_num": 0}

        mock_lib = MagicMock()
        mock_lib.update_user_overrides = AsyncMock(return_value=True)
        mock_lib.reset_volume = AsyncMock(return_value=True)
        mock_lib.reset_kegs_served = AsyncMock(return_value=True)

        with (
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
        ):
            result = run_async(reset_port("dev-1", 0, request_data, mock_request, mock_user, mock_session))

        assert result is True

    def test_accepts_ml_volume_unit(self):
        from routers.kegtron import ResetPortRequest, reset_port

        request_data = ResetPortRequest(volume_size=19000.0, volume_unit="ml")
        mock_request = self._create_mock_request()
        mock_user = MagicMock()
        mock_session = AsyncMock()

        mock_monitor = MagicMock()
        mock_monitor.meta = {"device_id": "dev-1", "port_num": 0}

        mock_lib = MagicMock()
        mock_lib.update_user_overrides = AsyncMock(return_value=True)
        mock_lib.reset_volume = AsyncMock(return_value=True)
        mock_lib.reset_kegs_served = AsyncMock(return_value=True)

        with (
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
        ):
            result = run_async(reset_port("dev-1", 0, request_data, mock_request, mock_user, mock_session))

        assert result is True


class TestClearPort:
    """Tests for clear_port endpoint"""

    def test_raises_400_when_kegtron_lib_not_enabled(self):
        from routers.kegtron import clear_port

        mock_user = MagicMock()
        mock_session = AsyncMock()

        with patch("routers.kegtron.get_tap_monitor_lib", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                run_async(clear_port("dev-1", 0, mock_user, mock_session))

        assert exc_info.value.status_code == 400
        assert "not enabled" in exc_info.value.detail.lower()

    def test_successful_clear_returns_true(self):
        from routers.kegtron import clear_port

        mock_user = MagicMock()
        mock_session = AsyncMock()

        mock_monitor = MagicMock()
        mock_monitor.meta = {"device_id": "dev-1", "port_num": 0}

        mock_lib = MagicMock()
        mock_lib.update_port = AsyncMock(return_value=True)

        with (
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
        ):
            result = run_async(clear_port("dev-1", 0, mock_user, mock_session))

        assert result is True

    def test_sends_default_clear_data_to_update_port(self):
        from routers.kegtron import clear_port

        mock_user = MagicMock()
        mock_session = AsyncMock()

        mock_monitor = MagicMock()
        mock_monitor.meta = {"device_id": "dev-1", "port_num": 0}

        mock_lib = MagicMock()
        mock_lib.update_port = AsyncMock(return_value=True)

        with (
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
        ):
            run_async(clear_port("dev-1", 0, mock_user, mock_session))

        port_data = mock_lib.update_port.call_args[0][0]
        assert port_data["abv"] == 0.0
        assert port_data["ibu"] == 0
        assert port_data["srm"] == 0
        assert port_data["style"] == ""
        assert port_data["userDesc"] == ""
        assert port_data["userName"] == "Port 1"
        assert port_data["labelUrl"] == ""

    def test_clear_port_uses_correct_port_name(self):
        from routers.kegtron import clear_port

        mock_user = MagicMock()
        mock_session = AsyncMock()

        mock_monitor = MagicMock()
        mock_monitor.meta = {"device_id": "dev-1", "port_num": 1}

        mock_lib = MagicMock()
        mock_lib.update_port = AsyncMock(return_value=True)

        with (
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
        ):
            run_async(clear_port("dev-1", 1, mock_user, mock_session))

        port_data = mock_lib.update_port.call_args[0][0]
        assert port_data["userName"] == "Port 2"

    def test_raises_502_when_device_update_fails(self):
        from routers.kegtron import clear_port

        mock_user = MagicMock()
        mock_session = AsyncMock()

        mock_monitor = MagicMock()
        mock_monitor.meta = {"device_id": "dev-1", "port_num": 0}

        mock_lib = MagicMock()
        mock_lib.update_port = AsyncMock(return_value=False)

        with (
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
        ):
            with pytest.raises(HTTPException) as exc_info:
                run_async(clear_port("dev-1", 0, mock_user, mock_session))

        assert exc_info.value.status_code == 502


class TestResetPortRequest:
    """Tests for ResetPortRequest model"""

    def test_creates_with_required_fields(self):
        from routers.kegtron import ResetPortRequest

        req = ResetPortRequest(volume_size=5.0, volume_unit="gal")
        assert req.volume_size == 5.0
        assert req.volume_unit == "gal"
        assert req.batch_id is None

    def test_creates_with_batch_id(self):
        from routers.kegtron import ResetPortRequest

        req = ResetPortRequest(volume_size=5.0, volume_unit="gal", batch_id="batch-123")
        assert req.batch_id == "batch-123"

    def test_accepts_camel_case_aliases(self):
        from routers.kegtron import ResetPortRequest

        req = ResetPortRequest(**{"volumeSize": 5.0, "volumeUnit": "gal", "batchId": "batch-1"})
        assert req.volume_size == 5.0
        assert req.volume_unit == "gal"
        assert req.batch_id == "batch-1"
