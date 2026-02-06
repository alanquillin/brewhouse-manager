"""Tests for db/beverages.py module - Beverages model"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from db.beverages import Beverages


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestBeveragesModel:
    """Tests for Beverages model class attributes"""

    def test_table_name(self):
        """Test table name is correct"""
        assert Beverages.__tablename__ == "beverages"

    def test_has_required_columns(self):
        """Test model has required columns"""
        column_names = [col.name for col in Beverages.__table__.columns]
        assert "id" in column_names
        assert "name" in column_names
        assert "description" in column_names
        assert "brewery" in column_names
        assert "brewery_link" in column_names
        assert "type" in column_names
        assert "flavor" in column_names
        assert "img_url" in column_names
        assert "empty_img_url" in column_names
        assert "meta" in column_names
        assert "image_transitions_enabled" in column_names

    def test_inherits_mixins(self):
        """Test Beverages inherits required mixins"""
        from db import AsyncQueryMethodsMixin, AuditedMixin, DictifiableMixin

        assert issubclass(Beverages, DictifiableMixin)
        assert issubclass(Beverages, AuditedMixin)
        assert issubclass(Beverages, AsyncQueryMethodsMixin)

    def test_has_relationships(self):
        """Test model has expected relationships"""
        relationships = {name for name, prop in Beverages.__mapper__.relationships.items()}
        assert "batches" in relationships


class TestBeveragesCreate:
    """Tests for Beverages.create method"""

    def test_create_defaults_image_transitions_to_false(self):
        """Test that create defaults image_transitions_enabled to False"""
        mock_session = AsyncMock()

        with patch("db.AsyncQueryMethodsMixin.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = MagicMock()
            run_async(Beverages.create(mock_session, name="Test Cider"))

            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["image_transitions_enabled"] is False

    def test_create_preserves_explicit_image_transitions(self):
        """Test that create preserves explicit image_transitions_enabled value"""
        mock_session = AsyncMock()

        with patch("db.AsyncQueryMethodsMixin.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = MagicMock()
            run_async(Beverages.create(mock_session, name="Test Cider", image_transitions_enabled=True))

            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["image_transitions_enabled"] is True

    def test_create_passes_all_kwargs(self):
        """Test that create passes all kwargs to parent"""
        mock_session = AsyncMock()

        with patch("db.AsyncQueryMethodsMixin.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = MagicMock()
            run_async(Beverages.create(mock_session, name="Apple Cider", brewery="Test Cidery", type="Cider", flavor="Apple"))

            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["name"] == "Apple Cider"
            assert call_kwargs["brewery"] == "Test Cidery"
            assert call_kwargs["type"] == "Cider"
            assert call_kwargs["flavor"] == "Apple"
