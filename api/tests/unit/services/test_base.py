"""Tests for services/base.py module - Base service utilities"""

from unittest.mock import MagicMock

import pytest

from services.base import BaseService, to_camel_case, transform_dict_to_camel_case


class TestToCamelCase:
    """Tests for to_camel_case function"""

    def test_single_word(self):
        """Test single word remains unchanged"""
        assert to_camel_case("name") == "name"

    def test_two_words(self):
        """Test two word snake_case conversion"""
        assert to_camel_case("first_name") == "firstName"

    def test_multiple_words(self):
        """Test multiple word snake_case conversion"""
        assert to_camel_case("external_brewing_tool_meta") == "externalBrewingToolMeta"

    def test_already_camel_case(self):
        """Test already camelCase string (no underscores)"""
        assert to_camel_case("firstName") == "firstName"

    def test_single_char_words(self):
        """Test with single character words"""
        assert to_camel_case("a_b_c") == "aBC"

    def test_numbers_in_name(self):
        """Test with numbers in name"""
        assert to_camel_case("field_1_name") == "field1Name"

    def test_trailing_underscore(self):
        """Test with trailing underscore"""
        assert to_camel_case("name_") == "name"

    def test_leading_underscore(self):
        """Test with leading underscore"""
        result = to_camel_case("_private_field")
        assert result == "PrivateField"


class TestTransformDictToCamelCase:
    """Tests for transform_dict_to_camel_case function"""

    def test_simple_dict(self):
        """Test simple dict transformation"""
        data = {"first_name": "John", "last_name": "Doe"}
        result = transform_dict_to_camel_case(data)
        assert result == {"firstName": "John", "lastName": "Doe"}

    def test_nested_dict(self):
        """Test nested dict transformation"""
        data = {"user_info": {"first_name": "John", "email_address": "john@test.com"}}
        result = transform_dict_to_camel_case(data)
        assert result == {"userInfo": {"firstName": "John", "emailAddress": "john@test.com"}}

    def test_list_of_dicts(self):
        """Test list of dicts transformation"""
        data = {"users": [{"first_name": "John"}, {"first_name": "Jane"}]}
        result = transform_dict_to_camel_case(data)
        assert result == {"users": [{"firstName": "John"}, {"firstName": "Jane"}]}

    def test_removes_none_values(self):
        """Test that None values are removed"""
        data = {"name": "John", "age": None, "city": "NYC"}
        result = transform_dict_to_camel_case(data)
        assert result == {"name": "John", "city": "NYC"}
        assert "age" not in result

    def test_preserves_non_underscore_keys(self):
        """Test keys without underscores are preserved"""
        data = {"name": "John", "email": "john@test.com"}
        result = transform_dict_to_camel_case(data)
        assert result == {"name": "John", "email": "john@test.com"}

    def test_none_input(self):
        """Test None input returns None"""
        assert transform_dict_to_camel_case(None) is None

    def test_list_input(self):
        """Test list input is transformed"""
        data = [{"first_name": "John"}, {"first_name": "Jane"}]
        result = transform_dict_to_camel_case(data)
        assert result == [{"firstName": "John"}, {"firstName": "Jane"}]

    def test_primitive_input(self):
        """Test primitive values pass through unchanged"""
        assert transform_dict_to_camel_case("string") == "string"
        assert transform_dict_to_camel_case(123) == 123
        assert transform_dict_to_camel_case(True) is True

    def test_deeply_nested(self):
        """Test deeply nested structure"""
        data = {"level_one": {"level_two": {"level_three": {"deep_value": "test"}}}}
        result = transform_dict_to_camel_case(data)
        assert result["levelOne"]["levelTwo"]["levelThree"]["deepValue"] == "test"

    def test_mixed_list_values(self):
        """Test list with mixed types"""
        data = {"items": [{"item_name": "first"}, "string_value", 123, {"another_item": "second"}]}
        result = transform_dict_to_camel_case(data)
        assert result["items"][0] == {"itemName": "first"}
        assert result["items"][1] == "string_value"
        assert result["items"][2] == 123
        assert result["items"][3] == {"anotherItem": "second"}

    def test_empty_dict(self):
        """Test empty dict"""
        assert transform_dict_to_camel_case({}) == {}

    def test_empty_list(self):
        """Test empty list"""
        assert transform_dict_to_camel_case([]) == []


class TestBaseService:
    """Tests for BaseService class"""

    def test_transform_response_returns_none_for_none(self):
        """Test transform_response returns None for None input"""
        result = BaseService.transform_response(None)
        assert result is None

    def test_transform_response_calls_to_dict(self):
        """Test transform_response calls model's to_dict method"""
        mock_model = MagicMock()
        mock_model.to_dict.return_value = {"first_name": "John", "last_name": "Doe"}

        result = BaseService.transform_response(mock_model)

        mock_model.to_dict.assert_called_once()
        assert result == {"firstName": "John", "lastName": "Doe"}

    def test_transform_response_removes_none_values(self):
        """Test transform_response removes None values"""
        mock_model = MagicMock()
        mock_model.to_dict.return_value = {"name": "John", "age": None}

        result = BaseService.transform_response(mock_model)

        assert "age" not in result
        assert result == {"name": "John"}

    def test_transform_response_list(self):
        """Test transform_response_list transforms multiple models"""
        mock1 = MagicMock()
        mock1.to_dict.return_value = {"user_name": "john"}
        mock2 = MagicMock()
        mock2.to_dict.return_value = {"user_name": "jane"}

        result = BaseService.transform_response_list([mock1, mock2])

        assert len(result) == 2
        assert result[0] == {"userName": "john"}
        assert result[1] == {"userName": "jane"}

    def test_transform_response_list_empty(self):
        """Test transform_response_list with empty list"""
        result = BaseService.transform_response_list([])
        assert result == []

    def test_transform_response_list_with_none_items(self):
        """Test transform_response_list handles None items"""
        mock = MagicMock()
        mock.to_dict.return_value = {"name": "test"}

        result = BaseService.transform_response_list([mock, None])

        assert len(result) == 2
        assert result[0] == {"name": "test"}
        assert result[1] is None
