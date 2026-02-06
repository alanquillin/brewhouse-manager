"""Tests for lib/__init__.py module (Singleton, ThreadSafeSingleton, UsefulEnum)"""

import threading

import pytest

from lib import Singleton, ThreadSafeSingleton, UsefulEnum
from lib.exceptions import InvalidEnum


class TestSingleton:
    """Tests for Singleton metaclass"""

    def setup_method(self):
        """Clear singleton instances before each test"""
        Singleton._instances = {}

    def test_singleton_returns_same_instance(self):
        """Test that Singleton returns the same instance"""

        class MySingleton(metaclass=Singleton):
            def __init__(self, value=None):
                self.value = value

        instance1 = MySingleton(value="first")
        instance2 = MySingleton(value="second")

        assert instance1 is instance2
        assert instance1.value == "first"  # Second call doesn't reinitialize

    def test_different_singleton_classes_have_different_instances(self):
        """Test that different singleton classes have independent instances"""

        class SingletonA(metaclass=Singleton):
            pass

        class SingletonB(metaclass=Singleton):
            pass

        instance_a = SingletonA()
        instance_b = SingletonB()

        assert instance_a is not instance_b


class TestThreadSafeSingleton:
    """Tests for ThreadSafeSingleton metaclass"""

    def setup_method(self):
        """Clear singleton instances before each test"""
        ThreadSafeSingleton._instances = {}

    def test_thread_safe_singleton_returns_same_instance(self):
        """Test that ThreadSafeSingleton returns the same instance"""

        class MyThreadSafeSingleton(metaclass=ThreadSafeSingleton):
            def __init__(self, value=None):
                self.value = value

        instance1 = MyThreadSafeSingleton(value="first")
        instance2 = MyThreadSafeSingleton(value="second")

        assert instance1 is instance2
        assert instance1.value == "first"

    def test_thread_safe_singleton_concurrent_access(self):
        """Test that ThreadSafeSingleton works correctly with concurrent access"""

        class ConcurrentSingleton(metaclass=ThreadSafeSingleton):
            def __init__(self):
                self.initialized = True

        instances = []
        errors = []

        def create_instance():
            try:
                instance = ConcurrentSingleton()
                instances.append(instance)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=create_instance) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(instances) == 10
        # All instances should be the same object
        assert all(inst is instances[0] for inst in instances)


class TestUsefulEnum:
    """Tests for UsefulEnum class"""

    def test_str_returns_value(self):
        """Test that __str__ returns the enum value"""

        class Color(UsefulEnum):
            RED = "red"
            BLUE = "blue"

        assert str(Color.RED) == "red"
        assert str(Color.BLUE) == "blue"

    def test_eq_with_string(self):
        """Test equality comparison with string"""

        class Status(UsefulEnum):
            ACTIVE = "active"
            INACTIVE = "inactive"

        assert Status.ACTIVE == "active"
        assert Status.INACTIVE == "inactive"
        assert not (Status.ACTIVE == "inactive")

    def test_eq_with_enum(self):
        """Test equality comparison with another enum"""

        class Status(UsefulEnum):
            ACTIVE = "active"

        assert Status.ACTIVE == Status.ACTIVE

    def test_hash(self):
        """Test that enum values can be used in sets and dicts"""

        class Color(UsefulEnum):
            RED = "red"
            BLUE = "blue"

        color_set = {Color.RED, Color.BLUE}
        assert Color.RED in color_set
        assert len(color_set) == 2

        color_dict = {Color.RED: 1, Color.BLUE: 2}
        assert color_dict[Color.RED] == 1

    def test_find_existing_value(self):
        """Test find() returns correct enum for existing value"""

        class Size(UsefulEnum):
            SMALL = "small"
            LARGE = "large"

        assert Size.find("small") == Size.SMALL
        assert Size.find("large") == Size.LARGE

    def test_find_invalid_value_raises(self):
        """Test find() raises InvalidEnum for invalid value"""

        class Size(UsefulEnum):
            SMALL = "small"

        with pytest.raises(InvalidEnum):
            Size.find("medium")

    def test_find_invalid_value_with_default(self):
        """Test find() returns default when raise_on_not_found=False"""

        class Size(UsefulEnum):
            SMALL = "small"

        result = Size.find("medium", raise_on_not_found=False, default=None)
        assert result is None

        result = Size.find("medium", raise_on_not_found=False, default=Size.SMALL)
        assert result == Size.SMALL

    def test_missing_raises_invalid_enum(self):
        """Test that creating enum with invalid value raises InvalidEnum"""

        class Size(UsefulEnum):
            SMALL = "small"

        with pytest.raises(InvalidEnum) as exc_info:
            Size("medium")

        assert "medium" in str(exc_info.value)
        assert "Size" in str(exc_info.value)
