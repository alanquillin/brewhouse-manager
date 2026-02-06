"""Tests for routers/dashboard.py module - Dashboard router"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


def create_mock_location(id_="loc-1", name="Test Location"):
    """Helper to create mock location"""
    mock = MagicMock()
    mock.id = id_
    mock.name = name
    return mock


def create_mock_tap(id_="tap-1", tap_number=1, location_id="loc-1"):
    """Helper to create mock tap"""
    mock = MagicMock()
    mock.id = id_
    mock.tap_number = tap_number
    mock.location_id = location_id
    return mock


def create_mock_beer(id_="beer-1", name="Test Beer"):
    """Helper to create mock beer"""
    mock = MagicMock()
    mock.id = id_
    mock.name = name
    return mock


def create_mock_beverage(id_="bev-1", name="Test Cider"):
    """Helper to create mock beverage"""
    mock = MagicMock()
    mock.id = id_
    mock.name = name
    return mock


def create_mock_tap_monitor(id_="monitor-1", name="Test Monitor"):
    """Helper to create mock tap monitor"""
    mock = MagicMock()
    mock.id = id_
    mock.name = name
    return mock


class TestGetLocationId:
    """Tests for get_location_id helper"""

    def test_returns_uuid_unchanged(self):
        """Test returns valid UUID unchanged"""
        from routers.dashboard import get_location_id

        mock_session = AsyncMock()
        uuid_str = "123e4567-e89b-12d3-a456-426614174000"

        with patch("routers.dashboard.util.is_valid_uuid", return_value=True):
            result = run_async(get_location_id(uuid_str, mock_session))

        assert result == uuid_str

    def test_looks_up_by_name(self):
        """Test looks up location by name"""
        from routers.dashboard import get_location_id

        mock_session = AsyncMock()
        mock_location = create_mock_location(id_="loc-abc")

        with patch("routers.dashboard.util.is_valid_uuid", return_value=False), patch("routers.dashboard.LocationsDB") as mock_db:
            mock_db.query = AsyncMock(return_value=[mock_location])

            result = run_async(get_location_id("Test Location", mock_session))

        assert result == "loc-abc"

    def test_returns_none_when_not_found(self):
        """Test returns None when location not found"""
        from routers.dashboard import get_location_id

        mock_session = AsyncMock()

        with patch("routers.dashboard.util.is_valid_uuid", return_value=False), patch("routers.dashboard.LocationsDB") as mock_db:
            mock_db.query = AsyncMock(return_value=[])

            result = run_async(get_location_id("Unknown", mock_session))

        assert result is None


class TestListDashboardLocations:
    """Tests for list_dashboard_locations endpoint"""

    def test_lists_all_locations(self):
        """Test lists all locations for dashboard (no auth required)"""
        from routers.dashboard import list_dashboard_locations

        mock_session = AsyncMock()
        mock_location = create_mock_location()

        with patch("routers.dashboard.LocationsDB") as mock_db, patch("routers.dashboard.LocationService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_location])
            mock_service.transform_response = AsyncMock(return_value={"id": "loc-1"})

            result = run_async(list_dashboard_locations(mock_session))

            assert len(result) == 1
            assert result[0]["id"] == "loc-1"

    def test_no_auth_required(self):
        """Test that list_dashboard_locations has no auth dependency"""
        import inspect

        from routers.dashboard import list_dashboard_locations

        sig = inspect.signature(list_dashboard_locations)
        params = list(sig.parameters.keys())

        # Should only have db_session parameter
        assert params == ["db_session"]


class TestGetDashboardTap:
    """Tests for get_dashboard_tap endpoint"""

    def test_gets_tap_by_id(self):
        """Test gets tap by ID"""
        from routers.dashboard import get_dashboard_tap

        mock_session = AsyncMock()
        mock_tap = create_mock_tap()

        with patch("routers.dashboard.TapsDB") as mock_db, patch("routers.dashboard.TapService") as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_tap)
            mock_service.transform_response = AsyncMock(return_value={"id": "tap-1"})

            result = run_async(get_dashboard_tap("tap-1", mock_session))

            assert result["id"] == "tap-1"

    def test_raises_404_when_not_found(self):
        """Test raises 404 when tap not found"""
        from routers.dashboard import get_dashboard_tap

        mock_session = AsyncMock()

        with patch("routers.dashboard.TapsDB") as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_dashboard_tap("unknown", mock_session))

            assert exc_info.value.status_code == 404


class TestGetDashboardBeer:
    """Tests for get_dashboard_beer endpoint"""

    def test_gets_beer_by_id(self):
        """Test gets beer by ID"""
        from routers.dashboard import get_dashboard_beer

        mock_session = AsyncMock()
        mock_beer = create_mock_beer()

        with patch("routers.dashboard.BeersDB") as mock_db, patch("routers.dashboard.BeerService") as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_beer)
            mock_service.transform_response = AsyncMock(return_value={"id": "beer-1"})

            result = run_async(get_dashboard_beer("beer-1", mock_session))

            assert result["id"] == "beer-1"

    def test_raises_404_when_not_found(self):
        """Test raises 404 when beer not found"""
        from routers.dashboard import get_dashboard_beer

        mock_session = AsyncMock()

        with patch("routers.dashboard.BeersDB") as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_dashboard_beer("unknown", mock_session))

            assert exc_info.value.status_code == 404


class TestGetDashboardBeverage:
    """Tests for get_dashboard_beverage endpoint"""

    def test_gets_beverage_by_id(self):
        """Test gets beverage by ID"""
        from routers.dashboard import get_dashboard_beverage

        mock_session = AsyncMock()
        mock_beverage = create_mock_beverage()

        with patch("routers.dashboard.BeveragesDB") as mock_db, patch("routers.dashboard.BeverageService") as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_beverage)
            mock_service.transform_response = AsyncMock(return_value={"id": "bev-1"})

            result = run_async(get_dashboard_beverage("bev-1", mock_session))

            assert result["id"] == "bev-1"

    def test_raises_404_when_not_found(self):
        """Test raises 404 when beverage not found"""
        from routers.dashboard import get_dashboard_beverage

        mock_session = AsyncMock()

        with patch("routers.dashboard.BeveragesDB") as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_dashboard_beverage("unknown", mock_session))

            assert exc_info.value.status_code == 404


class TestGetDashboardTapMonitor:
    """Tests for get_dashboard_tap_monitor endpoint"""

    def test_gets_tap_monitor_by_id(self):
        """Test gets tap monitor by ID"""
        from routers.dashboard import get_dashboard_tap_monitor

        mock_session = AsyncMock()
        mock_monitor = create_mock_tap_monitor()

        with patch("routers.dashboard.TapMonitorsDB") as mock_db, patch("routers.dashboard.TapMonitorService") as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_monitor)
            mock_service.transform_response = AsyncMock(return_value={"id": "monitor-1"})

            result = run_async(get_dashboard_tap_monitor("monitor-1", mock_session))

            assert result["id"] == "monitor-1"

    def test_raises_404_when_not_found(self):
        """Test raises 404 when tap monitor not found"""
        from routers.dashboard import get_dashboard_tap_monitor

        mock_session = AsyncMock()

        with patch("routers.dashboard.TapMonitorsDB") as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_dashboard_tap_monitor("unknown", mock_session))

            assert exc_info.value.status_code == 404


class TestGetDashboard:
    """Tests for get_dashboard endpoint"""

    def test_gets_dashboard_data(self):
        """Test gets dashboard data for location"""
        from routers.dashboard import get_dashboard

        mock_session = AsyncMock()
        mock_location = create_mock_location(id_="loc-1")
        mock_tap = create_mock_tap()

        with patch("routers.dashboard.get_location_id", new_callable=AsyncMock) as mock_get_loc, patch("routers.dashboard.LocationsDB") as mock_loc_db, patch(
            "routers.dashboard.TapsDB"
        ) as mock_taps_db, patch("routers.dashboard.LocationService") as mock_loc_service, patch("routers.dashboard.TapService") as mock_tap_service:
            mock_get_loc.return_value = "loc-1"
            mock_loc_db.query = AsyncMock(return_value=[mock_location])
            mock_loc_db.get_by_pkey = AsyncMock(return_value=mock_location)
            mock_taps_db.query = AsyncMock(return_value=[mock_tap])
            mock_loc_service.transform_response = AsyncMock(return_value={"id": "loc-1", "name": "Test Location"})
            mock_tap_service.transform_response = AsyncMock(return_value={"id": "tap-1"})

            result = run_async(get_dashboard("loc-1", mock_session))

            assert "taps" in result
            assert "locations" in result
            assert "location" in result
            assert result["location"]["id"] == "loc-1"

    def test_raises_404_when_location_not_found(self):
        """Test raises 404 when location not found"""
        from routers.dashboard import get_dashboard

        mock_session = AsyncMock()

        with patch("routers.dashboard.get_location_id", new_callable=AsyncMock) as mock_get_loc:
            mock_get_loc.return_value = None

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_dashboard("unknown", mock_session))

            assert exc_info.value.status_code == 404

    def test_returns_taps_for_specific_location(self):
        """Test returns only taps for the specified location"""
        from routers.dashboard import get_dashboard

        mock_session = AsyncMock()
        mock_location = create_mock_location(id_="loc-1")
        mock_tap = create_mock_tap()

        with patch("routers.dashboard.get_location_id", new_callable=AsyncMock) as mock_get_loc, patch("routers.dashboard.LocationsDB") as mock_loc_db, patch(
            "routers.dashboard.TapsDB"
        ) as mock_taps_db, patch("routers.dashboard.LocationService") as mock_loc_service, patch("routers.dashboard.TapService") as mock_tap_service:
            mock_get_loc.return_value = "loc-1"
            mock_loc_db.query = AsyncMock(return_value=[mock_location])
            mock_loc_db.get_by_pkey = AsyncMock(return_value=mock_location)
            mock_taps_db.query = AsyncMock(return_value=[mock_tap])
            mock_loc_service.transform_response = AsyncMock(return_value={"id": "loc-1"})
            mock_tap_service.transform_response = AsyncMock(return_value={"id": "tap-1"})

            run_async(get_dashboard("loc-1", mock_session))

            # Verify taps query was called with location filter
            mock_taps_db.query.assert_called_once_with(mock_session, locations=["loc-1"])
