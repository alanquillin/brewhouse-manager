"""Tests for routers/tap_monitors.py module - Tap monitors router"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
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


def create_mock_tap_monitor(id_="monitor-1", name="Test Monitor", monitor_type="plaato_keg", location_id="loc-1"):
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

        with patch("routers.util.is_valid_uuid", return_value=True):
            result = run_async(get_location_id(uuid_str, mock_session))

        assert result == uuid_str

    def test_looks_up_by_name(self):
        """Test looks up location by name"""
        from db.locations import Locations as LocationsDB
        from routers.tap_monitors import get_location_id

        mock_session = AsyncMock()
        mock_location = MagicMock(id="loc-abc")

        with patch("routers.util.is_valid_uuid", return_value=False), patch.object(LocationsDB, "query", new_callable=AsyncMock) as mock_query:
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

        with patch("routers.tap_monitors.get_tap_monitor_types", return_value=mock_types), patch("routers.tap_monitors.TapMonitorTypeService") as mock_service:
            mock_service.transform_response = AsyncMock(
                side_effect=[
                    {"type": "plaato_keg", "name": "Plaato Keg"},
                    {"type": "kegtron", "name": "Kegtron"},
                ]
            )

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

        with patch("routers.tap_monitors.get_tap_monitor_types", return_value=mock_types), patch(
            "routers.tap_monitors.get_tap_monitor_lib"
        ) as mock_get_lib, patch("routers.tap_monitors.transform_dict_to_camel_case") as mock_transform:
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

        with patch("routers.tap_monitors.get_tap_monitor_types", return_value=mock_types):
            with pytest.raises(HTTPException) as exc_info:
                run_async(discover_tap_monitors_by_type("invalid_type", mock_auth_user))

            assert exc_info.value.status_code == 400

    def test_raises_400_when_discovery_not_supported(self):
        """Test raises 400 when monitor type doesn't support discovery"""
        from routers.tap_monitors import discover_tap_monitors_by_type

        mock_auth_user = create_mock_auth_user()
        mock_types = [{"type": "plaato_keg"}]

        with patch("routers.tap_monitors.get_tap_monitor_types", return_value=mock_types), patch("routers.tap_monitors.get_tap_monitor_lib") as mock_get_lib:
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

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.TapMonitorService") as mock_service:
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

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.TapMonitorService") as mock_service:
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

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.TapMonitorService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_monitor])
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            run_async(list_tap_monitors(mock_request, None, mock_auth_user, mock_session))

            mock_service.transform_response.assert_called_with(mock_monitor, db_session=mock_session, include_tap=True)

    @pytest.mark.parametrize("param_value", ["true", "yes", "", "1", "True", "YES", "TRUE"])
    def test_include_tap_details_truthy_values(self, param_value):
        """Test that various truthy values for include_tap_details pass include_tap=True"""
        from routers.tap_monitors import list_tap_monitors

        mock_request = create_mock_request(query_params={"include_tap_details": param_value})
        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.TapMonitorService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_monitor])
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            run_async(list_tap_monitors(mock_request, None, mock_auth_user, mock_session))

            mock_service.transform_response.assert_called_with(mock_monitor, db_session=mock_session, include_tap=True)

    @pytest.mark.parametrize("param_value", ["false", "no", "0", "random"])
    def test_include_tap_details_falsy_values(self, param_value):
        """Test that non-truthy values for include_tap_details pass include_tap=False"""
        from routers.tap_monitors import list_tap_monitors

        mock_request = create_mock_request(query_params={"include_tap_details": param_value})
        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.TapMonitorService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_monitor])
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            run_async(list_tap_monitors(mock_request, None, mock_auth_user, mock_session))

            mock_service.transform_response.assert_called_with(mock_monitor, db_session=mock_session, include_tap=False)

    def test_include_tap_details_defaults_to_false(self):
        """Test that include_tap_details defaults to False when not provided"""
        from routers.tap_monitors import list_tap_monitors

        mock_request = create_mock_request()
        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.TapMonitorService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_monitor])
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            run_async(list_tap_monitors(mock_request, None, mock_auth_user, mock_session))

            mock_service.transform_response.assert_called_with(mock_monitor, db_session=mock_session, include_tap=False)


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

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.TapMonitorService") as mock_service:
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

    def test_raises_409_for_duplicate_device_id_and_monitor_type(self):
        """Test raises 409 when a monitor with the same device_id and monitor_type already exists"""
        from routers.tap_monitors import create_tap_monitor
        from schemas.tap_monitors import TapMonitorCreate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        existing_monitor = create_mock_tap_monitor(name="Existing Monitor")
        monitor_data = TapMonitorCreate(
            name="Duplicate Monitor",
            monitor_type="plaato-keg",
            location_id="loc-1",
            meta={"deviceId": "device-1"},
        )

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db:
            mock_db.query = AsyncMock(return_value=[existing_monitor])

            with pytest.raises(HTTPException) as exc_info:
                run_async(create_tap_monitor(monitor_data, None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 409
            assert "plaato-keg" in exc_info.value.detail
            assert "device-1" in exc_info.value.detail

    def test_allows_same_device_id_with_different_monitor_type(self):
        """Test allows creating a monitor with same device_id but different monitor_type"""
        from routers.tap_monitors import create_tap_monitor
        from schemas.tap_monitors import TapMonitorCreate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()
        monitor_data = TapMonitorCreate(
            name="New Monitor",
            monitor_type="open-plaato-keg",
            location_id="loc-1",
            meta={"deviceId": "device-1"},
        )

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.TapMonitorService") as mock_service:
            mock_db.query = AsyncMock(return_value=[])
            mock_db.create = AsyncMock(return_value=mock_monitor)
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            result = run_async(create_tap_monitor(monitor_data, None, mock_auth_user, mock_session))

            mock_db.create.assert_called_once()

    def test_allows_create_without_device_id_in_meta(self):
        """Test allows creating a monitor without device_id in meta (no duplicate check needed)"""
        from routers.tap_monitors import create_tap_monitor
        from schemas.tap_monitors import TapMonitorCreate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()
        monitor_data = TapMonitorCreate(
            name="New Monitor",
            monitor_type="plaato-keg",
            location_id="loc-1",
            meta={"emptyKegWeight": 4400},
        )

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.TapMonitorService") as mock_service:
            mock_db.create = AsyncMock(return_value=mock_monitor)
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            result = run_async(create_tap_monitor(monitor_data, None, mock_auth_user, mock_session))

            mock_db.create.assert_called_once()
            mock_db.query.assert_not_called()

    def test_allows_create_without_meta(self):
        """Test allows creating a monitor without meta at all"""
        from routers.tap_monitors import create_tap_monitor
        from schemas.tap_monitors import TapMonitorCreate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()
        monitor_data = TapMonitorCreate(
            name="New Monitor",
            monitor_type="plaato-keg",
            location_id="loc-1",
        )

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.TapMonitorService") as mock_service:
            mock_db.create = AsyncMock(return_value=mock_monitor)
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            result = run_async(create_tap_monitor(monitor_data, None, mock_auth_user, mock_session))

            mock_db.create.assert_called_once()
            mock_db.query.assert_not_called()


class TestCreateKegtronProValidation:
    """Tests for kegtron-pro meta validation on create"""

    def test_raises_400_when_missing_all_required_meta(self):
        """Test raises 400 when creating kegtron-pro without required meta fields"""
        from routers.tap_monitors import create_tap_monitor
        from schemas.tap_monitors import TapMonitorCreate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        monitor_data = TapMonitorCreate(
            name="Kegtron Monitor",
            monitor_type="kegtron-pro",
            location_id="loc-1",
            meta={},
        )

        with pytest.raises(HTTPException) as exc_info:
            run_async(create_tap_monitor(monitor_data, None, mock_auth_user, mock_session))

        assert exc_info.value.status_code == 400
        assert "port_num" in exc_info.value.detail
        assert "device_id" in exc_info.value.detail
        assert "access_token" in exc_info.value.detail

    def test_raises_400_when_missing_some_required_meta(self):
        """Test raises 400 listing only the missing fields"""
        from routers.tap_monitors import create_tap_monitor
        from schemas.tap_monitors import TapMonitorCreate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        monitor_data = TapMonitorCreate(
            name="Kegtron Monitor",
            monitor_type="kegtron-pro",
            location_id="loc-1",
            meta={"accessToken": "tok123"},
        )

        with pytest.raises(HTTPException) as exc_info:
            run_async(create_tap_monitor(monitor_data, None, mock_auth_user, mock_session))

        assert exc_info.value.status_code == 400
        assert "port_num" in exc_info.value.detail
        assert "device_id" in exc_info.value.detail
        assert "access_token" not in exc_info.value.detail

    def test_raises_400_when_meta_is_none(self):
        """Test raises 400 when creating kegtron-pro with no meta at all"""
        from routers.tap_monitors import create_tap_monitor
        from schemas.tap_monitors import TapMonitorCreate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        monitor_data = TapMonitorCreate(
            name="Kegtron Monitor",
            monitor_type="kegtron-pro",
            location_id="loc-1",
        )

        with pytest.raises(HTTPException) as exc_info:
            run_async(create_tap_monitor(monitor_data, None, mock_auth_user, mock_session))

        assert exc_info.value.status_code == 400

    def test_passes_with_all_required_meta(self):
        """Test kegtron-pro creation succeeds with all required meta fields"""
        from routers.tap_monitors import create_tap_monitor
        from schemas.tap_monitors import TapMonitorCreate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()
        monitor_data = TapMonitorCreate(
            name="Kegtron Monitor",
            monitor_type="kegtron-pro",
            location_id="loc-1",
            meta={"portNum": 0, "deviceId": "dev-1", "accessToken": "tok123"},
        )

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.TapMonitorService") as mock_service:
            mock_db.query = AsyncMock(return_value=[])
            mock_db.create = AsyncMock(return_value=mock_monitor)
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            result = run_async(create_tap_monitor(monitor_data, None, mock_auth_user, mock_session))

            mock_db.create.assert_called_once()

    def test_non_kegtron_type_skips_validation(self):
        """Test non-kegtron-pro types are not subject to kegtron meta validation"""
        from routers.tap_monitors import create_tap_monitor
        from schemas.tap_monitors import TapMonitorCreate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()
        monitor_data = TapMonitorCreate(
            name="Plaato Monitor",
            monitor_type="open-plaato-keg",
            location_id="loc-1",
            meta={"deviceId": "dev-1"},
        )

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.TapMonitorService") as mock_service:
            mock_db.query = AsyncMock(return_value=[])
            mock_db.create = AsyncMock(return_value=mock_monitor)
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            result = run_async(create_tap_monitor(monitor_data, None, mock_auth_user, mock_session))

            mock_db.create.assert_called_once()


class TestUpdateKegtronProValidation:
    """Tests for kegtron-pro meta validation on update"""

    def test_raises_400_when_updating_meta_missing_required_fields(self):
        """Test raises 400 when updating kegtron-pro meta without required fields"""
        from routers.tap_monitors import update_tap_monitor
        from schemas.tap_monitors import TapMonitorUpdate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor(monitor_type="kegtron-pro", location_id="loc-1")
        update_data = TapMonitorUpdate(meta={"portNum": None, "deviceId": ""})

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)

            with pytest.raises(HTTPException) as exc_info:
                run_async(update_tap_monitor("monitor-1", update_data, None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 400
            assert "device_id" in exc_info.value.detail
            assert "port_num" in exc_info.value.detail

    def test_passes_when_updating_meta_with_all_required_fields(self):
        """Test kegtron-pro update succeeds when meta has all required fields"""
        from routers.tap_monitors import update_tap_monitor
        from schemas.tap_monitors import TapMonitorUpdate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor(monitor_type="kegtron-pro", location_id="loc-1")
        update_data = TapMonitorUpdate(
            meta={"portNum": 1, "deviceId": "dev-1", "accessToken": "tok"},
        )

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.TapMonitorService") as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_db.update = AsyncMock()
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            result = run_async(update_tap_monitor("monitor-1", update_data, None, mock_auth_user, mock_session))

            mock_db.update.assert_called_once()

    def test_skips_validation_when_meta_not_in_update(self):
        """Test no validation when only updating name (no meta)"""
        from routers.tap_monitors import update_tap_monitor
        from schemas.tap_monitors import TapMonitorUpdate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor(monitor_type="kegtron-pro", location_id="loc-1")
        update_data = TapMonitorUpdate(name="Renamed Monitor")

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.TapMonitorService") as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_db.update = AsyncMock()
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            result = run_async(update_tap_monitor("monitor-1", update_data, None, mock_auth_user, mock_session))

            mock_db.update.assert_called_once()

    def test_raises_400_if_monitor_type_changes(self):
        """Test validates meta when monitor_type is being changed to kegtron-pro"""
        from routers.tap_monitors import update_tap_monitor
        from schemas.tap_monitors import TapMonitorUpdate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor(monitor_type="open-plaato-keg", location_id="loc-1")
        update_data = TapMonitorUpdate(
            monitor_type="kegtron-pro",
            meta={"portNum": 0},
        )

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)

            with pytest.raises(HTTPException) as exc_info:
                run_async(update_tap_monitor("monitor-1", update_data, None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 400

    def test_skips_validation_for_non_kegtron_type(self):
        """Test no kegtron validation when updating a non-kegtron monitor's meta"""
        from routers.tap_monitors import update_tap_monitor
        from schemas.tap_monitors import TapMonitorUpdate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor(monitor_type="open-plaato-keg", location_id="loc-1")
        update_data = TapMonitorUpdate(meta={"deviceId": "dev-1"})

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.TapMonitorService") as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_db.update = AsyncMock()
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            result = run_async(update_tap_monitor("monitor-1", update_data, None, mock_auth_user, mock_session))

            mock_db.update.assert_called_once()


class TestValidateKegtronProMeta:
    """Direct tests for _validate_kegtron_pro_meta helper"""

    def test_all_fields_present(self):
        """No exception when all required fields are present"""
        from routers.tap_monitors import _validate_kegtron_pro_meta

        _validate_kegtron_pro_meta({"port_num": 0, "device_id": "dev", "access_token": "tok"})

    def test_empty_meta_raises(self):
        """Raises HTTPException for empty meta"""
        from routers.tap_monitors import _validate_kegtron_pro_meta

        with pytest.raises(HTTPException) as exc_info:
            _validate_kegtron_pro_meta({})

        assert exc_info.value.status_code == 400
        assert "port_num" in exc_info.value.detail
        assert "device_id" in exc_info.value.detail
        assert "access_token" in exc_info.value.detail

    def test_partial_meta_lists_only_missing(self):
        """Only missing fields are listed in the error"""
        from routers.tap_monitors import _validate_kegtron_pro_meta

        with pytest.raises(HTTPException) as exc_info:
            _validate_kegtron_pro_meta({"port_num": 0})

        assert exc_info.value.status_code == 400
        assert "port_num" not in exc_info.value.detail
        assert "device_id" in exc_info.value.detail
        assert "access_token" in exc_info.value.detail

    def test_empty_string_treated_as_missing(self):
        """Empty string values are treated as missing"""
        from routers.tap_monitors import _validate_kegtron_pro_meta

        with pytest.raises(HTTPException) as exc_info:
            _validate_kegtron_pro_meta({"port_num": 0, "device_id": "", "access_token": None})

        assert exc_info.value.status_code == 400
        assert "port_num" not in exc_info.value.detail
        assert "device_id" in exc_info.value.detail
        assert "access_token" in exc_info.value.detail

    def test_zero_port_num_is_valid(self):
        """port_num of 0 is a valid value"""
        from routers.tap_monitors import _validate_kegtron_pro_meta

        _validate_kegtron_pro_meta({"port_num": 0, "device_id": "dev", "access_token": "tok"})


class TestGetTapMonitor:
    """Tests for get_tap_monitor endpoint"""

    def test_gets_tap_monitor_by_id(self):
        """Test gets tap monitor by ID"""
        from routers.tap_monitors import get_tap_monitor

        mock_request = create_mock_request()
        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-1"])
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor(location_id="loc-1")

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.TapMonitorService") as mock_service:
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

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db:
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

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_tap_monitor(mock_request, "monitor-1", None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 403

    def test_include_tap_details(self):
        """Test includes tap details when requested"""
        from routers.tap_monitors import get_tap_monitor

        mock_request = create_mock_request(query_params={"include_tap_details": "true"})
        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.TapMonitorService") as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            run_async(get_tap_monitor(mock_request, "monitor-1", None, mock_auth_user, mock_session))

            mock_service.transform_response.assert_called_with(mock_monitor, db_session=mock_session, include_tap=True)

    @pytest.mark.parametrize("param_value", ["true", "yes", "", "1", "True", "YES", "TRUE"])
    def test_include_tap_details_truthy_values(self, param_value):
        """Test that various truthy values for include_tap_details pass include_tap=True"""
        from routers.tap_monitors import get_tap_monitor

        mock_request = create_mock_request(query_params={"include_tap_details": param_value})
        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.TapMonitorService") as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            run_async(get_tap_monitor(mock_request, "monitor-1", None, mock_auth_user, mock_session))

            mock_service.transform_response.assert_called_with(mock_monitor, db_session=mock_session, include_tap=True)

    @pytest.mark.parametrize("param_value", ["false", "no", "0", "random"])
    def test_include_tap_details_falsy_values(self, param_value):
        """Test that non-truthy values for include_tap_details pass include_tap=False"""
        from routers.tap_monitors import get_tap_monitor

        mock_request = create_mock_request(query_params={"include_tap_details": param_value})
        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.TapMonitorService") as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            run_async(get_tap_monitor(mock_request, "monitor-1", None, mock_auth_user, mock_session))

            mock_service.transform_response.assert_called_with(mock_monitor, db_session=mock_session, include_tap=False)

    def test_include_tap_details_defaults_to_false(self):
        """Test that include_tap_details defaults to False when not provided"""
        from routers.tap_monitors import get_tap_monitor

        mock_request = create_mock_request()
        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.TapMonitorService") as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            run_async(get_tap_monitor(mock_request, "monitor-1", None, mock_auth_user, mock_session))

            mock_service.transform_response.assert_called_with(mock_monitor, db_session=mock_session, include_tap=False)


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

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.TapMonitorService") as mock_service:
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

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db:
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

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_monitor_db, patch("routers.tap_monitors.TapsDB") as mock_taps_db:
            mock_monitor_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_monitor_db.delete = AsyncMock()
            mock_taps_db.query = AsyncMock(return_value=[])

            result = run_async(delete_tap_monitor("monitor-1", None, mock_auth_user, mock_session))

            mock_monitor_db.delete.assert_called_once()

    def test_deletes_tap_monitor_updates_taps(self):
        """Test deletes tap monitor and updates associated taps"""
        from routers.tap_monitors import delete_tap_monitor

        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-1"])
        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor(location_id="loc-1")
        mock_tap = MagicMock(id="tap-1")

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_monitor_db, patch("routers.tap_monitors.TapsDB") as mock_taps_db:
            mock_monitor_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_monitor_db.delete = AsyncMock()
            mock_taps_db.query = AsyncMock(return_value=[mock_tap])
            mock_taps_db.update = AsyncMock()

            result = run_async(delete_tap_monitor("monitor-1", None, mock_auth_user, mock_session))

            mock_taps_db.update.assert_called_once_with(mock_session, "tap-1", tap_monitor_id=None)

    def test_raises_404_when_not_found(self):
        """Test raises 404 when tap monitor not found"""
        from routers.tap_monitors import delete_tap_monitor

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db:
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

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.get_tap_monitor_lib") as mock_get_lib:
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

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db:
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

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.get_tap_monitor_lib") as mock_get_lib:
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

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_specific_tap_monitor_data("unknown", "percent_left", None, mock_session))

            assert exc_info.value.status_code == 404

    def test_raises_400_for_invalid_data_type(self):
        """Test raises 400 for invalid data type"""
        from lib.tap_monitors import InvalidDataType
        from routers.tap_monitors import get_specific_tap_monitor_data

        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor(monitor_type="plaato_keg")

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.get_tap_monitor_lib") as mock_get_lib:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_lib = MagicMock()
            mock_lib.get = AsyncMock(side_effect=InvalidDataType("Invalid data type"))
            mock_get_lib.return_value = mock_lib

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_specific_tap_monitor_data("monitor-1", "invalid", None, mock_session))

            assert exc_info.value.status_code == 400

    def test_gets_online_status_calls_is_online(self):
        """Test getting 'online' data type calls is_online method"""
        from routers.tap_monitors import get_specific_tap_monitor_data

        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor(monitor_type="plaato_keg")

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.get_tap_monitor_lib") as mock_get_lib:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_lib = MagicMock()
            mock_lib.is_online = AsyncMock(return_value=True)
            mock_lib.get = AsyncMock()
            mock_get_lib.return_value = mock_lib

            result = run_async(get_specific_tap_monitor_data("monitor-1", "online", None, mock_session))

            assert result is True
            mock_lib.is_online.assert_called_once_with(monitor=mock_monitor, db_session=mock_session)
            mock_lib.get.assert_not_called()

    def test_gets_online_status_returns_false(self):
        """Test getting 'online' data type when device is offline"""
        from routers.tap_monitors import get_specific_tap_monitor_data

        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor(monitor_type="plaato_keg")

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.get_tap_monitor_lib") as mock_get_lib:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_lib = MagicMock()
            mock_lib.is_online = AsyncMock(return_value=False)
            mock_get_lib.return_value = mock_lib

            result = run_async(get_specific_tap_monitor_data("monitor-1", "online", None, mock_session))

            assert result is False


class TestGetTapMonitorDataWithOnlineFields:
    """Tests for get_tap_monitor_data endpoint with online and last_updated_on fields"""

    def test_returns_online_field(self):
        """Test returns online field in tap monitor data"""
        from routers.tap_monitors import get_tap_monitor_data

        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor(monitor_type="plaato_keg")

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.get_tap_monitor_lib") as mock_get_lib:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_lib = MagicMock()
            mock_lib.get_all = AsyncMock(
                return_value={
                    "percentRemaining": 75.5,
                    "online": True,
                }
            )
            mock_get_lib.return_value = mock_lib

            result = run_async(get_tap_monitor_data("monitor-1", None, mock_session))

            assert "online" in result
            assert result["online"] is True

    def test_returns_last_updated_on_field(self):
        """Test returns last_updated_on field in tap monitor data"""
        from routers.tap_monitors import get_tap_monitor_data

        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor(monitor_type="plaato_keg")

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.get_tap_monitor_lib") as mock_get_lib:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_lib = MagicMock()
            mock_lib.get_all = AsyncMock(
                return_value={
                    "percentRemaining": 75.5,
                    "lastUpdatedOn": 1707307200.0,
                }
            )
            mock_get_lib.return_value = mock_lib

            result = run_async(get_tap_monitor_data("monitor-1", None, mock_session))

            assert "lastUpdatedOn" in result
            assert result["lastUpdatedOn"] == 1707307200.0

    def test_returns_both_online_and_last_updated_on(self):
        """Test returns both online and last_updated_on fields"""
        from routers.tap_monitors import get_tap_monitor_data

        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor(monitor_type="plaato_keg")

        with patch("routers.tap_monitors.TapMonitorsDB") as mock_db, patch("routers.tap_monitors.get_tap_monitor_lib") as mock_get_lib:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_lib = MagicMock()
            mock_lib.get_all = AsyncMock(
                return_value={
                    "percentRemaining": 75.5,
                    "totalVolumeRemaining": 10.5,
                    "displayVolumeUnit": "L",
                    "online": True,
                    "lastUpdatedOn": 1707307200.0,
                }
            )
            mock_get_lib.return_value = mock_lib

            result = run_async(get_tap_monitor_data("monitor-1", None, mock_session))

            assert result["percentRemaining"] == 75.5
            assert result["online"] is True
            assert result["lastUpdatedOn"] == 1707307200.0


class TestListMonitorTypesWithOnlineStatus:
    """Tests for list_monitor_types endpoint with reports_online_status field"""

    def test_includes_reports_online_status(self):
        """Test includes reports_online_status in monitor type response"""
        from routers.tap_monitors import list_monitor_types

        mock_auth_user = create_mock_auth_user()
        mock_types = [
            {"type": "plaato_keg", "supports_discovery": False, "reports_online_status": True},
            {"type": "kegtron", "supports_discovery": True, "reports_online_status": False},
        ]

        with patch("routers.tap_monitors.get_tap_monitor_types", return_value=mock_types), patch("routers.tap_monitors.TapMonitorTypeService") as mock_service:
            mock_service.transform_response = AsyncMock(
                side_effect=[
                    {"type": "plaato_keg", "supportsDiscovery": False, "reportsOnlineStatus": True},
                    {"type": "kegtron", "supportsDiscovery": True, "reportsOnlineStatus": False},
                ]
            )

            result = run_async(list_monitor_types(mock_auth_user))

            assert len(result) == 2
            assert result[0]["reportsOnlineStatus"] is True
            assert result[1]["reportsOnlineStatus"] is False
