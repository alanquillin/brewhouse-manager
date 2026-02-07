"""Tests for db/types/nested.py module - JSONB change tracking utilities"""

from unittest.mock import MagicMock

import pytest

from db.types.nested import NestedMutableDict, NestedMutableList, TrackedDict, TrackedList, TrackedObject


class TestTrackedObject:
    """Tests for TrackedObject base class"""

    def test_init_sets_parent_to_none(self):
        """Test that parent is None by default"""
        obj = TrackedObject()
        assert obj.parent is None

    def test_changed_calls_parent_changed(self):
        """Test that changed() propagates to parent"""
        parent = MagicMock()
        obj = TrackedObject()
        obj.parent = parent

        obj.changed()

        parent.changed.assert_called_once()

    def test_register_decorator(self):
        """Test that register decorator adds type mapping"""
        # dict and list are already registered, verify they're in mapping
        assert dict in TrackedObject._type_mapping
        assert list in TrackedObject._type_mapping
        assert TrackedObject._type_mapping[dict] == TrackedDict
        assert TrackedObject._type_mapping[list] == TrackedList

    def test_convert_with_known_type(self):
        """Test convert replaces known types with tracked versions"""
        parent = MagicMock()
        result = TrackedObject.convert({"key": "value"}, parent)

        assert isinstance(result, TrackedDict)
        assert result.parent == parent

    def test_convert_with_unknown_type(self):
        """Test convert returns unknown types unchanged"""
        parent = MagicMock()
        original = "string value"
        result = TrackedObject.convert(original, parent)

        assert result is original

    def test_convert_list(self):
        """Test convert works with lists"""
        parent = MagicMock()
        result = TrackedObject.convert([1, 2, 3], parent)

        assert isinstance(result, TrackedList)
        assert result.parent == parent


class TestTrackedDict:
    """Tests for TrackedDict class"""

    def test_init_empty(self):
        """Test creating empty TrackedDict"""
        d = TrackedDict()
        assert len(d) == 0

    def test_init_from_dict(self):
        """Test creating TrackedDict from dict"""
        d = TrackedDict({"a": 1, "b": 2})
        assert d["a"] == 1
        assert d["b"] == 2

    def test_init_from_kwargs(self):
        """Test creating TrackedDict from kwargs"""
        d = TrackedDict(a=1, b=2)
        assert d["a"] == 1
        assert d["b"] == 2

    def test_setitem_calls_changed(self):
        """Test __setitem__ calls changed()"""
        d = TrackedDict()
        d.parent = MagicMock()

        d["key"] = "value"

        d.parent.changed.assert_called()

    def test_setitem_converts_nested_dict(self):
        """Test __setitem__ converts nested dicts"""
        d = TrackedDict()
        d["nested"] = {"inner": "value"}

        assert isinstance(d["nested"], TrackedDict)
        assert d["nested"]["inner"] == "value"

    def test_delitem_calls_changed(self):
        """Test __delitem__ calls changed()"""
        d = TrackedDict({"key": "value"})
        d.parent = MagicMock()

        del d["key"]

        d.parent.changed.assert_called()

    def test_clear_calls_changed(self):
        """Test clear() calls changed()"""
        d = TrackedDict({"a": 1, "b": 2})
        d.parent = MagicMock()

        d.clear()

        d.parent.changed.assert_called()
        assert len(d) == 0

    def test_pop_calls_changed(self):
        """Test pop() calls changed()"""
        d = TrackedDict({"key": "value"})
        d.parent = MagicMock()

        result = d.pop("key")

        d.parent.changed.assert_called()
        assert result == "value"

    def test_pop_with_default(self):
        """Test pop() with default value"""
        d = TrackedDict()
        d.parent = MagicMock()

        result = d.pop("missing", "default")

        assert result == "default"

    def test_popitem_calls_changed(self):
        """Test popitem() calls changed()"""
        d = TrackedDict({"key": "value"})
        d.parent = MagicMock()

        result = d.popitem()

        d.parent.changed.assert_called()
        assert result == ("key", "value")

    def test_update_calls_changed(self):
        """Test update() calls changed()"""
        d = TrackedDict()
        d.parent = MagicMock()

        d.update({"a": 1, "b": 2})

        d.parent.changed.assert_called()
        assert d["a"] == 1
        assert d["b"] == 2

    def test_update_converts_nested(self):
        """Test update() converts nested structures"""
        d = TrackedDict()
        d.update({"nested": {"inner": "value"}})

        assert isinstance(d["nested"], TrackedDict)

    def test_setdefault_existing_key(self):
        """Test setdefault() with existing key"""
        d = TrackedDict({"key": "original"})

        result = d.setdefault("key", "default")

        assert result == "original"
        assert d["key"] == "original"

    def test_setdefault_missing_key(self):
        """Test setdefault() with missing key"""
        d = TrackedDict()
        d.parent = MagicMock()

        result = d.setdefault("key", "default")

        assert result == "default"
        assert d["key"] == "default"

    def test_nested_change_propagation(self):
        """Test changes in nested dict propagate to root"""
        root = TrackedDict()
        root.parent = MagicMock()
        root["level1"] = {"level2": "value"}

        # Modify nested dict
        root["level1"]["level2"] = "new_value"

        # Change should propagate to root's parent
        assert root.parent.changed.call_count >= 1


