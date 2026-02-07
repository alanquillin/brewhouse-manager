"""Tests for db/locations.py module - Location model with name normalization"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from db.locations import Locations


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestLocationsModel:
    """Tests for Locations model class attributes"""

    def test_table_name(self):
        """Test table name is correct"""
        assert Locations.__tablename__ == "locations"

    def test_has_required_columns(self):
        """Test model has required columns"""
        column_names = [col.name for col in Locations.__table__.columns]
        assert "id" in column_names
        assert "name" in column_names
        assert "description" in column_names

    def test_inherits_mixins(self):
        """Test Locations inherits required mixins"""
        from db import AsyncQueryMethodsMixin, AuditedMixin, DictifiableMixin

        assert issubclass(Locations, DictifiableMixin)
        assert issubclass(Locations, AuditedMixin)
        assert issubclass(Locations, AsyncQueryMethodsMixin)


class TestLocationsReplaceName:
    """Tests for Locations._replace_name method"""

    def test_replace_spaces_with_dashes(self):
        """Test spaces are replaced with dashes"""
        result = Locations._replace_name({"name": "My Location"})
        assert result["name"] == "my-location"

    def test_lowercase_conversion(self):
        """Test name is converted to lowercase"""
        result = Locations._replace_name({"name": "MyLocation"})
        assert result["name"] == "mylocation"

    def test_remove_special_characters(self):
        """Test special characters are removed"""
        result = Locations._replace_name({"name": "My@Location!#$%"})
        assert result["name"] == "mylocation"

    def test_preserve_dashes(self):
        """Test existing dashes are preserved"""
        result = Locations._replace_name({"name": "my-location"})
        assert result["name"] == "my-location"

    def test_preserve_numbers(self):
        """Test numbers are preserved"""
        result = Locations._replace_name({"name": "Location 123"})
        assert result["name"] == "location-123"

    def test_no_name_in_data(self):
        """Test data without name is returned unchanged"""
        data = {"description": "Test description"}
        result = Locations._replace_name(data)
        assert result == data
        assert "name" not in result

    def test_empty_name(self):
        """Test empty name is handled"""
        result = Locations._replace_name({"name": ""})
        assert result["name"] == ""

    def test_none_name(self):
        """Test None name is handled"""
        result = Locations._replace_name({"name": None})
        assert result["name"] is None

    def test_complex_name_normalization(self):
        """Test complex name with multiple special chars"""
        result = Locations._replace_name({"name": "My Cool Location! @2023"})
        assert result["name"] == "my-cool-location-2023"

    def test_multiple_spaces(self):
        """Test multiple consecutive spaces"""
        result = Locations._replace_name({"name": "My   Location"})
        # Multiple spaces become multiple dashes, then chars between dashes remain
        assert "my" in result["name"]
        assert "location" in result["name"]


class TestLocationsCreate:
    """Tests for Locations.create method"""

    def test_create_normalizes_name(self):
        """Test that create normalizes the name"""
        mock_session = AsyncMock()

        with patch("db.AsyncQueryMethodsMixin.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = MagicMock()
            run_async(Locations.create(mock_session, name="My Location"))

            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["name"] == "my-location"

    def test_create_passes_other_kwargs(self):
        """Test that create passes through other kwargs"""
        mock_session = AsyncMock()

        with patch("db.AsyncQueryMethodsMixin.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = MagicMock()
            run_async(Locations.create(mock_session, name="My Location", description="Test description"))

            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["description"] == "Test description"


class TestLocationsUpdate:
    """Tests for Locations.update method"""

    def test_update_normalizes_name(self):
        """Test that update normalizes the name"""
        mock_session = AsyncMock()

        with patch("db.AsyncQueryMethodsMixin.update", new_callable=AsyncMock) as mock_update:
            mock_update.return_value = 1
            run_async(Locations.update(mock_session, "loc-id", name="New Location"))

            call_kwargs = mock_update.call_args[1]
            assert call_kwargs["name"] == "new-location"

    def test_update_without_name(self):
        """Test that update works without name"""
        mock_session = AsyncMock()

        with patch("db.AsyncQueryMethodsMixin.update", new_callable=AsyncMock) as mock_update:
            mock_update.return_value = 1
            run_async(Locations.update(mock_session, "loc-id", description="Updated description"))

            call_kwargs = mock_update.call_args[1]
            assert "name" not in call_kwargs
            assert call_kwargs["description"] == "Updated description"
