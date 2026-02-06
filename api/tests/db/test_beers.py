"""Tests for db/beers.py module - Beers model"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from db.beers import Beers


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestBeersModel:
    """Tests for Beers model class attributes"""

    def test_table_name(self):
        """Test table name is correct"""
        assert Beers.__tablename__ == "beers"

    def test_has_required_columns(self):
        """Test model has required columns"""
        column_names = [col.name for col in Beers.__table__.columns]
        assert "id" in column_names
        assert "name" in column_names
        assert "description" in column_names
        assert "brewery" in column_names
        assert "style" in column_names
        assert "abv" in column_names
        assert "ibu" in column_names
        assert "srm" in column_names
        assert "img_url" in column_names
        assert "empty_img_url" in column_names
        assert "image_transitions_enabled" in column_names
        assert "external_brewing_tool" in column_names
        assert "external_brewing_tool_meta" in column_names

    def test_inherits_mixins(self):
        """Test Beers inherits required mixins"""
        from db import DictifiableMixin, AuditedMixin, AsyncQueryMethodsMixin
        assert issubclass(Beers, DictifiableMixin)
        assert issubclass(Beers, AuditedMixin)
        assert issubclass(Beers, AsyncQueryMethodsMixin)

    def test_has_relationships(self):
        """Test model has expected relationships"""
        relationships = {name for name, prop in Beers.__mapper__.relationships.items()}
        assert "batches" in relationships


class TestBeersCreate:
    """Tests for Beers.create method"""

    def test_create_defaults_image_transitions_to_false(self):
        """Test that create defaults image_transitions_enabled to False"""
        mock_session = AsyncMock()

        with patch('db.AsyncQueryMethodsMixin.create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = MagicMock()
            run_async(Beers.create(mock_session, name="Test Beer"))

            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["image_transitions_enabled"] is False

    def test_create_preserves_explicit_image_transitions(self):
        """Test that create preserves explicit image_transitions_enabled value"""
        mock_session = AsyncMock()

        with patch('db.AsyncQueryMethodsMixin.create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = MagicMock()
            run_async(Beers.create(
                mock_session,
                name="Test Beer",
                image_transitions_enabled=True
            ))

            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["image_transitions_enabled"] is True

    def test_create_passes_all_kwargs(self):
        """Test that create passes all kwargs to parent"""
        mock_session = AsyncMock()

        with patch('db.AsyncQueryMethodsMixin.create', new_callable=AsyncMock) as mock_create:
            mock_create.return_value = MagicMock()
            run_async(Beers.create(
                mock_session,
                name="Test IPA",
                brewery="Test Brewery",
                style="IPA",
                abv=6.5,
                ibu=65
            ))

            call_kwargs = mock_create.call_args[1]
            assert call_kwargs["name"] == "Test IPA"
            assert call_kwargs["brewery"] == "Test Brewery"
            assert call_kwargs["style"] == "IPA"
            assert call_kwargs["abv"] == 6.5
            assert call_kwargs["ibu"] == 65
