"""Tests for lib/tap_monitors/__init__.py module"""

import pytest
from unittest.mock import patch, MagicMock

from lib.tap_monitors import InvalidDataType, TapMonitorBase, get_types, get_tap_monitor_lib
from lib.exceptions import Error


class TestInvalidDataType:
    """Tests for InvalidDataType exception"""

    def test_is_error_subclass(self):
        """Test InvalidDataType is a subclass of Error"""
        error = InvalidDataType("unknown_type")
        assert isinstance(error, Error)

    def test_default_message(self):
        """Test default error message"""
        error = InvalidDataType("bad_data")
        assert error.data_type == "bad_data"
        assert "bad_data" in error.message
        assert "Invalid data type" in error.message

    def test_custom_message(self):
        """Test custom error message"""
        error = InvalidDataType("test_type", message="Custom error")
        assert error.data_type == "test_type"
        assert error.message == "Custom error"

    def test_str_representation(self):
        """Test string representation"""
        error = InvalidDataType("my_type")
        assert "my_type" in str(error)


class TestTapMonitorBase:
    """Tests for TapMonitorBase class"""

    @patch('lib.tap_monitors.Config')
    @patch('lib.tap_monitors.logging')
    def test_init(self, mock_logging, mock_config):
        """Test TapMonitorBase initialization"""
        mock_logger = MagicMock()
        mock_logging.getLogger.return_value = mock_logger

        base = TapMonitorBase()

        assert base.config is not None
        assert base.logger == mock_logger
        mock_logging.getLogger.assert_called_with("TapMonitorBase")


class TestGetTypes:
    """Tests for get_types function"""

    def test_returns_list(self):
        """Test get_types returns a list"""
        result = get_types()
        assert isinstance(result, list)

    def test_items_have_required_fields(self):
        """Test each item has type and supports_discovery fields"""
        result = get_types()
        for item in result:
            assert "type" in item
            assert "supports_discovery" in item


class TestGetTapMonitorLib:
    """Tests for get_tap_monitor_lib function"""

    def test_unknown_type_returns_none(self):
        """Test get_tap_monitor_lib returns None for unknown type"""
        result = get_tap_monitor_lib("unknown-monitor-type")
        assert result is None
