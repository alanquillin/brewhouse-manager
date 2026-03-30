"""Tests for routers/kegtron_gen1.py module - Kegtron Gen1 Device Management router"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


def create_mock_auth_user(id_="user-1", admin=True):
    """Helper to create mock AuthUser"""
    mock = MagicMock()
    mock.id = id_
    mock.admin = admin
    return mock


def create_mock_tap_monitor(id_="monitor-1", name="Test Monitor", meta=None):
    """Helper to create mock tap monitor"""
    mock = MagicMock()
    mock.id = id_
    mock.name = name
    mock.meta = meta or {"device_id": "device-1", "port_index": 0}
    return mock


class TestGetMonitorFromDeviceAndPort:
    """Tests for get_monitor_from_device_and_port helper"""

    def test_returns_matching_monitor(self):
        from routers.kegtron_gen1 import get_monitor_from_device_and_port

        mock_monitor = MagicMock()
        mock_monitor.meta = {"device_id": "dev-1", "port_index": 0}

        mock_session = AsyncMock()
        with patch("routers.kegtron_gen1.TapMonitorsDB") as mock_db:
            mock_db.query = AsyncMock(return_value=[mock_monitor])
            result = run_async(get_monitor_from_device_and_port("dev-1", 0, mock_session))

        assert result == mock_monitor

    def test_raises_404_when_no_monitor_found(self):
        from routers.kegtron_gen1 import get_monitor_from_device_and_port

        mock_session = AsyncMock()
        with patch("routers.kegtron_gen1.TapMonitorsDB") as mock_db:
            mock_db.query = AsyncMock(return_value=[])
            with pytest.raises(HTTPException) as exc_info:
                run_async(get_monitor_from_device_and_port("nonexistent", 0, mock_session))

        assert exc_info.value.status_code == 404
        assert "not found" in exc_info.value.detail.lower()

    def test_raises_404_when_port_index_does_not_match(self):
        from routers.kegtron_gen1 import get_monitor_from_device_and_port

        mock_monitor = MagicMock()
        mock_monitor.meta = {"device_id": "dev-1", "port_index": 1}

        mock_session = AsyncMock()
        with patch("routers.kegtron_gen1.TapMonitorsDB") as mock_db:
            mock_db.query = AsyncMock(return_value=[mock_monitor])
            with pytest.raises(HTTPException) as exc_info:
                run_async(get_monitor_from_device_and_port("dev-1", 0, mock_session))

        assert exc_info.value.status_code == 404


class TestResetVolume:
    """Tests for reset_volume endpoint"""

    def test_rejects_invalid_volume_unit(self):
        from routers.kegtron_gen1 import ResetVolumeRequest, reset_volume

        request_data = ResetVolumeRequest(keg_size=5.0, start_volume=5.0, volume_unit="invalid")
        mock_user = MagicMock()
        mock_session = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            run_async(reset_volume("dev-1", 0, request_data, mock_user, mock_session))

        assert exc_info.value.status_code == 400
        assert "Invalid volume unit" in exc_info.value.detail

    def test_raises_400_when_kegtron_gen1_lib_not_enabled(self):
        from routers.kegtron_gen1 import ResetVolumeRequest, reset_volume

        request_data = ResetVolumeRequest(keg_size=5.0, start_volume=5.0, volume_unit="gal")
        mock_user = MagicMock()
        mock_session = AsyncMock()

        with patch("routers.kegtron_gen1.get_tap_monitor_lib", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                run_async(reset_volume("dev-1", 0, request_data, mock_user, mock_session))

        assert exc_info.value.status_code == 400
        assert "not enabled" in exc_info.value.detail.lower()

    def test_successful_reset_returns_true(self):
        from routers.kegtron_gen1 import ResetVolumeRequest, reset_volume

        request_data = ResetVolumeRequest(keg_size=5.0, start_volume=5.0, volume_unit="gal")
        mock_user = MagicMock()
        mock_session = AsyncMock()

        mock_monitor = create_mock_tap_monitor()
        mock_lib = MagicMock()
        mock_lib.reset_volume = AsyncMock(return_value=True)

        with (
            patch("routers.kegtron_gen1.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron_gen1.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
        ):
            result = run_async(reset_volume("dev-1", 0, request_data, mock_user, mock_session))

        assert result is True

    def test_calls_reset_volume_with_correct_args(self):
        from routers.kegtron_gen1 import ResetVolumeRequest, reset_volume

        request_data = ResetVolumeRequest(keg_size=5.0, start_volume=4.5, volume_unit="l")
        mock_user = MagicMock()
        mock_session = AsyncMock()

        mock_monitor = create_mock_tap_monitor(meta={"device_id": "dev-1", "port_index": 1})
        mock_lib = MagicMock()
        mock_lib.reset_volume = AsyncMock(return_value=True)

        with (
            patch("routers.kegtron_gen1.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron_gen1.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
        ):
            run_async(reset_volume("dev-1", 1, request_data, mock_user, mock_session))

        mock_lib.reset_volume.assert_called_once_with(
            keg_size=5.0,
            start_volume=4.5,
            unit="l",
            meta=mock_monitor.meta,
        )

    def test_raises_502_when_reset_fails(self):
        from routers.kegtron_gen1 import ResetVolumeRequest, reset_volume

        request_data = ResetVolumeRequest(keg_size=5.0, start_volume=5.0, volume_unit="gal")
        mock_user = MagicMock()
        mock_session = AsyncMock()

        mock_monitor = create_mock_tap_monitor()
        mock_lib = MagicMock()
        mock_lib.reset_volume = AsyncMock(return_value=False)

        with (
            patch("routers.kegtron_gen1.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron_gen1.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
        ):
            with pytest.raises(HTTPException) as exc_info:
                run_async(reset_volume("dev-1", 0, request_data, mock_user, mock_session))

        assert exc_info.value.status_code == 502

    def test_accepts_gal_volume_unit(self):
        from routers.kegtron_gen1 import ResetVolumeRequest, reset_volume

        request_data = ResetVolumeRequest(keg_size=5.0, start_volume=5.0, volume_unit="gal")
        mock_user = MagicMock()
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()
        mock_lib = MagicMock()
        mock_lib.reset_volume = AsyncMock(return_value=True)

        with (
            patch("routers.kegtron_gen1.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron_gen1.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
        ):
            result = run_async(reset_volume("dev-1", 0, request_data, mock_user, mock_session))

        assert result is True

    def test_accepts_l_volume_unit(self):
        from routers.kegtron_gen1 import ResetVolumeRequest, reset_volume

        request_data = ResetVolumeRequest(keg_size=19.0, start_volume=19.0, volume_unit="l")
        mock_user = MagicMock()
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()
        mock_lib = MagicMock()
        mock_lib.reset_volume = AsyncMock(return_value=True)

        with (
            patch("routers.kegtron_gen1.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron_gen1.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
        ):
            result = run_async(reset_volume("dev-1", 0, request_data, mock_user, mock_session))

        assert result is True

    def test_accepts_ml_volume_unit(self):
        from routers.kegtron_gen1 import ResetVolumeRequest, reset_volume

        request_data = ResetVolumeRequest(keg_size=19000.0, start_volume=19000.0, volume_unit="ml")
        mock_user = MagicMock()
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()
        mock_lib = MagicMock()
        mock_lib.reset_volume = AsyncMock(return_value=True)

        with (
            patch("routers.kegtron_gen1.get_tap_monitor_lib", return_value=mock_lib),
            patch("routers.kegtron_gen1.get_monitor_from_device_and_port", new_callable=AsyncMock, return_value=mock_monitor),
        ):
            result = run_async(reset_volume("dev-1", 0, request_data, mock_user, mock_session))

        assert result is True


class TestResetVolumeRequest:
    """Tests for ResetVolumeRequest model"""

    def test_creates_with_required_fields(self):
        from routers.kegtron_gen1 import ResetVolumeRequest

        req = ResetVolumeRequest(keg_size=5.0, start_volume=5.0, volume_unit="gal")
        assert req.keg_size == 5.0
        assert req.start_volume == 5.0
        assert req.volume_unit == "gal"
        assert req.batch_id is None

    def test_creates_with_batch_id(self):
        from routers.kegtron_gen1 import ResetVolumeRequest

        req = ResetVolumeRequest(keg_size=5.0, start_volume=5.0, volume_unit="gal", batch_id="batch-123")
        assert req.batch_id == "batch-123"

    def test_accepts_camel_case_aliases(self):
        from routers.kegtron_gen1 import ResetVolumeRequest

        req = ResetVolumeRequest(**{"kegSize": 5.0, "startVolume": 5.0, "volumeUnit": "gal", "batchId": "batch-1"})
        assert req.keg_size == 5.0
        assert req.start_volume == 5.0
        assert req.volume_unit == "gal"
        assert req.batch_id == "batch-1"


class TestValidateKegtronGen1Meta:
    """Tests for _validate_kegtron_gen1_meta helper"""

    def test_all_fields_present(self):
        from routers.tap_monitors import _validate_kegtron_gen1_meta

        _validate_kegtron_gen1_meta({"device_id": "dev-1", "port_index": 0})

    def test_empty_meta_raises(self):
        from routers.tap_monitors import _validate_kegtron_gen1_meta

        with pytest.raises(HTTPException) as exc_info:
            _validate_kegtron_gen1_meta({})

        assert exc_info.value.status_code == 400
        assert "device_id" in exc_info.value.detail
        assert "port_index" in exc_info.value.detail

    def test_partial_meta_lists_only_missing(self):
        from routers.tap_monitors import _validate_kegtron_gen1_meta

        with pytest.raises(HTTPException) as exc_info:
            _validate_kegtron_gen1_meta({"device_id": "dev-1"})

        assert exc_info.value.status_code == 400
        assert "device_id" not in exc_info.value.detail
        assert "port_index" in exc_info.value.detail

    def test_empty_string_treated_as_missing(self):
        from routers.tap_monitors import _validate_kegtron_gen1_meta

        with pytest.raises(HTTPException) as exc_info:
            _validate_kegtron_gen1_meta({"device_id": "", "port_index": None})

        assert exc_info.value.status_code == 400
        assert "device_id" in exc_info.value.detail
        assert "port_index" in exc_info.value.detail

    def test_zero_port_index_is_valid(self):
        from routers.tap_monitors import _validate_kegtron_gen1_meta

        _validate_kegtron_gen1_meta({"device_id": "dev-1", "port_index": 0})

    def test_allow_missing_skips_absent_keys(self):
        from routers.tap_monitors import _validate_kegtron_gen1_meta

        _validate_kegtron_gen1_meta({"device_id": "dev-1"}, allow_missing=True)

    def test_allow_missing_still_rejects_empty_values(self):
        from routers.tap_monitors import _validate_kegtron_gen1_meta

        with pytest.raises(HTTPException) as exc_info:
            _validate_kegtron_gen1_meta({"device_id": "", "port_index": 0}, allow_missing=True)

        assert exc_info.value.status_code == 400
        assert "device_id" in exc_info.value.detail
