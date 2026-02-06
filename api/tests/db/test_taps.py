"""Tests for db/taps.py module - Taps model"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from db.taps import Taps


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestTapsModel:
    """Tests for Taps model class attributes"""

    def test_table_name(self):
        """Test table name is correct"""
        assert Taps.__tablename__ == "taps"

    def test_has_required_columns(self):
        """Test model has required columns"""
        column_names = [col.name for col in Taps.__table__.columns]
        assert "id" in column_names
        assert "tap_number" in column_names
        assert "description" in column_names
        assert "location_id" in column_names
        assert "tap_monitor_id" in column_names
        assert "on_tap_id" in column_names
        assert "name_prefix" in column_names
        assert "name_suffix" in column_names

    def test_inherits_mixins(self):
        """Test Taps inherits required mixins"""
        from db import DictifiableMixin, AuditedMixin, AsyncQueryMethodsMixin
        assert issubclass(Taps, DictifiableMixin)
        assert issubclass(Taps, AuditedMixin)
        assert issubclass(Taps, AsyncQueryMethodsMixin)

    def test_has_relationships(self):
        """Test model has expected relationships"""
        from sqlalchemy.orm import RelationshipProperty
        relationships = {name for name, prop in Taps.__mapper__.relationships.items()}
        assert "location" in relationships
        assert "tap_monitor" in relationships
        assert "on_tap" in relationships


class TestTapsGetByLocation:
    """Tests for Taps.get_by_location method"""

    def test_get_by_location_filters_by_location_id(self):
        """Test get_by_location filters by location_id"""
        mock_session = AsyncMock()
        mock_taps = [MagicMock(), MagicMock()]

        with patch.object(Taps.__bases__[3], 'query', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_taps
            result = run_async(Taps.get_by_location(mock_session, "location-123"))

            assert result == mock_taps
            mock_query.assert_called_once()
            # Verify q_fn is passed
            call_kwargs = mock_query.call_args[1]
            assert "q_fn" in call_kwargs


class TestTapsGetByBatch:
    """Tests for Taps.get_by_batch method"""

    def test_get_by_batch_filters_by_batch_id(self):
        """Test get_by_batch filters by batch_id"""
        mock_session = AsyncMock()
        mock_taps = [MagicMock()]

        with patch.object(Taps.__bases__[3], 'query', new_callable=AsyncMock) as mock_query:
            mock_query.return_value = mock_taps
            result = run_async(Taps.get_by_batch(mock_session, "batch-123"))

            assert result == mock_taps
            mock_query.assert_called_once()
            call_kwargs = mock_query.call_args[1]
            assert "q_fn" in call_kwargs
