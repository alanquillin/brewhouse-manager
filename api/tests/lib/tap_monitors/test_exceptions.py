"""Tests for lib/tap_monitors/exceptions.py module"""

import pytest

from lib.exceptions import Error
from lib.tap_monitors.exceptions import TapMonitorDependencyError


class TestTapMonitorDependencyError:
    """Tests for TapMonitorDependencyError exception"""

    def test_is_error_subclass(self):
        """Test TapMonitorDependencyError is a subclass of Error"""
        error = TapMonitorDependencyError("kegtron")
        assert isinstance(error, Error)

    def test_default_message(self):
        """Test default error message"""
        error = TapMonitorDependencyError("plaato-keg")
        assert error.monitor_type == "plaato-keg"
        assert "plaato-keg" in error.message
        assert "dependent service" in error.message

    def test_custom_message(self):
        """Test custom error message"""
        error = TapMonitorDependencyError("kegtron", message="API timeout")
        assert error.monitor_type == "kegtron"
        assert error.message == "API timeout"

    def test_str_representation(self):
        """Test string representation"""
        error = TapMonitorDependencyError("test-monitor")
        assert "test-monitor" in str(error)

    def test_can_be_raised(self):
        """Test exception can be raised and caught"""
        with pytest.raises(TapMonitorDependencyError) as exc_info:
            raise TapMonitorDependencyError("my-monitor", "Connection failed")

        assert exc_info.value.monitor_type == "my-monitor"
        assert exc_info.value.message == "Connection failed"