class TestTrackedList:
    """Tests for TrackedList class"""

    def test_init_empty(self):
        """Test creating empty TrackedList"""
        lst = TrackedList()
        assert len(lst) == 0

    def test_init_from_iterable(self):
        """Test creating TrackedList from iterable"""
        lst = TrackedList([1, 2, 3])
        assert list(lst) == [1, 2, 3]

    def test_setitem_calls_changed(self):
        """Test __setitem__ calls changed()"""
        lst = TrackedList([1, 2, 3])
        lst.parent = MagicMock()

        lst[0] = 10

        lst.parent.changed.assert_called()
        assert lst[0] == 10

    def test_setitem_converts_nested(self):
        """Test __setitem__ converts nested structures"""
        lst = TrackedList([None])
        lst[0] = {"key": "value"}

        assert isinstance(lst[0], TrackedDict)

    def test_delitem_calls_changed(self):
        """Test __delitem__ calls changed()"""
        lst = TrackedList([1, 2, 3])
        lst.parent = MagicMock()

        del lst[0]

        lst.parent.changed.assert_called()
        assert list(lst) == [2, 3]

    def test_append_calls_changed(self):
        """Test append() calls changed()"""
        lst = TrackedList()
        lst.parent = MagicMock()

        lst.append(1)

        lst.parent.changed.assert_called()
        assert lst[0] == 1

    def test_append_converts_nested(self):
        """Test append() converts nested structures"""
        lst = TrackedList()
        lst.append({"key": "value"})

        assert isinstance(lst[0], TrackedDict)

    def test_extend_calls_changed(self):
        """Test extend() calls changed()"""
        lst = TrackedList([1])
        lst.parent = MagicMock()

        lst.extend([2, 3])

        lst.parent.changed.assert_called()
        assert list(lst) == [1, 2, 3]

    def test_extend_converts_nested(self):
        """Test extend() converts nested structures"""
        lst = TrackedList()
        lst.extend([{"a": 1}, {"b": 2}])

        assert isinstance(lst[0], TrackedDict)
        assert isinstance(lst[1], TrackedDict)

    def test_remove_calls_changed(self):
        """Test remove() calls changed()"""
        lst = TrackedList([1, 2, 3])
        lst.parent = MagicMock()

        lst.remove(2)

        lst.parent.changed.assert_called()
        assert list(lst) == [1, 3]

    def test_pop_calls_changed(self):
        """Test pop() calls changed()"""
        lst = TrackedList([1, 2, 3])
        lst.parent = MagicMock()

        result = lst.pop(0)

        lst.parent.changed.assert_called()
        assert result == 1
        assert list(lst) == [2, 3]

    def test_nested_list_in_dict(self):
        """Test nested list inside TrackedDict"""
        d = TrackedDict()
        d["items"] = [1, 2, 3]

        assert isinstance(d["items"], TrackedList)
        assert d["items"].parent == d

    def test_nested_dict_in_list(self):
        """Test nested dict inside TrackedList"""
        lst = TrackedList()
        lst.append({"key": "value"})

        assert isinstance(lst[0], TrackedDict)
        assert lst[0].parent == lst


