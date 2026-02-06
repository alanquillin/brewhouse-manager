"""Tests for db/image_transitions.py module - ImageTransitions model"""

import pytest
from unittest.mock import MagicMock

from db.image_transitions import ImageTransitions


class TestImageTransitionsModel:
    """Tests for ImageTransitions model class attributes"""

    def test_table_name(self):
        """Test table name is correct"""
        assert ImageTransitions.__tablename__ == "image_transitions"

    def test_has_required_columns(self):
        """Test model has required columns"""
        column_names = [col.name for col in ImageTransitions.__table__.columns]
        assert "id" in column_names
        assert "beer_id" in column_names
        assert "beverage_id" in column_names
        assert "img_url" in column_names
        assert "change_percent" in column_names

    def test_inherits_mixins(self):
        """Test ImageTransitions inherits required mixins"""
        from db import DictifiableMixin, AuditedMixin, AsyncQueryMethodsMixin
        assert issubclass(ImageTransitions, DictifiableMixin)
        assert issubclass(ImageTransitions, AuditedMixin)
        assert issubclass(ImageTransitions, AsyncQueryMethodsMixin)

    def test_has_relationships(self):
        """Test model has expected relationships"""
        relationships = {name for name, prop in ImageTransitions.__mapper__.relationships.items()}
        assert "beer" in relationships
        assert "beverage" in relationships

    def test_has_indexes(self):
        """Test model has expected indexes"""
        index_names = [idx.name for idx in ImageTransitions.__table__.indexes]
        assert "ix_image_transition_beer_id" in index_names
        assert "ix_image_transition_beverage_id" in index_names

    def test_beer_foreign_key(self):
        """Test beer_id has foreign key constraint"""
        beer_id_col = next(c for c in ImageTransitions.__table__.columns if c.name == "beer_id")
        assert len(beer_id_col.foreign_keys) > 0
        fk = list(beer_id_col.foreign_keys)[0]
        assert "beers" in str(fk.target_fullname)

    def test_beverage_foreign_key(self):
        """Test beverage_id has foreign key constraint"""
        bev_id_col = next(c for c in ImageTransitions.__table__.columns if c.name == "beverage_id")
        assert len(bev_id_col.foreign_keys) > 0
        fk = list(bev_id_col.foreign_keys)[0]
        assert "beverages" in str(fk.target_fullname)

    def test_beer_id_nullable(self):
        """Test beer_id column is nullable (can be beer OR beverage)"""
        beer_id_col = next(c for c in ImageTransitions.__table__.columns if c.name == "beer_id")
        assert beer_id_col.nullable is True

    def test_beverage_id_nullable(self):
        """Test beverage_id column is nullable (can be beer OR beverage)"""
        bev_id_col = next(c for c in ImageTransitions.__table__.columns if c.name == "beverage_id")
        assert bev_id_col.nullable is True

    def test_img_url_not_nullable(self):
        """Test img_url column is not nullable"""
        img_col = next(c for c in ImageTransitions.__table__.columns if c.name == "img_url")
        assert img_col.nullable is False
