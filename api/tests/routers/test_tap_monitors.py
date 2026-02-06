"""Tests for routers/tap_monitors.py module - Tap monitors router"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi import HTTPException


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


def create_mock_auth_user(id_="user-1", admin=False, locations=None):
    """Helper to create mock AuthUser"""
    mock = MagicMock()
    mock.id = id_
    mock.admin = admin
    mock.locations = locations or []
    return mock


def create_mock_tap_monitor(
    id_="monitor-1",
    name="Test Monitor",
    monitor_type="plaato_keg",
    location_id="loc-1"
):
    """Helper to create mock tap monitor"""
    mock = MagicMock()
    mock.id = id_
    mock.name = name
    mock.monitor_type = monitor_type
    mock.location_id = location_id
    return mock


def create_mock_request(query_params=None):
    """Helper to create mock request"""
    mock = MagicMock()
    mock.query_params = query_params or {}
    return mock


class TestGetLocationId:
    """Tests for get_location_id helper"""

    def test_returns_uuid_unchanged(self):
        """Test returns valid UUID unchanged"""
        from routers.tap_monitors import get_location_id

        mock_session = AsyncMock()
        uuid_str = "123e4567-e89b-12d3-a456-426614174000"

        with patch('routers.tap_monitors.util.is_valid_uuid', return_value=True):
            result = run_async(get_location_id(uuid_str, mock_session))

        assert result == uuid_str

    def test_looks_up_by_name(self):
        """Test looks up location by name"""
        from routers.tap_monitors import get_location_id
        from db.locations import Locations as LocationsDB

        mock_session = AsyncMock()
        mock_location = MagicMock(id="loc-abc")

        with patch('routers.tap_monitors.util.is_valid_uuid', return_value=False), \
             patch.object(LocationsDB, 'query', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = [mock_location]

            result = run_async(get_location_id("Test Location", mock_session))

        assert result == "loc-abc"


class TestListMonitorTypes:
    """Tests for list_monitor_types endpoint"""

    def test_lists_available_monitor_types(self):
        """Test lists available tap monitor types"""
        from routers.tap_monitors import list_monitor_types

        mock_auth_user = create_mock_auth_user()
        mock_types = [
            {"type": "plaato_keg", "name": "Plaato Keg"},
            {"type": "kegtron", "name": "Kegtron"},
        ]

        with patch('routers.tap_monitors.get_tap_monitor_types', return_value=mock_types), \
             patch('routers.tap_monitors.TapMonitorTypeService') as mock_service:
            mock_service.transform_response = AsyncMock(side_effect=[
                {"type": "plaato_keg", "name": "Plaato Keg"},
                {"type": "kegtron", "name": "Kegtron"},
            ])

            result = run_async(list_monitor_types(mock_auth_user))

            assert len(result) == 2


class TestDiscoverTapMonitors:
    """Tests for discover_tap_monitors endpoint"""

    def test_raises_404(self):
        """Test raises 404 - generic discover not supported"""
        from routers.tap_monitors import discover_tap_monitors

        mock_auth_user = create_mock_auth_user()

        with pytest.raises(HTTPException) as exc_info:
            run_async(discover_tap_monitors(mock_auth_user))

        assert exc_info.value.status_code == 404


class TestDiscoverTapMonitorsByType:
    """Tests for discover_tap_monitors_by_type endpoint"""

    def test_discovers_monitors_by_type(self):
        """Test discovers monitors of specific type"""
        from routers.tap_monitors import discover_tap_monitors_by_type

        mock_auth_user = create_mock_auth_user()
        mock_types = [{"type": "plaato_keg"}, {"type": "kegtron"}]

        with patch('routers.tap_monitors.get_tap_monitor_types', return_value=mock_types), \
             patch('routers.tap_monitors.get_tap_monitor_lib') as mock_get_lib, \
             patch('routers.tap_monitors.transform_dict_to_camel_case') as mock_transform:
            mock_lib = MagicMock()
            mock_lib.supports_discovery.return_value = True
            mock_lib.discover = AsyncMock(return_value=[{"id": "device-1"}])
            mock_get_lib.return_value = mock_lib
            mock_transform.return_value = [{"id": "device-1"}]

            result = run_async(discover_tap_monitors_by_type("plaato_keg", mock_auth_user))

            assert result == [{"id": "device-1"}]

    def test_raises_400_for_invalid_type(self):
        """Test raises 400 for invalid monitor type"""
        from routers.tap_monitors import discover_tap_monitors_by_type

        mock_auth_user = create_mock_auth_user()
        mock_types = [{"type": "plaato_keg"}]

        with patch('routers.tap_monitors.get_tap_monitor_types', return_value=mock_types):
            with pytest.raises(HTTPException) as exc_info:
                run_async(discover_tap_monitors_by_type("invalid_type", mock_auth_user))

            assert exc_info.value.status_code == 400

    def test_raises_400_when_discovery_not_supported(self):
        """Test raises 400 when monitor type doesn't support discovery"""
        from routers.tap_monitors import discover_tap_monitors_by_type

        mock_auth_user = create_mock_auth_user()
        mock_types = [{"type": "plaato_keg"}]

        with patch('routers.tap_monitors.get_tap_monitor_types', return_value=mock_types), \
             patch('routers.tap_monitors.get_tap_monitor_lib') as mock_get_lib:
            mock_lib = MagicMock()
            mock_lib.supports_discovery.return_value = False
            mock_get_lib.return_value = mock_lib

            with pytest.raises(HTTPException) as exc_info:
                run_async(discover_tap_monitors_by_type("plaato_keg", mock_auth_user))

            assert exc_info.value.status_code == 400


