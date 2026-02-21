"""Tests for services/locations.py module - Location service"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from services.locations import LocationService


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestLocationServiceTransformResponse:
    """Tests for LocationService.transform_response method"""

    def test_returns_none_for_none_input(self):
        """Test returns None when location is None"""
        result = run_async(LocationService.transform_response(None))
        assert result is None

    def test_calls_to_dict(self):
        """Test calls model's to_dict method"""
        mock_location = MagicMock()
        mock_location.to_dict.return_value = {"id": "loc-1", "name": "test-location"}

        with patch("services.locations.transform_dict_to_camel_case", side_effect=lambda x: x):
            result = run_async(LocationService.transform_response(mock_location))

        mock_location.to_dict.assert_called_once()
        assert result["id"] == "loc-1"
        assert result["name"] == "test-location"

    def test_transforms_to_camel_case(self):
        """Test response is transformed to camelCase"""
        mock_location = MagicMock()
        mock_location.to_dict.return_value = {"id": "loc-1", "name": "test-location", "created_on": "2024-01-01"}

        result = run_async(LocationService.transform_response(mock_location))

        assert "createdOn" in result
        assert "created_on" not in result

    def test_accepts_kwargs(self):
        """Test accepts additional kwargs without error"""
        mock_location = MagicMock()
        mock_location.to_dict.return_value = {"id": "loc-1"}

        # Should not raise
        result = run_async(LocationService.transform_response(mock_location, extra_param="value", another="test"))

        assert result is not None
