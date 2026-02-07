"""Tests for lib/external_brew_tools/exceptions.py module"""

import pytest

from lib.exceptions import Error
from lib.external_brew_tools.exceptions import ResourceNotFoundError


class TestResourceNotFoundError:
    """Tests for ResourceNotFoundError exception"""

    def test_is_error_subclass(self):
        """Test ResourceNotFoundError is a subclass of Error"""
        error = ResourceNotFoundError("123")
        assert isinstance(error, Error)

    def test_default_message(self):
        """Test default error message"""
        error = ResourceNotFoundError("abc123")
        assert error.resource_id == "abc123"
        assert "abc123" in error.message
        assert "could not be found" in error.message

    def test_custom_message(self):
        """Test custom error message"""
        error = ResourceNotFoundError("xyz", message="Batch not found")
        assert error.resource_id == "xyz"
        assert error.message == "Batch not found"

    def test_str_representation(self):
        """Test string representation"""
        error = ResourceNotFoundError("id456")
        assert "id456" in str(error)

    def test_can_be_raised(self):
        """Test exception can be raised and caught"""
        with pytest.raises(ResourceNotFoundError) as exc_info:
            raise ResourceNotFoundError("test_id")

        assert exc_info.value.resource_id == "test_id"
