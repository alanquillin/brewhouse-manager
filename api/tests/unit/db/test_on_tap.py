"""Tests for db/on_tap.py module - OnTap model"""

from unittest.mock import MagicMock

import pytest

from db.on_tap import OnTap


class TestOnTapModel:
    """Tests for OnTap model class attributes"""

    def test_table_name(self):
        """Test table name is correct"""
        assert OnTap.__tablename__ == "on_tap"

    def test_has_required_columns(self):
        """Test model has required columns"""
        column_names = [col.name for col in OnTap.__table__.columns]
        assert "id" in column_names
        assert "batch_id" in column_names
        assert "tapped_on" in column_names
        assert "untapped_on" in column_names

    def test_inherits_mixins(self):
        """Test OnTap inherits required mixins"""
        from db import AsyncQueryMethodsMixin, AuditedMixin, DictifiableMixin

        assert issubclass(OnTap, DictifiableMixin)
        assert issubclass(OnTap, AuditedMixin)
        assert issubclass(OnTap, AsyncQueryMethodsMixin)

    def test_has_relationships(self):
        """Test model has expected relationships"""
        relationships = {name for name, prop in OnTap.__mapper__.relationships.items()}
        assert "batch" in relationships

    def test_has_indexes(self):
        """Test model has expected indexes"""
        index_names = [idx.name for idx in OnTap.__table__.indexes]
        assert "ix_on_tap_batch_id" in index_names

    def test_batch_foreign_key(self):
        """Test batch_id has foreign key constraint"""
        batch_id_col = next(c for c in OnTap.__table__.columns if c.name == "batch_id")
        assert len(batch_id_col.foreign_keys) > 0
        fk = list(batch_id_col.foreign_keys)[0]
        assert "batches" in str(fk.target_fullname)