class TestListTapMonitors:
    """Tests for list_tap_monitors endpoint"""

    def test_admin_lists_all_monitors(self):
        """Test admin can list all tap monitors"""
        from routers.tap_monitors import list_tap_monitors

        mock_request = create_mock_request()
        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()

        with patch('routers.tap_monitors.TapMonitorsDB') as mock_db, \
             patch('routers.tap_monitors.TapMonitorService') as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_monitor])
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            result = run_async(list_tap_monitors(mock_request, None, mock_auth_user, mock_session))

            mock_db.query.assert_called_once_with(mock_session)
            assert len(result) == 1

    def test_non_admin_lists_own_location_monitors(self):
        """Test non-admin lists only monitors in their locations"""
        from routers.tap_monitors import list_tap_monitors

        mock_request = create_mock_request()
        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-1", "loc-2"])
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()

        with patch('routers.tap_monitors.TapMonitorsDB') as mock_db, \
             patch('routers.tap_monitors.TapMonitorService') as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_monitor])
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            result = run_async(list_tap_monitors(mock_request, None, mock_auth_user, mock_session))

            mock_db.query.assert_called_once_with(mock_session, locations=["loc-1", "loc-2"])

    def test_include_tap_details(self):
        """Test includes tap details when requested"""
        from routers.tap_monitors import list_tap_monitors

        mock_request = create_mock_request(query_params={"include_tap_details": "true"})
        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()

        with patch('routers.tap_monitors.TapMonitorsDB') as mock_db, \
             patch('routers.tap_monitors.TapMonitorService') as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_monitor])
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            run_async(list_tap_monitors(mock_request, None, mock_auth_user, mock_session))

            mock_service.transform_response.assert_called_with(
                mock_monitor,
                db_session=mock_session,
                include_tap=True
            )


