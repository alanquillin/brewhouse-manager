"""Tests for lib/json.py module"""

import datetime
from uuid import UUID

import pytest

from lib import UsefulEnum
from lib.json import CloudCommonJsonEncoder, dumps


class TestCloudCommonJsonEncoder:
    """Tests for CloudCommonJsonEncoder class"""

    def test_encode_datetime(self):
        """Test encoding datetime objects"""
        dt = datetime.datetime(2024, 1, 15, 10, 30, 0)
        result = dumps({"time": dt})
        assert "2024-01-15T10:30:00" in result

    def test_encode_datetime_with_timezone(self):
        """Test encoding datetime with timezone"""
        dt = datetime.datetime(2024, 6, 20, 14, 45, tzinfo=datetime.timezone.utc)
        result = dumps({"time": dt})
        assert "2024-06-20T14:45:00" in result

    def test_encode_useful_enum(self):
        """Test encoding UsefulEnum values"""

        class Status(UsefulEnum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        result = dumps({"status": Status.ACTIVE})
        assert '"status": "active"' in result

    def test_encode_uuid(self):
        """Test encoding UUID objects"""
        uuid = UUID("550e8400-e29b-41d4-a716-446655440000")
        result = dumps({"id": uuid})
        # UUID hex is without dashes
        assert "550e8400e29b41d4a716446655440000" in result

    def test_encode_object_with_json_repr(self):
        """Test encoding objects with _json_repr_ method"""

        class CustomObject:
            def __init__(self, value):
                self.value = value

            def _json_repr_(self):
                return {"custom": self.value}

        obj = CustomObject("test")
        result = dumps({"obj": obj})
        assert '"custom"' in result
        assert '"test"' in result

    def test_encode_nested_objects(self):
        """Test encoding nested objects with special types"""

        class Status(UsefulEnum):
            ACTIVE = "active"

        data = {"created": datetime.datetime(2024, 1, 1), "status": Status.ACTIVE, "nested": {"id": UUID("550e8400-e29b-41d4-a716-446655440000")}}
        result = dumps(data)
        assert "2024-01-01" in result
        assert "active" in result
        assert "550e8400e29b41d4a716446655440000" in result

    def test_encode_standard_types(self):
        """Test that standard types still work"""
        data = {"string": "hello", "number": 42, "float": 3.14, "boolean": True, "null": None, "list": [1, 2, 3], "dict": {"nested": "value"}}
        result = dumps(data)
        assert '"string": "hello"' in result
        assert '"number": 42' in result
        assert '"boolean": true' in result
        assert '"null": null' in result


class TestDumps:
    """Tests for dumps function"""

    def test_dumps_basic(self):
        """Test basic dumps functionality"""
        result = dumps({"key": "value"})
        assert result == '{"key": "value"}'

    def test_dumps_with_indent(self):
        """Test dumps with indent parameter"""
        result = dumps({"key": "value"}, indent=2)
        assert "\n" in result

    def test_dumps_list(self):
        """Test dumps with list"""
        result = dumps([1, 2, 3])
        assert result == "[1, 2, 3]"

    def test_dumps_empty_dict(self):
        """Test dumps with empty dict"""
        result = dumps({})
        assert result == "{}"

    def test_dumps_special_characters(self):
        """Test dumps handles special characters"""
        result = dumps({"message": "Hello\nWorld"})
        assert "\\n" in result