class TestNestedMutableDict:
    """Tests for NestedMutableDict class"""

    def test_coerce_dict(self):
        """Test coerce converts dict to NestedMutableDict"""
        result = NestedMutableDict.coerce("key", {"a": 1})

        assert isinstance(result, NestedMutableDict)
        assert result["a"] == 1

    def test_coerce_already_nested_mutable(self):
        """Test coerce returns NestedMutableDict unchanged"""
        original = NestedMutableDict({"a": 1})
        result = NestedMutableDict.coerce("key", original)

        assert result is original

    def test_coerce_none(self):
        """Test coerce handles None"""
        result = NestedMutableDict.coerce("key", None)
        assert result is None

    def test_inherits_tracked_dict_behavior(self):
        """Test NestedMutableDict has TrackedDict behavior"""
        d = NestedMutableDict({"a": 1})
        d["nested"] = {"b": 2}

        assert isinstance(d["nested"], TrackedDict)


class TestNestedMutableList:
    """Tests for NestedMutableList class"""

    def test_coerce_list(self):
        """Test coerce converts list to NestedMutableList"""
        result = NestedMutableList.coerce("key", [1, 2, 3])

        assert isinstance(result, NestedMutableList)
        assert list(result) == [1, 2, 3]

    def test_coerce_already_nested_mutable(self):
        """Test coerce returns NestedMutableList unchanged"""
        original = NestedMutableList([1, 2, 3])
        result = NestedMutableList.coerce("key", original)

        assert result is original

    def test_coerce_none(self):
        """Test coerce handles None"""
        result = NestedMutableList.coerce("key", None)
        assert result is None

    def test_inherits_tracked_list_behavior(self):
        """Test NestedMutableList has TrackedList behavior"""
        lst = NestedMutableList([{"a": 1}])

        assert isinstance(lst[0], TrackedDict)


class TestDeepNesting:
    """Tests for deeply nested structures"""

    def test_deeply_nested_dict(self):
        """Test deeply nested dict structure"""
        d = TrackedDict()
        d["l1"] = {"l2": {"l3": {"l4": "value"}}}

        assert isinstance(d["l1"], TrackedDict)
        assert isinstance(d["l1"]["l2"], TrackedDict)
        assert isinstance(d["l1"]["l2"]["l3"], TrackedDict)
        assert d["l1"]["l2"]["l3"]["l4"] == "value"

    def test_mixed_nesting(self):
        """Test mixed dict/list nesting"""
        d = TrackedDict()
        d["items"] = [{"name": "item1"}, {"name": "item2"}]

        assert isinstance(d["items"], TrackedList)
        assert isinstance(d["items"][0], TrackedDict)
        assert d["items"][0]["name"] == "item1"

    def test_change_propagation_deep(self):
        """Test change propagation through deep nesting"""
        root = NestedMutableDict()
        root["l1"] = {"l2": {"l3": "value"}}

        # Track that changed() was called on root
        original_changed = root.changed
        changed_called = []

        def track_changed():
            changed_called.append(True)
            original_changed()

        root.changed = track_changed

        # Modify deeply nested value
        root["l1"]["l2"]["l3"] = "new_value"

        assert len(changed_called) >= 1