class TestCreateTapMonitor:
    """Tests for create_tap_monitor endpoint"""

    def test_creates_tap_monitor(self):
        """Test creates tap monitor successfully"""
        from routers.tap_monitors import create_tap_monitor
        from schemas.tap_monitors import TapMonitorCreate

        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-1"])
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()
        monitor_data = TapMonitorCreate(name="New Monitor", monitor_type="plaato_keg", location_id="loc-1")

        with patch('routers.tap_monitors.TapMonitorsDB') as mock_db, \
             patch('routers.tap_monitors.TapMonitorService') as mock_service:
            mock_db.create = AsyncMock(return_value=mock_monitor)
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            result = run_async(create_tap_monitor(monitor_data, None, mock_auth_user, mock_session))

            mock_db.create.assert_called_once()

    def test_raises_403_for_unauthorized_location(self):
        """Test raises 403 when creating monitor in unauthorized location"""
        from routers.tap_monitors import create_tap_monitor
        from schemas.tap_monitors import TapMonitorCreate

        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-other"])
        mock_session = AsyncMock()
        monitor_data = TapMonitorCreate(name="New Monitor", monitor_type="plaato_keg", location_id="loc-1")

        with pytest.raises(HTTPException) as exc_info:
            run_async(create_tap_monitor(monitor_data, None, mock_auth_user, mock_session))

        assert exc_info.value.status_code == 403


