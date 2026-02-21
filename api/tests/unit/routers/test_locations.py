"""Tests for routers/locations.py module - Locations router"""

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


def create_mock_location(id_="loc-1", name="Test Location"):
    """Helper to create mock location"""
    mock = MagicMock()
    mock.id = id_
    mock.name = name
    return mock


class TestListLocations:
    """Tests for list_locations endpoint"""

    def test_admin_gets_all_locations(self):
        """Test admin user gets all locations"""
        from routers.locations import list_locations

        mock_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_location = create_mock_location()

        with patch("routers.locations.LocationsDB") as mock_db, patch("routers.locations.LocationService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_location])
            mock_service.transform_response = AsyncMock(return_value={"id": "loc-1"})

            result = run_async(list_locations(mock_user, mock_session))

            # Admin should query without location filter
            mock_db.query.assert_called_once_with(mock_session)
            assert len(result) == 1

    def test_non_admin_gets_own_locations(self):
        """Test non-admin user gets only their locations"""
        from routers.locations import list_locations

        mock_user = create_mock_auth_user(admin=False, locations=["loc-1", "loc-2"])
        mock_session = AsyncMock()
        mock_location = create_mock_location()

        with patch("routers.locations.LocationsDB") as mock_db, patch("routers.locations.LocationService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_location])
            mock_service.transform_response = AsyncMock(return_value={"id": "loc-1"})

            result = run_async(list_locations(mock_user, mock_session))

            # Non-admin should filter by their locations
            mock_db.query.assert_called_once_with(mock_session, ids=["loc-1", "loc-2"])


class TestCreateLocation:
    """Tests for create_location endpoint"""

    def test_creates_location(self):
        """Test creates location successfully"""
        from routers.locations import create_location
        from schemas.locations import LocationCreate

        mock_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_location = create_mock_location()
        location_data = LocationCreate(name="New Location")

        with patch("routers.locations.LocationsDB") as mock_db, patch("routers.locations.LocationService") as mock_service:
            mock_db.create = AsyncMock(return_value=mock_location)
            mock_service.transform_response = AsyncMock(return_value={"id": "loc-1", "name": "New Location"})

            result = run_async(create_location(location_data, mock_user, mock_session))

            mock_db.create.assert_called_once()
            assert result["name"] == "New Location"


class TestGetLocation:
    """Tests for get_location endpoint"""

    def test_gets_location_by_id(self):
        """Test gets location by ID"""
        from routers.locations import get_location

        mock_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_location = create_mock_location(id_="loc-1")

        with patch("routers.locations.get_location_id", new_callable=AsyncMock) as mock_get_id, patch("routers.locations.LocationsDB") as mock_db, patch(
            "routers.locations.LocationService"
        ) as mock_service:
            mock_get_id.return_value = "loc-1"
            mock_db.get_by_pkey = AsyncMock(return_value=mock_location)
            mock_service.transform_response = AsyncMock(return_value={"id": "loc-1"})

            result = run_async(get_location("loc-1", mock_user, mock_session))

            assert result["id"] == "loc-1"

    def test_raises_404_when_id_not_found(self):
        """Test raises 404 when location ID not found"""
        from routers.locations import get_location

        mock_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()

        with patch("routers.locations.get_location_id", new_callable=AsyncMock) as mock_get_id:
            mock_get_id.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_location("unknown", mock_user, mock_session))

            assert exc_info.value.status_code == 404

    def test_raises_404_when_location_not_found(self):
        """Test raises 404 when location not in database"""
        from routers.locations import get_location

        mock_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()

        with patch("routers.locations.get_location_id", new_callable=AsyncMock) as mock_get_id, patch("routers.locations.LocationsDB") as mock_db:
            mock_get_id.return_value = "loc-1"
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_location("loc-1", mock_user, mock_session))

            assert exc_info.value.status_code == 404

    def test_raises_403_for_unauthorized_location(self):
        """Test raises 403 when user not authorized for location"""
        from routers.locations import get_location

        mock_user = create_mock_auth_user(admin=False, locations=["loc-other"])
        mock_session = AsyncMock()
        mock_location = create_mock_location(id_="loc-1")

        with patch("routers.locations.get_location_id", new_callable=AsyncMock) as mock_get_id, patch("routers.locations.LocationsDB") as mock_db:
            mock_get_id.return_value = "loc-1"
            mock_db.get_by_pkey = AsyncMock(return_value=mock_location)

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_location("loc-1", mock_user, mock_session))

            assert exc_info.value.status_code == 403

    def test_admin_can_access_any_location(self):
        """Test admin can access any location"""
        from routers.locations import get_location

        mock_user = create_mock_auth_user(admin=True, locations=[])
        mock_session = AsyncMock()
        mock_location = create_mock_location(id_="loc-1")

        with patch("routers.locations.get_location_id", new_callable=AsyncMock) as mock_get_id, patch("routers.locations.LocationsDB") as mock_db, patch(
            "routers.locations.LocationService"
        ) as mock_service:
            mock_get_id.return_value = "loc-1"
            mock_db.get_by_pkey = AsyncMock(return_value=mock_location)
            mock_service.transform_response = AsyncMock(return_value={"id": "loc-1"})

            result = run_async(get_location("loc-1", mock_user, mock_session))

            assert result["id"] == "loc-1"


