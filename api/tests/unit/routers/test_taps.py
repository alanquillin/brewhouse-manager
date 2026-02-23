"""Tests for routers/taps.py module - Taps router"""

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


def create_mock_tap(id_="tap-1", tap_number=1, location_id="loc-1", on_tap_id=None):
    """Helper to create mock tap"""
    mock = MagicMock()
    mock.id = id_
    mock.tap_number = tap_number
    mock.location_id = location_id
    mock.on_tap_id = on_tap_id
    mock.on_tap = None

    async def _awaitable_on_tap():
        return mock.on_tap

    mock.awaitable_attrs = MagicMock()
    mock.awaitable_attrs.on_tap = _awaitable_on_tap()

    return mock


class TestGetLocationId:
    """Tests for get_location_id helper"""

    def test_returns_uuid_unchanged(self):
        """Test returns valid UUID unchanged"""
        from routers.taps import get_location_id

        mock_session = AsyncMock()
        uuid_str = "123e4567-e89b-12d3-a456-426614174000"

        with patch("routers.util.is_valid_uuid", return_value=True):
            result = run_async(get_location_id(uuid_str, mock_session))

        assert result == uuid_str

    def test_looks_up_by_name(self):
        """Test looks up location by name"""
        from db.locations import Locations as LocationsDB
        from routers.taps import get_location_id

        mock_session = AsyncMock()
        mock_location = MagicMock(id="loc-abc")

        with patch("routers.util.is_valid_uuid", return_value=False), patch.object(LocationsDB, "query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = [mock_location]

            result = run_async(get_location_id("Test Location", mock_session))

        assert result == "loc-abc"


class TestListTaps:
    """Tests for list_taps endpoint"""

    def test_admin_lists_all_taps(self):
        """Test admin can list all taps"""
        from routers.taps import list_taps

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_tap = create_mock_tap()

        with patch("routers.taps.TapsDB") as mock_db, patch("routers.taps.TapService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_tap])
            mock_service.transform_response = AsyncMock(return_value={"id": "tap-1"})

            result = run_async(list_taps(None, mock_auth_user, mock_session))

            mock_db.query.assert_called_once_with(mock_session)
            assert len(result) == 1

    def test_non_admin_lists_own_location_taps(self):
        """Test non-admin lists only taps in their locations"""
        from routers.taps import list_taps

        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-1", "loc-2"])
        mock_session = AsyncMock()
        mock_tap = create_mock_tap()

        with patch("routers.taps.TapsDB") as mock_db, patch("routers.taps.TapService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_tap])
            mock_service.transform_response = AsyncMock(return_value={"id": "tap-1"})

            result = run_async(list_taps(None, mock_auth_user, mock_session))

            mock_db.query.assert_called_once_with(mock_session, locations=["loc-1", "loc-2"])

    def test_filters_by_location(self):
        """Test filters taps by location parameter"""
        from routers.taps import list_taps

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_tap = create_mock_tap()

        with patch("routers.taps.get_location_id", new_callable=AsyncMock) as mock_get_loc, patch("routers.taps.TapsDB") as mock_db, patch(
            "routers.taps.TapService"
        ) as mock_service:
            mock_get_loc.return_value = "loc-1"
            mock_db.query = AsyncMock(return_value=[mock_tap])
            mock_service.transform_response = AsyncMock(return_value={"id": "tap-1"})

            result = run_async(list_taps("loc-1", mock_auth_user, mock_session))

            mock_db.query.assert_called_once_with(mock_session, locations=["loc-1"])

    def test_raises_403_for_unauthorized_location(self):
        """Test raises 403 when user not authorized for location"""
        from routers.taps import list_taps

        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-other"])
        mock_session = AsyncMock()

        with patch("routers.taps.get_location_id", new_callable=AsyncMock) as mock_get_loc:
            mock_get_loc.return_value = "loc-1"

            with pytest.raises(HTTPException) as exc_info:
                run_async(list_taps("loc-1", mock_auth_user, mock_session))

            assert exc_info.value.status_code == 403


class TestCreateTap:
    """Tests for create_tap endpoint"""

    def test_creates_tap(self):
        """Test creates tap successfully"""
        from routers.taps import create_tap
        from schemas.taps import TapCreate

        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-1"])
        mock_session = AsyncMock()
        mock_tap = create_mock_tap()
        tap_data = TapCreate(tap_number=1, location_id="loc-1")

        with patch("routers.taps.TapsDB") as mock_db, patch("routers.taps.TapService") as mock_service:
            mock_db.create = AsyncMock(return_value=mock_tap)
            mock_service.transform_response = AsyncMock(return_value={"id": "tap-1"})

            result = run_async(create_tap(tap_data, None, mock_auth_user, mock_session))

            mock_db.create.assert_called_once()

    def test_creates_tap_with_batch(self):
        """Test creates tap with batch creates on_tap entry"""
        from routers.taps import create_tap
        from schemas.taps import TapCreate

        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-1"])
        mock_session = AsyncMock()
        mock_tap = create_mock_tap()
        mock_batch = MagicMock(id="batch-1")
        mock_on_tap = MagicMock(id="on-tap-1")
        tap_data = TapCreate(tap_number=1, location_id="loc-1", batch_id="batch-1")

        with patch("routers.taps.TapsDB") as mock_taps_db, patch("routers.taps.BatchesDB") as mock_batches_db, patch(
            "routers.taps.OnTapDB"
        ) as mock_on_tap_db, patch("routers.taps.TapService") as mock_service:
            mock_batches_db.get_by_pkey = AsyncMock(return_value=mock_batch)
            mock_on_tap_db.create = AsyncMock(return_value=mock_on_tap)
            mock_taps_db.create = AsyncMock(return_value=mock_tap)
            mock_service.transform_response = AsyncMock(return_value={"id": "tap-1"})

            result = run_async(create_tap(tap_data, None, mock_auth_user, mock_session))

            mock_on_tap_db.create.assert_called_once()

    def test_raises_403_for_unauthorized_location(self):
        """Test raises 403 when creating tap in unauthorized location"""
        from routers.taps import create_tap
        from schemas.taps import TapCreate

        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-other"])
        mock_session = AsyncMock()
        tap_data = TapCreate(tap_number=1, location_id="loc-1")

        with pytest.raises(HTTPException) as exc_info:
            run_async(create_tap(tap_data, None, mock_auth_user, mock_session))

        assert exc_info.value.status_code == 403


class TestCreateTapMonitorValidation:
    """Tests for tap monitor validation in create_tap endpoint"""

    def test_raises_404_for_nonexistent_tap_monitor(self):
        """Test raises 404 when tap monitor ID does not exist"""
        from routers.taps import create_tap
        from schemas.taps import TapCreate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        tap_data = TapCreate(tap_number=1, location_id="loc-1", tap_monitor_id="nonexistent-monitor")

        with patch("routers.taps.TapMonitorsDB") as mock_monitors_db:
            mock_monitors_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(create_tap(tap_data, None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404
            assert "tap monitor not found" in exc_info.value.detail.lower()

    def test_raises_400_for_unsupported_tap_monitor(self):
        """Test raises 400 when tap monitor has unsupported type"""
        from routers.taps import create_tap
        from schemas.taps import TapCreate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_monitor = MagicMock(id="monitor-1", monitor_type="unsupported-type", location_id="loc-1")
        tap_data = TapCreate(tap_number=1, location_id="loc-1", tap_monitor_id="monitor-1")

        with patch("routers.taps.TapMonitorsDB") as mock_monitors_db, patch("routers.taps.get_tap_monitor_lib", return_value=None):
            mock_monitors_db.get_by_pkey = AsyncMock(return_value=mock_monitor)

            with pytest.raises(HTTPException) as exc_info:
                run_async(create_tap(tap_data, None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 400
            assert "unsupported" in exc_info.value.detail.lower()
            assert "unsupported-type" in exc_info.value.detail.lower()

    def test_raises_400_for_tap_monitor_location_mismatch(self):
        """Test raises 400 when tap monitor is at a different location than the tap"""
        from routers.taps import create_tap
        from schemas.taps import TapCreate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_monitor = MagicMock(id="monitor-1", monitor_type="open-plaato-keg", location_id="loc-other")
        tap_data = TapCreate(tap_number=1, location_id="loc-1", tap_monitor_id="monitor-1")

        with patch("routers.taps.TapMonitorsDB") as mock_monitors_db, patch("routers.taps.get_tap_monitor_lib", return_value=MagicMock()):
            mock_monitors_db.get_by_pkey = AsyncMock(return_value=mock_monitor)

            with pytest.raises(HTTPException) as exc_info:
                run_async(create_tap(tap_data, None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 400
            assert "not associated with this location" in exc_info.value.detail.lower()

    def test_creates_tap_with_supported_tap_monitor(self):
        """Test successfully creates tap with a supported tap monitor"""
        from routers.taps import create_tap
        from schemas.taps import TapCreate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_tap = create_mock_tap()
        mock_monitor = MagicMock(id="monitor-1", monitor_type="open-plaato-keg", location_id="loc-1")
        tap_data = TapCreate(tap_number=1, location_id="loc-1", tap_monitor_id="monitor-1")

        with patch("routers.taps.TapMonitorsDB") as mock_monitors_db, patch("routers.taps.get_tap_monitor_lib", return_value=MagicMock()), patch(
            "routers.taps.TapsDB"
        ) as mock_db, patch("routers.taps.TapService") as mock_service:
            mock_monitors_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_db.create = AsyncMock(return_value=mock_tap)
            mock_service.transform_response = AsyncMock(return_value={"id": "tap-1"})

            result = run_async(create_tap(tap_data, None, mock_auth_user, mock_session))

            assert result["id"] == "tap-1"
            mock_db.create.assert_called_once()

    def test_skips_validation_when_no_tap_monitor_id(self):
        """Test skips tap monitor validation when tap_monitor_id is not provided"""
        from routers.taps import create_tap
        from schemas.taps import TapCreate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_tap = create_mock_tap()
        tap_data = TapCreate(tap_number=1, location_id="loc-1")

        with patch("routers.taps.TapMonitorsDB") as mock_monitors_db, patch("routers.taps.TapsDB") as mock_db, patch(
            "routers.taps.TapService"
        ) as mock_service:
            mock_db.create = AsyncMock(return_value=mock_tap)
            mock_service.transform_response = AsyncMock(return_value={"id": "tap-1"})

            result = run_async(create_tap(tap_data, None, mock_auth_user, mock_session))

            assert result["id"] == "tap-1"
            mock_monitors_db.get_by_pkey.assert_not_called()


class TestGetTap:
    """Tests for get_tap endpoint"""

    def test_gets_tap_by_id(self):
        """Test gets tap by ID"""
        from routers.taps import get_tap

        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-1"])
        mock_session = AsyncMock()
        mock_tap = create_mock_tap(location_id="loc-1")

        with patch("routers.taps.TapsDB") as mock_db, patch("routers.taps.TapService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_tap])
            mock_service.transform_response = AsyncMock(return_value={"id": "tap-1"})

            result = run_async(get_tap("tap-1", None, mock_auth_user, mock_session))

            assert result["id"] == "tap-1"

    def test_raises_404_when_not_found(self):
        """Test raises 404 when tap not found"""
        from routers.taps import get_tap

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()

        with patch("routers.taps.TapsDB") as mock_db:
            mock_db.query = AsyncMock(return_value=[])

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_tap("unknown", None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404

    def test_raises_403_for_unauthorized_tap(self):
        """Test raises 403 when user not authorized for tap's location"""
        from routers.taps import get_tap

        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-other"])
        mock_session = AsyncMock()
        mock_tap = create_mock_tap(location_id="loc-1")

        with patch("routers.taps.TapsDB") as mock_db:
            mock_db.query = AsyncMock(return_value=[mock_tap])

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_tap("tap-1", None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 403


class TestUpdateTap:
    """Tests for update_tap endpoint"""

    def test_updates_tap(self):
        """Test updates tap successfully"""
        from routers.taps import update_tap
        from schemas.taps import TapUpdate

        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-1"])
        mock_session = AsyncMock()
        mock_tap = create_mock_tap(location_id="loc-1")
        update_data = TapUpdate(tap_number=2)

        with patch("routers.taps.TapsDB") as mock_db, patch("routers.taps.TapService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_tap])
            mock_db.update = AsyncMock()
            mock_db.get_by_pkey = AsyncMock(return_value=mock_tap)
            mock_service.transform_response = AsyncMock(return_value={"id": "tap-1"})

            result = run_async(update_tap("tap-1", update_data, None, mock_auth_user, mock_session))

            mock_db.update.assert_called_once()

    def test_raises_404_when_not_found(self):
        """Test raises 404 when tap not found"""
        from routers.taps import update_tap
        from schemas.taps import TapUpdate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        update_data = TapUpdate(tap_number=2)

        with patch("routers.taps.TapsDB") as mock_db:
            mock_db.query = AsyncMock(return_value=[])

            with pytest.raises(HTTPException) as exc_info:
                run_async(update_tap("unknown", update_data, None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404


class TestUpdateTapMonitorValidation:
    """Tests for tap monitor validation in update_tap endpoint"""

    def test_raises_404_for_nonexistent_tap_monitor(self):
        """Test raises 404 when tap monitor ID does not exist"""
        from routers.taps import update_tap
        from schemas.taps import TapUpdate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_tap = create_mock_tap(location_id="loc-1")
        update_data = TapUpdate(tap_monitor_id="nonexistent-monitor")

        with patch("routers.taps.TapsDB") as mock_db, patch("routers.taps.TapMonitorsDB") as mock_monitors_db:
            mock_db.query = AsyncMock(return_value=[mock_tap])
            mock_monitors_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(update_tap("tap-1", update_data, None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404
            assert "tap monitor not found" in exc_info.value.detail.lower()

    def test_raises_400_for_unsupported_tap_monitor(self):
        """Test raises 400 when tap monitor has unsupported type"""
        from routers.taps import update_tap
        from schemas.taps import TapUpdate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_tap = create_mock_tap(location_id="loc-1")
        mock_monitor = MagicMock(id="monitor-1", monitor_type="unsupported-type", location_id="loc-1")
        update_data = TapUpdate(tap_monitor_id="monitor-1")

        with patch("routers.taps.TapsDB") as mock_db, patch("routers.taps.TapMonitorsDB") as mock_monitors_db, patch(
            "routers.taps.get_tap_monitor_lib", return_value=None
        ):
            mock_db.query = AsyncMock(return_value=[mock_tap])
            mock_monitors_db.get_by_pkey = AsyncMock(return_value=mock_monitor)

            with pytest.raises(HTTPException) as exc_info:
                run_async(update_tap("tap-1", update_data, None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 400
            assert "unsupported" in exc_info.value.detail.lower()
            assert "unsupported-type" in exc_info.value.detail.lower()

    def test_raises_400_for_tap_monitor_location_mismatch(self):
        """Test raises 400 when tap monitor is at a different location than the tap"""
        from routers.taps import update_tap
        from schemas.taps import TapUpdate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_tap = create_mock_tap(location_id="loc-1")
        mock_monitor = MagicMock(id="monitor-1", monitor_type="open-plaato-keg", location_id="loc-other")
        update_data = TapUpdate(tap_monitor_id="monitor-1")

        with patch("routers.taps.TapsDB") as mock_db, patch("routers.taps.TapMonitorsDB") as mock_monitors_db, patch(
            "routers.taps.get_tap_monitor_lib", return_value=MagicMock()
        ):
            mock_db.query = AsyncMock(return_value=[mock_tap])
            mock_monitors_db.get_by_pkey = AsyncMock(return_value=mock_monitor)

            with pytest.raises(HTTPException) as exc_info:
                run_async(update_tap("tap-1", update_data, None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 400
            assert "not associated with this location" in exc_info.value.detail.lower()

    def test_updates_tap_with_supported_tap_monitor(self):
        """Test successfully updates tap with a supported tap monitor"""
        from routers.taps import update_tap
        from schemas.taps import TapUpdate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_tap = create_mock_tap(location_id="loc-1")
        mock_monitor = MagicMock(id="monitor-1", monitor_type="open-plaato-keg", location_id="loc-1")
        update_data = TapUpdate(tap_monitor_id="monitor-1")

        with patch("routers.taps.TapsDB") as mock_db, patch("routers.taps.TapMonitorsDB") as mock_monitors_db, patch(
            "routers.taps.get_tap_monitor_lib", return_value=MagicMock()
        ), patch("routers.taps.TapService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_tap])
            mock_db.update = AsyncMock()
            mock_db.get_by_pkey = AsyncMock(return_value=mock_tap)
            mock_monitors_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_service.transform_response = AsyncMock(return_value={"id": "tap-1"})

            result = run_async(update_tap("tap-1", update_data, None, mock_auth_user, mock_session))

            assert result["id"] == "tap-1"
            mock_db.update.assert_called_once()

    def test_skips_validation_when_no_tap_monitor_id(self):
        """Test skips tap monitor validation when tap_monitor_id is not in update"""
        from routers.taps import update_tap
        from schemas.taps import TapUpdate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_tap = create_mock_tap(location_id="loc-1")
        update_data = TapUpdate(description="Updated description")

        with patch("routers.taps.TapsDB") as mock_db, patch("routers.taps.TapMonitorsDB") as mock_monitors_db, patch(
            "routers.taps.TapService"
        ) as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_tap])
            mock_db.update = AsyncMock()
            mock_db.get_by_pkey = AsyncMock(return_value=mock_tap)
            mock_service.transform_response = AsyncMock(return_value={"id": "tap-1"})

            result = run_async(update_tap("tap-1", update_data, None, mock_auth_user, mock_session))

            assert result["id"] == "tap-1"
            mock_monitors_db.get_by_pkey.assert_not_called()


class TestDeleteTap:
    """Tests for delete_tap endpoint"""

    def test_deletes_tap(self):
        """Test deletes tap successfully"""
        from routers.taps import delete_tap

        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-1"])
        mock_session = AsyncMock()
        mock_tap = create_mock_tap(location_id="loc-1", on_tap_id=None)

        with patch("routers.taps.TapsDB") as mock_taps_db:
            mock_taps_db.query = AsyncMock(return_value=[mock_tap])
            mock_taps_db.delete = AsyncMock()

            result = run_async(delete_tap("tap-1", None, mock_auth_user, mock_session))

            mock_taps_db.delete.assert_called_once()

    def test_deletes_tap_with_on_tap(self):
        """Test deletes tap and associated on_tap entry"""
        from routers.taps import delete_tap

        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-1"])
        mock_session = AsyncMock()
        mock_tap = create_mock_tap(location_id="loc-1", on_tap_id="on-tap-1")

        with patch("routers.taps.TapsDB") as mock_taps_db, patch("routers.taps.OnTapDB") as mock_on_tap_db:
            mock_taps_db.query = AsyncMock(return_value=[mock_tap])
            mock_taps_db.delete = AsyncMock()
            mock_on_tap_db.delete = AsyncMock()

            result = run_async(delete_tap("tap-1", None, mock_auth_user, mock_session))

            mock_on_tap_db.delete.assert_called_once_with(mock_session, "on-tap-1")

    def test_raises_404_when_not_found(self):
        """Test raises 404 when tap not found"""
        from routers.taps import delete_tap

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()

        with patch("routers.taps.TapsDB") as mock_db:
            mock_db.query = AsyncMock(return_value=[])

            with pytest.raises(HTTPException) as exc_info:
                run_async(delete_tap("unknown", None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404

    def test_raises_403_for_unauthorized_tap(self):
        """Test raises 403 when user not authorized for tap's location"""
        from routers.taps import delete_tap

        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-other"])
        mock_session = AsyncMock()
        mock_tap = create_mock_tap(location_id="loc-1")

        with patch("routers.taps.TapsDB") as mock_db:
            mock_db.query = AsyncMock(return_value=[mock_tap])

            with pytest.raises(HTTPException) as exc_info:
                run_async(delete_tap("tap-1", None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 403
