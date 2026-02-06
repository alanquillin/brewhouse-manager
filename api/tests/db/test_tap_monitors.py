"""Tests for db/tap_monitors.py module - TapMonitors model"""

import pytest
from unittest.mock import MagicMock

from db.tap_monitors import TapMonitors


class TestTapMonitorsModel:
    """Tests for TapMonitors model class attributes"""

    def test_table_name(self):
        """Test table name is correct"""
        assert TapMonitors.__tablename__ == "tap_monitors"

    def test_has_required_columns(self):
        """Test model has required columns"""
        column_names = [col.name for col in TapMonitors.__table__.columns]
        assert "id" in column_names
        assert "name" in column_names
        assert "location_id" in column_names
        assert "monitor_type" in column_names
        assert "meta" in column_names

    def test_inherits_mixins(self):
        """Test TapMonitors inherits required mixins"""
        from db import DictifiableMixin, AuditedMixin, AsyncQueryMethodsMixin
        assert issubclass(TapMonitors, DictifiableMixin)
        assert issubclass(TapMonitors, AuditedMixin)
        assert issubclass(TapMonitors, AsyncQueryMethodsMixin)

    def test_has_relationships(self):
        """Test model has expected relationships"""
        relationships = {name for name, prop in TapMonitors.__mapper__.relationships.items()}
        assert "location" in relationships

    def test_has_indexes(self):
        """Test model has expected indexes"""
        index_names = [idx.name for idx in TapMonitors.__table__.indexes]
        assert "ix_tap_monitor_location_id" in index_names

    def test_location_foreign_key(self):
        """Test location_id has foreign key constraint"""
        loc_id_col = next(c for c in TapMonitors.__table__.columns if c.name == "location_id")
        assert len(loc_id_col.foreign_keys) > 0
        fk = list(loc_id_col.foreign_keys)[0]
        assert "locations" in str(fk.target_fullname)

    def test_name_not_nullable(self):
        """Test name column is not nullable"""
        name_col = next(c for c in TapMonitors.__table__.columns if c.name == "name")
        assert name_col.nullable is False

    def test_monitor_type_not_nullable(self):
        """Test monitor_type column is not nullable"""
        type_col = next(c for c in TapMonitors.__table__.columns if c.name == "monitor_type")
        assert type_col.nullable is False

    def test_meta_uses_jsonb(self):
        """Test meta column uses JSONB type"""
        meta_col = next(c for c in TapMonitors.__table__.columns if c.name == "meta")
        from sqlalchemy.dialects.postgresql import JSONB
        # Check that it's JSONB based
        assert "JSONB" in str(meta_col.type)