class TestUpdateLocation:
    """Tests for update_location endpoint"""

    def test_updates_location(self):
        """Test updates location successfully"""
        from routers.locations import update_location
        from schemas.locations import LocationUpdate

        mock_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_location = create_mock_location(id_="loc-1")
        update_data = LocationUpdate(name="Updated Location")

        with patch("routers.locations.get_location_id", new_callable=AsyncMock) as mock_get_id, patch("routers.locations.LocationsDB") as mock_db, patch(
            "routers.locations.LocationService"
        ) as mock_service:
            mock_get_id.return_value = "loc-1"
            mock_db.get_by_pkey = AsyncMock(return_value=mock_location)
            mock_db.update = AsyncMock()
            mock_service.transform_response = AsyncMock(return_value={"id": "loc-1", "name": "Updated Location"})

            result = run_async(update_location("loc-1", update_data, mock_user, mock_session))

            mock_db.update.assert_called_once()

    def test_raises_404_when_not_found(self):
        """Test raises 404 when location not found"""
        from routers.locations import update_location
        from schemas.locations import LocationUpdate

        mock_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        update_data = LocationUpdate(name="Updated")

        with patch("routers.locations.get_location_id", new_callable=AsyncMock) as mock_get_id:
            mock_get_id.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                run_async(update_location("unknown", update_data, mock_user, mock_session))

            assert exc_info.value.status_code == 404


class TestDeleteLocation:
    """Tests for delete_location endpoint"""

    def test_deletes_location(self):
        """Test deletes location and related data"""
        from routers.locations import delete_location

        mock_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_location = create_mock_location(id_="loc-1")

        with patch("routers.locations.get_location_id", new_callable=AsyncMock) as mock_get_id, patch("routers.locations.LocationsDB") as mock_loc_db, patch(
            "routers.locations.TapsDB"
        ) as mock_taps_db, patch("routers.locations.BatchLocationsDB") as mock_batch_loc_db, patch("routers.locations.UserLocationsDB") as mock_user_loc_db:
            mock_get_id.return_value = "loc-1"
            mock_loc_db.get_by_pkey = AsyncMock(return_value=mock_location)
            mock_loc_db.delete = AsyncMock()
            mock_taps_db.delete_by = AsyncMock()
            mock_batch_loc_db.delete_by = AsyncMock()
            mock_user_loc_db.delete_by = AsyncMock()

            result = run_async(delete_location("loc-1", mock_user, mock_session))

            mock_taps_db.delete_by.assert_called_once()
            mock_batch_loc_db.delete_by.assert_called_once()
            mock_user_loc_db.delete_by.assert_called_once()
            mock_loc_db.delete.assert_called_once()

    def test_raises_404_when_not_found(self):
        """Test raises 404 when location not found"""
        from routers.locations import delete_location

        mock_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()

        with patch("routers.locations.get_location_id", new_callable=AsyncMock) as mock_get_id:
            mock_get_id.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                run_async(delete_location("unknown", mock_user, mock_session))

            assert exc_info.value.status_code == 404
