"""Tests for db/batch_overrides.py module - BatchOverrides model"""

import pytest
from unittest.mock import MagicMock

from db.batch_overrides import BatchOverrides


class TestBatchOverridesModel:
    """Tests for BatchOverrides model class attributes"""

    def test_table_name(self):
        """Test table name is correct"""
        assert BatchOverrides.__tablename__ == "batch_overrides"

    def test_has_required_columns(self):
        """Test model has required columns"""
        column_names = [col.name for col in BatchOverrides.__table__.columns]
        assert "id" in column_names
        assert "batch_id" in column_names
        assert "key" in column_names
        assert "value" in column_names

    def test_inherits_mixins(self):
        """Test BatchOverrides inherits required mixins"""
        from db import DictifiableMixin, AuditedMixin, AsyncQueryMethodsMixin
        assert issubclass(BatchOverrides, DictifiableMixin)
        assert issubclass(BatchOverrides, AuditedMixin)
        assert issubclass(BatchOverrides, AsyncQueryMethodsMixin)

    def test_has_relationships(self):
        """Test model has expected relationships"""
        relationships = {name for name, prop in BatchOverrides.__mapper__.relationships.items()}
        assert "batch" in relationships

    def test_has_indexes(self):
        """Test model has expected indexes"""
        index_names = [idx.name for idx in BatchOverrides.__table__.indexes]
        assert "ix_batch_overrides_batch_id" in index_names

    def test_batch_foreign_key(self):
        """Test batch_id has foreign key constraint"""
        batch_id_col = next(c for c in BatchOverrides.__table__.columns if c.name == "batch_id")
        assert len(batch_id_col.foreign_keys) > 0
        fk = list(batch_id_col.foreign_keys)[0]
        assert "batches" in str(fk.target_fullname)

    def test_key_not_nullable(self):
        """Test key column is not nullable"""
        key_col = next(c for c in BatchOverrides.__table__.columns if c.name == "key")
        assert key_col.nullable is False

    def test_value_not_nullable(self):
        """Test value column is not nullable"""
        value_col = next(c for c in BatchOverrides.__table__.columns if c.name == "value")
        assert value_col.nullable is False

    def test_batch_id_nullable(self):
        """Test batch_id is nullable (allows orphan overrides)"""
        batch_id_col = next(c for c in BatchOverrides.__table__.columns if c.name == "batch_id")
        assert batch_id_col.nullable is True
