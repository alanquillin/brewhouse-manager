"""Tests for db/batches.py module - Batches model"""

from unittest.mock import MagicMock

import pytest

from db.batches import Batches


class TestBatchesModel:
    """Tests for Batches model class attributes"""

    def test_table_name(self):
        """Test table name is correct"""
        assert Batches.__tablename__ == "batches"

    def test_has_required_columns(self):
        """Test model has required columns"""
        column_names = [col.name for col in Batches.__table__.columns]
        assert "id" in column_names
        assert "name" in column_names
        assert "batch_number" in column_names
        assert "beer_id" in column_names
        assert "beverage_id" in column_names
        assert "external_brewing_tool" in column_names
        assert "external_brewing_tool_meta" in column_names
        assert "abv" in column_names
        assert "ibu" in column_names
        assert "srm" in column_names
        assert "img_url" in column_names
        assert "brew_date" in column_names
        assert "keg_date" in column_names
        assert "archived_on" in column_names

    def test_inherits_mixins(self):
        """Test Batches inherits required mixins"""
        from db import AsyncQueryMethodsMixin, AuditedMixin, DictifiableMixin

        assert issubclass(Batches, DictifiableMixin)
        assert issubclass(Batches, AuditedMixin)
        assert issubclass(Batches, AsyncQueryMethodsMixin)

    def test_has_relationships(self):
        """Test model has expected relationships"""
        relationships = {name for name, prop in Batches.__mapper__.relationships.items()}
        assert "beer" in relationships
        assert "beverage" in relationships
        assert "locations" in relationships

    def test_has_indexes(self):
        """Test model has expected indexes"""
        index_names = [idx.name for idx in Batches.__table__.indexes]
        assert "ix_batches_beer_id" in index_names
        assert "ix_batches_beverage_id" in index_names
