"""Tests for db/user_locations.py module - UserLocations model and table"""

from unittest.mock import MagicMock

import pytest

# Import users first to resolve circular dependency with user_locations
import db.users  # noqa: F401 - needed to avoid circular import
from db.user_locations import UserLocations, user_locations


class TestUserLocationsTable:
    """Tests for user_locations Table"""

    def test_table_name(self):
        """Test table name is correct"""
        assert user_locations.name == "user_locations"

    def test_has_required_columns(self):
        """Test table has required columns"""
        column_names = [col.name for col in user_locations.columns]
        assert "id" in column_names
        assert "user_id" in column_names
        assert "location_id" in column_names

    def test_has_audit_columns(self):
        """Test table has audit columns"""
        column_names = [col.name for col in user_locations.columns]
        assert "created_app" in column_names
        assert "created_user" in column_names
        assert "created_on" in column_names
        assert "updated_app" in column_names
        assert "updated_user" in column_names
        assert "updated_on" in column_names

    def test_user_foreign_key(self):
        """Test user_id has foreign key constraint"""
        user_id_col = user_locations.c.user_id
        assert len(user_id_col.foreign_keys) > 0
        fk = list(user_id_col.foreign_keys)[0]
        assert "users" in str(fk.target_fullname)

    def test_location_foreign_key(self):
        """Test location_id has foreign key constraint"""
        loc_id_col = user_locations.c.location_id
        assert len(loc_id_col.foreign_keys) > 0
        fk = list(loc_id_col.foreign_keys)[0]
        assert "locations" in str(fk.target_fullname)


class TestUserLocationsModel:
    """Tests for UserLocations model class"""

    def test_table_name(self):
        """Test table name is correct"""
        assert UserLocations.__tablename__ == "user_locations"

    def test_inherits_mixins(self):
        """Test UserLocations inherits required mixins"""
        from db import AsyncQueryMethodsMixin, DictifiableMixin

        assert issubclass(UserLocations, DictifiableMixin)
        assert issubclass(UserLocations, AsyncQueryMethodsMixin)

    def test_uses_shared_table(self):
        """Test model uses the shared table definition"""
        assert UserLocations.__table__ is user_locations
