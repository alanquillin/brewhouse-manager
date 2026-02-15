"""Tests for routers/kegtron.py module - Kegtron device management router"""

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
    mock.meta = meta or {"device_id": "device-1", "port_num": 0, "access_token": "token-1"}
    return mock


def create_reset_request(volume_size=5.0, volume_unit="gal"):
    """Helper to create mock ResetPortRequest"""
    from routers.kegtron import ResetPortRequest

    return ResetPortRequest(volume_size=volume_size, volume_unit=volume_unit)


def create_mock_request(query_params=None):
    """Helper to create mock FastAPI request"""
    mock = MagicMock()
    mock.query_params = query_params or {}
    return mock


class TestResetPort:
    """Tests for reset_port endpoint"""

    def test_happy_path_returns_true(self):
        """Test successful reset returns True"""
        from routers.kegtron import reset_port

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()
        mock_kegtron_lib = MagicMock()
        mock_kegtron_lib.update_user_overrides = AsyncMock(return_value=True)
        mock_kegtron_lib.reset_volume = AsyncMock(return_value=True)
        mock_kegtron_lib.reset_kegs_served = AsyncMock(return_value=True)
        request_data = create_reset_request(volume_size=5.0, volume_unit="gal")
        mock_request = create_mock_request()

        with (
            patch("routers.kegtron.TapMonitorsDB") as mock_db,
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_kegtron_lib),
        ):
            mock_db.query = AsyncMock(return_value=[mock_monitor])

            result = run_async(reset_port("device-1", 0, request_data, mock_request, mock_auth_user, mock_session))

            assert result is True
            mock_kegtron_lib.update_user_overrides.assert_called_once()
            mock_kegtron_lib.reset_volume.assert_called_once()
            mock_kegtron_lib.reset_kegs_served.assert_called_once()
            call_args = mock_kegtron_lib.update_user_overrides.call_args
            assert "volStart" in call_args[0][0]
            assert call_args[1]["meta"] == mock_monitor.meta

    def test_invalid_volume_unit_returns_400(self):
        """Test invalid volume unit raises 400"""
        from routers.kegtron import reset_port

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        request_data = create_reset_request(volume_size=5.0, volume_unit="invalid")
        mock_request = create_mock_request()

        with pytest.raises(HTTPException) as exc_info:
            run_async(reset_port("device-1", 0, request_data, mock_request, mock_auth_user, mock_session))

        assert exc_info.value.status_code == 400
        assert "Invalid volume unit" in exc_info.value.detail

    def test_monitor_not_found_returns_404(self):
        """Test raises 404 when no matching monitor found"""
        from routers.kegtron import reset_port

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_kegtron_lib = MagicMock()
        request_data = create_reset_request(volume_size=5.0, volume_unit="gal")
        mock_request = create_mock_request()

        with (
            patch("routers.kegtron.TapMonitorsDB") as mock_db,
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_kegtron_lib),
        ):
            mock_db.query = AsyncMock(return_value=[])

            with pytest.raises(HTTPException) as exc_info:
                run_async(reset_port("device-1", 0, request_data, mock_request, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404

    def test_kegtron_lib_not_enabled_returns_400(self):
        """Test raises 400 when kegtron lib is not enabled"""
        from routers.kegtron import reset_port

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        request_data = create_reset_request(volume_size=5.0, volume_unit="gal")
        mock_request = create_mock_request()

        with patch("routers.kegtron.get_tap_monitor_lib", return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                run_async(reset_port("device-1", 0, request_data, mock_request, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 400
            assert "not enabled" in exc_info.value.detail

    def test_device_update_failure_returns_502(self):
        """Test raises 502 when device update fails"""
        from routers.kegtron import reset_port

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()
        mock_kegtron_lib = MagicMock()
        mock_kegtron_lib.update_user_overrides = AsyncMock(return_value=False)
        mock_kegtron_lib.reset_volume = AsyncMock(return_value=True)
        mock_kegtron_lib.reset_kegs_served = AsyncMock(return_value=True)
        request_data = create_reset_request(volume_size=5.0, volume_unit="gal")
        mock_request = create_mock_request()

        with (
            patch("routers.kegtron.TapMonitorsDB") as mock_db,
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_kegtron_lib),
        ):
            mock_db.query = AsyncMock(return_value=[mock_monitor])

            with pytest.raises(HTTPException) as exc_info:
                run_async(reset_port("device-1", 0, request_data, mock_request, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 502

    def test_volume_conversion_gallons(self):
        """Test gallons are correctly converted to ml"""
        from routers.kegtron import reset_port

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()
        mock_kegtron_lib = MagicMock()
        mock_kegtron_lib.update_user_overrides = AsyncMock(return_value=True)
        mock_kegtron_lib.reset_volume = AsyncMock(return_value=True)
        mock_kegtron_lib.reset_kegs_served = AsyncMock(return_value=True)
        request_data = create_reset_request(volume_size=5.0, volume_unit="gal")
        mock_request = create_mock_request()

        with (
            patch("routers.kegtron.TapMonitorsDB") as mock_db,
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_kegtron_lib),
        ):
            mock_db.query = AsyncMock(return_value=[mock_monitor])

            run_async(reset_port("device-1", 0, request_data, mock_request, mock_auth_user, mock_session))

            call_args = mock_kegtron_lib.update_user_overrides.call_args
            vol_start = call_args[0][0]["volStart"]
            assert vol_start == int(5.0 / 0.0002641721)

    def test_volume_conversion_liters(self):
        """Test liters are correctly converted to ml"""
        from routers.kegtron import reset_port

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()
        mock_kegtron_lib = MagicMock()
        mock_kegtron_lib.update_user_overrides = AsyncMock(return_value=True)
        mock_kegtron_lib.reset_volume = AsyncMock(return_value=True)
        mock_kegtron_lib.reset_kegs_served = AsyncMock(return_value=True)
        request_data = create_reset_request(volume_size=19.0, volume_unit="l")
        mock_request = create_mock_request()

        with (
            patch("routers.kegtron.TapMonitorsDB") as mock_db,
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_kegtron_lib),
        ):
            mock_db.query = AsyncMock(return_value=[mock_monitor])

            run_async(reset_port("device-1", 0, request_data, mock_request, mock_auth_user, mock_session))

            call_args = mock_kegtron_lib.update_user_overrides.call_args
            vol_start = call_args[0][0]["volStart"]
            assert vol_start == 19000

    def test_volume_conversion_ml(self):
        """Test ml passes through without conversion"""
        from routers.kegtron import reset_port

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()
        mock_kegtron_lib = MagicMock()
        mock_kegtron_lib.update_user_overrides = AsyncMock(return_value=True)
        mock_kegtron_lib.reset_volume = AsyncMock(return_value=True)
        mock_kegtron_lib.reset_kegs_served = AsyncMock(return_value=True)
        request_data = create_reset_request(volume_size=19000.0, volume_unit="ml")
        mock_request = create_mock_request()

        with (
            patch("routers.kegtron.TapMonitorsDB") as mock_db,
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_kegtron_lib),
        ):
            mock_db.query = AsyncMock(return_value=[mock_monitor])

            run_async(reset_port("device-1", 0, request_data, mock_request, mock_auth_user, mock_session))

            call_args = mock_kegtron_lib.update_user_overrides.call_args
            vol_start = call_args[0][0]["volStart"]
            assert vol_start == 19000

    def test_port_num_matching(self):
        """Test that the correct monitor is selected by port_num"""
        from routers.kegtron import reset_port

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_monitor_0 = create_mock_tap_monitor(meta={"device_id": "device-1", "port_num": 0, "access_token": "token-1"})
        mock_monitor_1 = create_mock_tap_monitor(meta={"device_id": "device-1", "port_num": 1, "access_token": "token-1"})
        mock_kegtron_lib = MagicMock()
        mock_kegtron_lib.update_user_overrides = AsyncMock(return_value=True)
        mock_kegtron_lib.reset_volume = AsyncMock(return_value=True)
        mock_kegtron_lib.reset_kegs_served = AsyncMock(return_value=True)
        request_data = create_reset_request(volume_size=5.0, volume_unit="gal")
        mock_request = create_mock_request()

        with (
            patch("routers.kegtron.TapMonitorsDB") as mock_db,
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_kegtron_lib),
        ):
            mock_db.query = AsyncMock(return_value=[mock_monitor_0, mock_monitor_1])

            run_async(reset_port("device-1", 1, request_data, mock_request, mock_auth_user, mock_session))

            call_args = mock_kegtron_lib.update_user_overrides.call_args
            assert call_args[1]["meta"] == mock_monitor_1.meta

    def test_update_date_tapped_includes_date(self):
        """Test that update_date_tapped=true adds dateTapped to the payload"""
        from routers.kegtron import reset_port

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()
        mock_kegtron_lib = MagicMock()
        mock_kegtron_lib.update_user_overrides = AsyncMock(return_value=True)
        mock_kegtron_lib.reset_volume = AsyncMock(return_value=True)
        mock_kegtron_lib.reset_kegs_served = AsyncMock(return_value=True)
        request_data = create_reset_request(volume_size=5.0, volume_unit="gal")
        mock_request = create_mock_request(query_params={"update_date_tapped": "true"})

        with (
            patch("routers.kegtron.TapMonitorsDB") as mock_db,
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_kegtron_lib),
        ):
            mock_db.query = AsyncMock(return_value=[mock_monitor])

            run_async(reset_port("device-1", 0, request_data, mock_request, mock_auth_user, mock_session))

            call_args = mock_kegtron_lib.update_user_overrides.call_args
            data = call_args[0][0]
            assert "dateTapped" in data
            assert "volStart" in data

    def test_update_date_tapped_false_excludes_date(self):
        """Test that without update_date_tapped, dateTapped is not included"""
        from routers.kegtron import reset_port

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()
        mock_kegtron_lib = MagicMock()
        mock_kegtron_lib.update_user_overrides = AsyncMock(return_value=True)
        mock_kegtron_lib.reset_volume = AsyncMock(return_value=True)
        mock_kegtron_lib.reset_kegs_served = AsyncMock(return_value=True)
        request_data = create_reset_request(volume_size=5.0, volume_unit="gal")
        mock_request = create_mock_request()

        with (
            patch("routers.kegtron.TapMonitorsDB") as mock_db,
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_kegtron_lib),
        ):
            mock_db.query = AsyncMock(return_value=[mock_monitor])

            run_async(reset_port("device-1", 0, request_data, mock_request, mock_auth_user, mock_session))

            call_args = mock_kegtron_lib.update_user_overrides.call_args
            data = call_args[0][0]
            assert "dateTapped" not in data
            assert "volStart" in data

    def test_reset_volume_failure_returns_502(self):
        """Test raises 502 when reset_volume fails"""
        from routers.kegtron import reset_port

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()
        mock_kegtron_lib = MagicMock()
        mock_kegtron_lib.update_user_overrides = AsyncMock(return_value=True)
        mock_kegtron_lib.reset_volume = AsyncMock(return_value=False)
        mock_kegtron_lib.reset_kegs_served = AsyncMock(return_value=True)
        request_data = create_reset_request(volume_size=5.0, volume_unit="gal")
        mock_request = create_mock_request()

        with (
            patch("routers.kegtron.TapMonitorsDB") as mock_db,
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_kegtron_lib),
        ):
            mock_db.query = AsyncMock(return_value=[mock_monitor])

            with pytest.raises(HTTPException) as exc_info:
                run_async(reset_port("device-1", 0, request_data, mock_request, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 502

    def test_reset_kegs_served_failure_returns_502(self):
        """Test raises 502 when reset_kegs_served fails"""
        from routers.kegtron import reset_port

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()
        mock_kegtron_lib = MagicMock()
        mock_kegtron_lib.update_user_overrides = AsyncMock(return_value=True)
        mock_kegtron_lib.reset_volume = AsyncMock(return_value=True)
        mock_kegtron_lib.reset_kegs_served = AsyncMock(return_value=False)
        request_data = create_reset_request(volume_size=5.0, volume_unit="gal")
        mock_request = create_mock_request()

        with (
            patch("routers.kegtron.TapMonitorsDB") as mock_db,
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_kegtron_lib),
        ):
            mock_db.query = AsyncMock(return_value=[mock_monitor])

            with pytest.raises(HTTPException) as exc_info:
                run_async(reset_port("device-1", 0, request_data, mock_request, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 502

    def test_all_three_operations_called_concurrently(self):
        """Test that update_user_overrides, reset_volume, and reset_kegs_served are all called"""
        from routers.kegtron import reset_port

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()
        mock_kegtron_lib = MagicMock()
        mock_kegtron_lib.update_user_overrides = AsyncMock(return_value=True)
        mock_kegtron_lib.reset_volume = AsyncMock(return_value=True)
        mock_kegtron_lib.reset_kegs_served = AsyncMock(return_value=True)
        request_data = create_reset_request(volume_size=5.0, volume_unit="gal")
        mock_request = create_mock_request()

        with (
            patch("routers.kegtron.TapMonitorsDB") as mock_db,
            patch("routers.kegtron.get_tap_monitor_lib", return_value=mock_kegtron_lib),
        ):
            mock_db.query = AsyncMock(return_value=[mock_monitor])

            run_async(reset_port("device-1", 0, request_data, mock_request, mock_auth_user, mock_session))

            mock_kegtron_lib.update_user_overrides.assert_called_once()
            mock_kegtron_lib.reset_volume.assert_called_once()
            mock_kegtron_lib.reset_kegs_served.assert_called_once()
            # Verify reset_volume and reset_kegs_served receive the correct meta
            assert mock_kegtron_lib.reset_volume.call_args[1]["meta"] == mock_monitor.meta
            assert mock_kegtron_lib.reset_kegs_served.call_args[1]["meta"] == mock_monitor.meta