class TestGetTapMonitor:
    """Tests for get_tap_monitor endpoint"""

    def test_gets_tap_monitor_by_id(self):
        """Test gets tap monitor by ID"""
        from routers.tap_monitors import get_tap_monitor

        mock_request = create_mock_request()
        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-1"])
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor(location_id="loc-1")

        with patch('routers.tap_monitors.TapMonitorsDB') as mock_db, \
             patch('routers.tap_monitors.TapMonitorService') as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            result = run_async(get_tap_monitor(mock_request, "monitor-1", None, mock_auth_user, mock_session))

            assert result["id"] == "monitor-1"

    def test_raises_404_when_not_found(self):
        """Test raises 404 when tap monitor not found"""
        from routers.tap_monitors import get_tap_monitor

        mock_request = create_mock_request()
        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()

        with patch('routers.tap_monitors.TapMonitorsDB') as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_tap_monitor(mock_request, "unknown", None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404

    def test_raises_403_for_unauthorized_monitor(self):
        """Test raises 403 when user not authorized for monitor's location"""
        from routers.tap_monitors import get_tap_monitor

        mock_request = create_mock_request()
        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-other"])
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor(location_id="loc-1")

        with patch('routers.tap_monitors.TapMonitorsDB') as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_tap_monitor(mock_request, "monitor-1", None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 403


class TestUpdateTapMonitor:
    """Tests for update_tap_monitor endpoint"""

    def test_updates_tap_monitor(self):
        """Test updates tap monitor successfully"""
        from routers.tap_monitors import update_tap_monitor
        from schemas.tap_monitors import TapMonitorUpdate

        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-1"])
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor(location_id="loc-1")
        update_data = TapMonitorUpdate(name="Updated Monitor")

        with patch('routers.tap_monitors.TapMonitorsDB') as mock_db, \
             patch('routers.tap_monitors.TapMonitorService') as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_db.update = AsyncMock()
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            result = run_async(update_tap_monitor("monitor-1", update_data, None, mock_auth_user, mock_session))

            mock_db.update.assert_called_once()

    def test_raises_404_when_not_found(self):
        """Test raises 404 when tap monitor not found"""
        from routers.tap_monitors import update_tap_monitor
        from schemas.tap_monitors import TapMonitorUpdate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        update_data = TapMonitorUpdate(name="Updated")

        with patch('routers.tap_monitors.TapMonitorsDB') as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(update_tap_monitor("unknown", update_data, None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404


class TestDeleteTapMonitor:
    """Tests for delete_tap_monitor endpoint"""

    def test_deletes_tap_monitor(self):
        """Test deletes tap monitor successfully"""
        from routers.tap_monitors import delete_tap_monitor

        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-1"])
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor(location_id="loc-1")

        with patch('routers.tap_monitors.TapMonitorsDB') as mock_monitor_db, \
             patch('routers.tap_monitors.TapsDB') as mock_taps_db:
            mock_monitor_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_monitor_db.delete = AsyncMock()
            mock_taps_db.query = AsyncMock(return_value=[])

            result = run_async(delete_tap_monitor("monitor-1", None, mock_auth_user, mock_session))

            assert result is True
            mock_monitor_db.delete.assert_called_once()

    def test_deletes_tap_monitor_updates_taps(self):
        """Test deletes tap monitor and updates associated taps"""
        from routers.tap_monitors import delete_tap_monitor

        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-1"])
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor(location_id="loc-1")
        mock_tap = MagicMock(id="tap-1")

        with patch('routers.tap_monitors.TapMonitorsDB') as mock_monitor_db, \
             patch('routers.tap_monitors.TapsDB') as mock_taps_db:
            mock_monitor_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_monitor_db.delete = AsyncMock()
            mock_taps_db.query = AsyncMock(return_value=[mock_tap])
            mock_taps_db.update = AsyncMock()

            result = run_async(delete_tap_monitor("monitor-1", None, mock_auth_user, mock_session))

            assert result is True
            mock_taps_db.update.assert_called_once_with(mock_session, "tap-1", tap_monitor_id=None)

    def test_raises_404_when_not_found(self):
        """Test raises 404 when tap monitor not found"""
        from routers.tap_monitors import delete_tap_monitor

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()

        with patch('routers.tap_monitors.TapMonitorsDB') as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(delete_tap_monitor("unknown", None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404


class TestGetTapMonitorData:
    """Tests for get_tap_monitor_data endpoint"""

    def test_gets_tap_monitor_data(self):
        """Test gets tap monitor data"""
        from routers.tap_monitors import get_tap_monitor_data

        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor(monitor_type="plaato_keg")

        with patch('routers.tap_monitors.TapMonitorsDB') as mock_db, \
             patch('routers.tap_monitors.get_tap_monitor_lib') as mock_get_lib:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_lib = MagicMock()
            mock_lib.get_all = AsyncMock(return_value={"percent_left": 75.5})
            mock_get_lib.return_value = mock_lib

            result = run_async(get_tap_monitor_data("monitor-1", None, mock_session))

            assert result["percent_left"] == 75.5

    def test_raises_404_when_not_found(self):
        """Test raises 404 when tap monitor not found"""
        from routers.tap_monitors import get_tap_monitor_data

        mock_session = AsyncMock()

        with patch('routers.tap_monitors.TapMonitorsDB') as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_tap_monitor_data("unknown", None, mock_session))

            assert exc_info.value.status_code == 404


class TestGetSpecificTapMonitorData:
    """Tests for get_specific_tap_monitor_data endpoint"""

    def test_gets_specific_data_type(self):
        """Test gets specific data type from tap monitor"""
        from routers.tap_monitors import get_specific_tap_monitor_data

        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor(monitor_type="plaato_keg")

        with patch('routers.tap_monitors.TapMonitorsDB') as mock_db, \
             patch('routers.tap_monitors.get_tap_monitor_lib') as mock_get_lib:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_lib = MagicMock()
            mock_lib.get = AsyncMock(return_value=75.5)
            mock_get_lib.return_value = mock_lib

            result = run_async(get_specific_tap_monitor_data("monitor-1", "percent_left", None, mock_session))

            assert result == 75.5

    def test_raises_404_when_not_found(self):
        """Test raises 404 when tap monitor not found"""
        from routers.tap_monitors import get_specific_tap_monitor_data

        mock_session = AsyncMock()

        with patch('routers.tap_monitors.TapMonitorsDB') as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_specific_tap_monitor_data("unknown", "percent_left", None, mock_session))

            assert exc_info.value.status_code == 404

    def test_raises_400_for_invalid_data_type(self):
        """Test raises 400 for invalid data type"""
        from routers.tap_monitors import get_specific_tap_monitor_data
        from lib.tap_monitors import InvalidDataType

        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor(monitor_type="plaato_keg")

        with patch('routers.tap_monitors.TapMonitorsDB') as mock_db, \
             patch('routers.tap_monitors.get_tap_monitor_lib') as mock_get_lib:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_lib = MagicMock()
            mock_lib.get = AsyncMock(side_effect=InvalidDataType("Invalid data type"))
            mock_get_lib.return_value = mock_lib

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_specific_tap_monitor_data("monitor-1", "invalid", None, mock_session))

            assert exc_info.value.status_code == 400
