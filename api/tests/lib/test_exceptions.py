"""Tests for lib/exceptions.py module"""

import pytest

from lib.exceptions import Error, InvalidEnum, InvalidExternalBrewingTool, InvalidParameter, InvalidTapMonitorType, ItemAlreadyExists, RequiredParameterNotFound


class TestError:
    """Tests for base Error exception"""

    def test_error_message(self):
        """Test Error stores and returns message"""
        error = Error("Something went wrong")
        assert error.message == "Something went wrong"
        assert str(error) == "Something went wrong"

    def test_error_is_exception(self):
        """Test Error can be raised and caught"""
        with pytest.raises(Error) as exc_info:
            raise Error("Test error")
        assert str(exc_info.value) == "Test error"


class TestInvalidEnum:
    """Tests for InvalidEnum exception"""

    def test_invalid_enum_is_value_error(self):
        """Test InvalidEnum is a ValueError"""
        error = InvalidEnum("Invalid value")
        assert isinstance(error, ValueError)

    def test_invalid_enum_message(self):
        """Test InvalidEnum message"""
        with pytest.raises(InvalidEnum) as exc_info:
            raise InvalidEnum("'foo' is not valid")
        assert "'foo' is not valid" in str(exc_info.value)


class TestInvalidParameter:
    """Tests for InvalidParameter exception"""

    def test_invalid_parameter_without_allowed_list(self):
        """Test InvalidParameter without allowed params"""
        error = InvalidParameter("foo")
        assert error.param == "foo"
        assert error.allowed_params is None
        assert "foo" in error.message
        assert "not allowed" in error.message

    def test_invalid_parameter_with_allowed_list(self):
        """Test InvalidParameter with allowed params"""
        error = InvalidParameter("foo", allowed_params=["bar", "baz"])
        assert error.param == "foo"
        assert error.allowed_params == ["bar", "baz"]
        assert "foo" in error.message
        assert "bar" in error.message
        assert "baz" in error.message

    def test_invalid_parameter_str(self):
        """Test InvalidParameter string representation"""
        error = InvalidParameter("invalid_param", ["valid1", "valid2"])
        assert str(error) == error.message


class TestRequiredParameterNotFound:
    """Tests for RequiredParameterNotFound exception"""

    def test_required_parameter_message(self):
        """Test RequiredParameterNotFound message"""
        error = RequiredParameterNotFound("username")
        assert error.param == "username"
        assert "username" in error.message
        assert "not provided" in error.message

    def test_required_parameter_str(self):
        """Test RequiredParameterNotFound string representation"""
        error = RequiredParameterNotFound("password")
        assert "password" in str(error)


class TestItemAlreadyExists:
    """Tests for ItemAlreadyExists exception"""

    def test_item_already_exists_default_message(self):
        """Test ItemAlreadyExists with default message"""
        error = ItemAlreadyExists()
        assert "already exists" in error.message

    def test_item_already_exists_custom_message(self):
        """Test ItemAlreadyExists with custom message"""
        error = ItemAlreadyExists("User with email already exists")
        assert error.message == "User with email already exists"


class TestInvalidExternalBrewingTool:
    """Tests for InvalidExternalBrewingTool exception"""

    def test_invalid_tool_default_message(self):
        """Test InvalidExternalBrewingTool with default message"""
        error = InvalidExternalBrewingTool("unknown_tool")
        assert error.name == "unknown_tool"
        assert "unknown_tool" in error.message
        assert "Invalid external brewing tool" in error.message

    def test_invalid_tool_custom_message(self):
        """Test InvalidExternalBrewingTool with custom message"""
        error = InvalidExternalBrewingTool("bad_tool", "Custom error message")
        assert error.name == "bad_tool"
        assert error.message == "Custom error message"


class TestInvalidTapMonitorType:
    """Tests for InvalidTapMonitorType exception"""

    def test_invalid_monitor_default_message(self):
        """Test InvalidTapMonitorType with default message"""
        error = InvalidTapMonitorType("unknown_monitor")
        assert error.monitor_type == "unknown_monitor"
        assert "unknown_monitor" in error.message
        assert "Invalid tap monitor type" in error.message

    def test_invalid_monitor_custom_message(self):
        """Test InvalidTapMonitorType with custom message"""
        error = InvalidTapMonitorType("bad_monitor", "Monitor not supported")
        assert error.monitor_type == "bad_monitor"
        assert error.message == "Monitor not supported"
