"""Tests for db/__init__.py module - Core database utilities and mixins"""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from sqlalchemy.exc import IntegrityError

from db import (
    convert_exception,
    DictifiableMixin,
    DictMethodsMixin,
    mergeable_fields,
    _merge_into,
    generate_db_enum,
    Base,
)
from lib.exceptions import InvalidParameter, RequiredParameterNotFound, ItemAlreadyExists


class TestConvertException:
    """Tests for convert_exception context manager"""

    def test_no_exception_passes_through(self):
        """Test that no exception yields cleanly"""
        with convert_exception(ValueError, new=RuntimeError):
            result = 1 + 1
        assert result == 2

    def test_matching_exception_converted(self):
        """Test that matching exception is converted"""
        with pytest.raises(RuntimeError):
            with convert_exception(ValueError, new=RuntimeError):
                raise ValueError("test")

    def test_non_matching_exception_not_converted(self):
        """Test that non-matching exception is not converted"""
        with pytest.raises(TypeError):
            with convert_exception(ValueError, new=RuntimeError):
                raise TypeError("test")

    def test_str_match_filter(self):
        """Test str_match filters exceptions"""
        # Should convert - string matches
        with pytest.raises(RuntimeError):
            with convert_exception(ValueError, new=RuntimeError, str_match="specific"):
                raise ValueError("specific error")

        # Should not convert - string doesn't match
        with pytest.raises(ValueError):
            with convert_exception(ValueError, new=RuntimeError, str_match="specific"):
                raise ValueError("different error")


class TestDictifiableMixin:
    """Tests for DictifiableMixin class"""

    def test_to_dict_uses_inspection(self):
        """Test to_dict calls SQLAlchemy inspect"""
        class MockModel(DictifiableMixin):
            pass

        mock_instance = MockModel()

        # Verify the inspect function is called when to_dict is invoked
        with patch('db.inspect') as mock_inspect:
            mock_mapper = MagicMock()
            mock_mapper.all_orm_descriptors.items.return_value = []
            mock_inspect.return_value = mock_mapper

            result = mock_instance.to_dict()

            mock_inspect.assert_called_once_with(MockModel)
            assert isinstance(result, dict)

    def test_json_repr_calls_to_dict(self):
        """Test _json_repr_ delegates to to_dict"""
        class MockModel(DictifiableMixin):
            def to_dict(self, *args, **kwargs):
                return {"test": "value"}

        instance = MockModel()
        result = instance._json_repr_()

        assert result == {"test": "value"}


class TestDictMethodsMixin:
    """Tests for DictMethodsMixin class"""

    def test_get_existing_attribute(self):
        """Test get() with existing attribute"""
        class MockModel(DictMethodsMixin):
            name = "test_value"

        instance = MockModel()
        assert instance.get("name") == "test_value"

    def test_get_missing_attribute_returns_default(self):
        """Test get() with missing attribute returns default"""
        class MockModel(DictMethodsMixin):
            pass

        instance = MockModel()
        assert instance.get("missing", "default") == "default"

    def test_getitem(self):
        """Test __getitem__ returns attribute"""
        class MockModel(DictMethodsMixin):
            name = "test"

        instance = MockModel()
        assert instance["name"] == "test"

    def test_setitem(self):
        """Test __setitem__ sets attribute"""
        class MockModel(DictMethodsMixin):
            name = None

        instance = MockModel()
        instance["name"] = "new_value"
        assert instance.name == "new_value"

    def test_contains_true(self):
        """Test __contains__ returns True for existing attribute"""
        class MockModel(DictMethodsMixin):
            name = "test"

        instance = MockModel()
        assert "name" in instance

    def test_contains_false(self):
        """Test __contains__ returns False for missing attribute"""
        class MockModel(DictMethodsMixin):
            pass

        instance = MockModel()
        assert "missing" not in instance


class TestMergeableFieldsDecorator:
    """Tests for mergeable_fields decorator"""

    def test_decorator_sets_fields_list(self):
        """Test decorator sets _mergeable_fields attribute"""
        @mergeable_fields("field1", "field2")
        class TestClass:
            pass

        assert hasattr(TestClass, "_mergeable_fields")
        assert TestClass._mergeable_fields == ("field1", "field2")

    def test_decorator_with_no_fields(self):
        """Test decorator with no fields"""
        @mergeable_fields()
        class TestClass:
            pass

        assert TestClass._mergeable_fields == ()


class TestMergeInto:
    """Tests for _merge_into function"""

    def test_merge_simple_dict(self):
        """Test merging simple dict"""
        target = {"a": 1, "b": 2}
        updates = {"b": 3, "c": 4}

        result = _merge_into(target, updates)

        assert result == {"a": 1, "b": 3, "c": 4}
        assert result is target  # Modifies in place

    def test_merge_nested_dict(self):
        """Test merging nested dict"""
        target = {"outer": {"inner1": 1, "inner2": 2}}
        updates = {"outer": {"inner2": 3, "inner3": 4}}

        result = _merge_into(target, updates)

        assert result["outer"] == {"inner1": 1, "inner2": 3, "inner3": 4}

    def test_merge_lists_extends(self):
        """Test merging lists extends them"""
        target = {"items": [1, 2]}
        updates = {"items": [3, 4]}

        result = _merge_into(target, updates)

        assert result["items"] == [1, 2, 3, 4]

    def test_merge_none_target_returns_updates(self):
        """Test merging into None returns updates"""
        result = _merge_into(None, {"a": 1})
        assert result == {"a": 1}

    def test_merge_replaces_non_matching_types(self):
        """Test merge replaces when types don't match"""
        target = {"a": [1, 2]}
        updates = {"a": "string"}

        result = _merge_into(target, updates)

        assert result["a"] == "string"


class TestGenerateDbEnum:
    """Tests for generate_db_enum function"""

    def test_generates_enum(self):
        """Test generate_db_enum creates PostgreSQL ENUM"""
        from enum import Enum

        class TestEnum(Enum):
            VALUE1 = "value1"
            VALUE2 = "value2"

        result = generate_db_enum(TestEnum)

        # Verify it's a PostgreSQL ENUM type
        assert result is not None
        assert result.name == "TestEnum"


class TestBase:
    """Tests for Base declarative class"""

    def test_base_has_async_attrs(self):
        """Test Base inherits from AsyncAttrs"""
        from sqlalchemy.ext.asyncio import AsyncAttrs
        assert issubclass(Base, AsyncAttrs)


class TestAuditColumns:
    """Tests for audit column definitions"""

    def test_audit_column_names_defined(self):
        """Test audit column names are defined"""
        from db import audit_column_names

        expected = [
            "created_app",
            "created_user",
            "created_on",
            "updated_app",
            "updated_user",
            "updated_on"
        ]
        assert audit_column_names == expected

    def test_audit_columns_defined(self):
        """Test audit columns are defined"""
        from db import audit_columns

        assert len(audit_columns) == 6

        column_names = [col.name for col in audit_columns]
        assert "created_app" in column_names
        assert "created_user" in column_names
        assert "created_on" in column_names
        assert "updated_app" in column_names
        assert "updated_user" in column_names
        assert "updated_on" in column_names
