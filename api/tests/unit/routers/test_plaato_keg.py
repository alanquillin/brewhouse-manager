"""Tests for routers/plaato_keg.py module - Plaato Keg device management router"""

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


def create_mock_device(id_="device-1", name="Test Device"):
    """Helper to create mock plaato keg device"""
    mock = MagicMock()
    mock.id = id_
    mock.name = name
    return mock


def create_mock_tap_monitor(id_="monitor-1", name="Test Monitor", meta=None):
    """Helper to create mock tap monitor"""
    mock = MagicMock()
    mock.id = id_
    mock.name = name
    mock.meta = meta or {"device_id": "device-1"}
    return mock


def create_mock_request(query_params=None):
    """Helper to create mock FastAPI request"""
    mock = MagicMock()
    mock.query_params = query_params or {}
    return mock


class TestDeleteDevice:
    """Tests for delete endpoint"""

    def test_deletes_device_successfully(self):
        """Test deletes device when no tap monitors reference it"""
        from routers.plaato_keg import delete

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_device = create_mock_device()
        mock_request = create_mock_request()

        with patch("routers.plaato_keg.PlaatoDataDB") as mock_plaato_db, patch("routers.plaato_keg.TapMonitorsDB") as mock_monitors_db:
            mock_plaato_db.get_by_pkey = AsyncMock(return_value=mock_device)
            mock_plaato_db.delete = AsyncMock(return_value=1)
            mock_monitors_db.query = AsyncMock(return_value=[])

            result = run_async(delete("device-1", mock_request, mock_auth_user, mock_session))

            mock_plaato_db.delete.assert_called_once_with(mock_session, "device-1")

    def test_raises_404_when_device_not_found(self):
        """Test raises 404 when device does not exist"""
        from routers.plaato_keg import delete

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_request = create_mock_request()

        with patch("routers.plaato_keg.PlaatoDataDB") as mock_plaato_db:
            mock_plaato_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(delete("unknown", mock_request, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404

    def test_raises_409_when_tap_monitor_references_device(self):
        """Test raises 409 Conflict when a tap monitor references the device via meta.device_id"""
        from routers.plaato_keg import delete

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_device = create_mock_device(id_="device-1")
        mock_monitor = create_mock_tap_monitor(name="My Monitor", meta={"device_id": "device-1"})
        mock_request = create_mock_request()

        with patch("routers.plaato_keg.PlaatoDataDB") as mock_plaato_db, patch("routers.plaato_keg.TapMonitorsDB") as mock_monitors_db:
            mock_plaato_db.get_by_pkey = AsyncMock(return_value=mock_device)
            mock_monitors_db.query = AsyncMock(return_value=[mock_monitor])

            with pytest.raises(HTTPException) as exc_info:
                run_async(delete("device-1", mock_request, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 409
            assert "My Monitor" in exc_info.value.detail

    def test_raises_409_includes_all_monitor_names(self):
        """Test 409 error message includes all referencing monitor names"""
        from routers.plaato_keg import delete

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_device = create_mock_device(id_="device-1")
        mock_monitor_1 = create_mock_tap_monitor(id_="m1", name="Monitor A")
        mock_monitor_2 = create_mock_tap_monitor(id_="m2", name="Monitor B")
        mock_request = create_mock_request()

        with patch("routers.plaato_keg.PlaatoDataDB") as mock_plaato_db, patch("routers.plaato_keg.TapMonitorsDB") as mock_monitors_db:
            mock_plaato_db.get_by_pkey = AsyncMock(return_value=mock_device)
            mock_monitors_db.query = AsyncMock(return_value=[mock_monitor_1, mock_monitor_2])

            with pytest.raises(HTTPException) as exc_info:
                run_async(delete("device-1", mock_request, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 409
            assert "Monitor A" in exc_info.value.detail
            assert "Monitor B" in exc_info.value.detail

    def test_force_delete_removes_referencing_tap_monitors(self):
        """Test force_delete_tap_monitor=true deletes referencing monitors then the device"""
        from routers.plaato_keg import delete

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_device = create_mock_device(id_="device-1")
        mock_monitor = create_mock_tap_monitor(id_="monitor-1", name="My Monitor")
        mock_request = create_mock_request(query_params={"force_delete_tap_monitor": "true"})

        with patch("routers.plaato_keg.PlaatoDataDB") as mock_plaato_db, patch("routers.plaato_keg.TapMonitorsDB") as mock_monitors_db:
            mock_plaato_db.get_by_pkey = AsyncMock(return_value=mock_device)
            mock_plaato_db.delete = AsyncMock(return_value=1)
            mock_monitors_db.query = AsyncMock(return_value=[mock_monitor])
            mock_monitors_db.delete = AsyncMock()

            result = run_async(delete("device-1", mock_request, mock_auth_user, mock_session))

            mock_monitors_db.delete.assert_called_once_with(mock_session, "monitor-1")
            mock_plaato_db.delete.assert_called_once_with(mock_session, "device-1")

    def test_force_delete_removes_multiple_monitors(self):
        """Test force delete removes all referencing monitors"""
        from routers.plaato_keg import delete

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_device = create_mock_device(id_="device-1")
        mock_monitor_1 = create_mock_tap_monitor(id_="m1", name="Monitor A")
        mock_monitor_2 = create_mock_tap_monitor(id_="m2", name="Monitor B")
        mock_request = create_mock_request(query_params={"force_delete_tap_monitor": "true"})

        with patch("routers.plaato_keg.PlaatoDataDB") as mock_plaato_db, patch("routers.plaato_keg.TapMonitorsDB") as mock_monitors_db:
            mock_plaato_db.get_by_pkey = AsyncMock(return_value=mock_device)
            mock_plaato_db.delete = AsyncMock(return_value=1)
            mock_monitors_db.query = AsyncMock(return_value=[mock_monitor_1, mock_monitor_2])
            mock_monitors_db.delete = AsyncMock()

            result = run_async(delete("device-1", mock_request, mock_auth_user, mock_session))

            assert mock_monitors_db.delete.call_count == 2
            mock_monitors_db.delete.assert_any_call(mock_session, "m1")
            mock_monitors_db.delete.assert_any_call(mock_session, "m2")
            mock_plaato_db.delete.assert_called_once()

    def test_force_delete_false_still_raises_409(self):
        """Test force_delete_tap_monitor=false still raises 409"""
        from routers.plaato_keg import delete

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_device = create_mock_device(id_="device-1")
        mock_monitor = create_mock_tap_monitor(name="My Monitor")
        mock_request = create_mock_request(query_params={"force_delete_tap_monitor": "false"})

        with patch("routers.plaato_keg.PlaatoDataDB") as mock_plaato_db, patch("routers.plaato_keg.TapMonitorsDB") as mock_monitors_db:
            mock_plaato_db.get_by_pkey = AsyncMock(return_value=mock_device)
            mock_monitors_db.query = AsyncMock(return_value=[mock_monitor])

            with pytest.raises(HTTPException) as exc_info:
                run_async(delete("device-1", mock_request, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 409

    def test_raises_500_when_delete_affects_no_rows(self):
        """Test raises 500 when delete operation affects no rows"""
        from routers.plaato_keg import delete

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_device = create_mock_device()
        mock_request = create_mock_request()

        with patch("routers.plaato_keg.PlaatoDataDB") as mock_plaato_db, patch("routers.plaato_keg.TapMonitorsDB") as mock_monitors_db:
            mock_plaato_db.get_by_pkey = AsyncMock(return_value=mock_device)
            mock_plaato_db.delete = AsyncMock(return_value=0)
            mock_monitors_db.query = AsyncMock(return_value=[])

            with pytest.raises(HTTPException) as exc_info:
                run_async(delete("device-1", mock_request, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 500
