"""Tests for routers/__init__.py module - shared router utilities"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


def create_mock_location(id_="loc-1", name="Test Location"):
    """Helper to create mock location"""
    mock = MagicMock()
    mock.id = id_
    mock.name = name
    return mock


class TestGetLocationId:
    """Tests for get_location_id helper function"""

    def test_returns_uuid_unchanged(self):
        """Test returns valid UUID unchanged without database query"""
        from routers import get_location_id

        mock_session = AsyncMock()
        uuid_str = "123e4567-e89b-12d3-a456-426614174000"

        with patch("routers.util.is_valid_uuid", return_value=True) as mock_is_valid:
            result = run_async(get_location_id(uuid_str, mock_session))

        assert result == uuid_str
        mock_is_valid.assert_called_once_with(uuid_str)

    def test_queries_database_when_not_uuid(self):
        """Test queries database by name when identifier is not a UUID"""
        from routers import get_location_id

        mock_session = AsyncMock()
        mock_location = create_mock_location(id_="found-loc-id", name="My Brewery")

        with patch("routers.util.is_valid_uuid", return_value=False), patch("db.locations.Locations") as mock_db:
            mock_db.query = AsyncMock(return_value=[mock_location])

            result = run_async(get_location_id("My Brewery", mock_session))

        assert result == "found-loc-id"
        mock_db.query.assert_called_once_with(mock_session, name="My Brewery")

    def test_returns_first_location_id_when_multiple_match(self):
        """Test returns first location ID when multiple locations match name"""
        from routers import get_location_id

        mock_session = AsyncMock()
        mock_location1 = create_mock_location(id_="first-loc-id", name="Duplicate")
        mock_location2 = create_mock_location(id_="second-loc-id", name="Duplicate")

        with patch("routers.util.is_valid_uuid", return_value=False), patch("db.locations.Locations") as mock_db:
            mock_db.query = AsyncMock(return_value=[mock_location1, mock_location2])

            result = run_async(get_location_id("Duplicate", mock_session))

        assert result == "first-loc-id"

    def test_returns_none_when_name_not_found(self):
        """Test returns None when location name not found in database"""
        from routers import get_location_id

        mock_session = AsyncMock()

        with patch("routers.util.is_valid_uuid", return_value=False), patch("db.locations.Locations") as mock_db:
            mock_db.query = AsyncMock(return_value=[])

            result = run_async(get_location_id("Unknown Location", mock_session))

        assert result is None
        mock_db.query.assert_called_once_with(mock_session, name="Unknown Location")

    def test_returns_none_when_query_returns_none(self):
        """Test returns None when database query returns None instead of empty list"""
        from routers import get_location_id

        mock_session = AsyncMock()

        with patch("routers.util.is_valid_uuid", return_value=False), patch("db.locations.Locations") as mock_db:
            mock_db.query = AsyncMock(return_value=None)

            result = run_async(get_location_id("Unknown Location", mock_session))

        assert result is None

    def test_does_not_query_database_for_valid_uuid(self):
        """Test does not query database when identifier is a valid UUID"""
        from routers import get_location_id

        mock_session = AsyncMock()
        uuid_str = "550e8400-e29b-41d4-a716-446655440000"

        with patch("routers.util.is_valid_uuid", return_value=True), patch("db.locations.Locations") as mock_db:
            mock_db.query = AsyncMock()

            result = run_async(get_location_id(uuid_str, mock_session))

        assert result == uuid_str
        mock_db.query.assert_not_called()
