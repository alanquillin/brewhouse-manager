"""Tests for db/batch_locations.py module - BatchLocations model"""

from unittest.mock import MagicMock

import pytest

# Import batches first to resolve circular dependency with batch_locations
import db.batches  # noqa: F401 - needed to avoid circular import
from db.batch_locations import BatchLocations


class TestBatchLocationsModel:
    """Tests for BatchLocations model class attributes"""

    def test_table_name(self):
        """Test table name is correct"""
        assert BatchLocations.__tablename__ == "batch_locations"

    def test_has_required_columns(self):
        """Test model has required columns"""
        column_names = [col.name for col in BatchLocations.__table__.columns]
        assert "id" in column_names
        assert "batch_id" in column_names
        assert "location_id" in column_names

    def test_inherits_mixins(self):
        """Test BatchLocations inherits required mixins"""
        from db import AsyncQueryMethodsMixin, AuditedMixin, DictifiableMixin

        assert issubclass(BatchLocations, DictifiableMixin)
        assert issubclass(BatchLocations, AuditedMixin)
        assert issubclass(BatchLocations, AsyncQueryMethodsMixin)

    def test_has_relationships(self):
        """Test model has expected relationships"""
        relationships = {name for name, prop in BatchLocations.__mapper__.relationships.items()}
        assert "batch" in relationships
        assert "location" in relationships

    def test_has_indexes(self):
        """Test model has expected indexes"""
        index_names = [idx.name for idx in BatchLocations.__table__.indexes]
        assert "ix_locations_batch_id" in index_names
        assert "ix_locations_batch_id_location_id" in index_names

    def test_batch_foreign_key(self):
        """Test batch_id has foreign key constraint"""
        batch_id_col = next(c for c in BatchLocations.__table__.columns if c.name == "batch_id")
        assert len(batch_id_col.foreign_keys) > 0
        fk = list(batch_id_col.foreign_keys)[0]
        assert "batches" in str(fk.target_fullname)

    def test_location_foreign_key(self):
        """Test location_id has foreign key constraint"""
        loc_id_col = next(c for c in BatchLocations.__table__.columns if c.name == "location_id")
        assert len(loc_id_col.foreign_keys) > 0
        fk = list(loc_id_col.foreign_keys)[0]
        assert "locations" in str(fk.target_fullname)

    def test_batch_id_not_nullable(self):
        """Test batch_id column is not nullable"""
        batch_id_col = next(c for c in BatchLocations.__table__.columns if c.name == "batch_id")
        assert batch_id_col.nullable is False

    def test_location_id_not_nullable(self):
        """Test location_id column is not nullable"""
        loc_id_col = next(c for c in BatchLocations.__table__.columns if c.name == "location_id")
        assert loc_id_col.nullable is False
