import threading
from enum import Enum

from lib.exceptions import *


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class ThreadSafeSingleton(type):
    _instances = {}
    _singleton_lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._singleton_lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(ThreadSafeSingleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class UsefulEnum(Enum):
    def __str__(self):  # pylint: disable=invalid-str-returned
        return self.value

    def __eq__(self, other):
        if not isinstance(other, Enum):
            return str(self) == other
        return self.value == other.value  # pylint: disable=comparison-with-callable

    def __hash__(self):
        return hash(self.value)

    @classmethod
    def find(cls, value, raise_on_not_found=True, default=None):
        try:
            return cls(value)
        except InvalidEnum:
            if raise_on_not_found:
                raise
            return default

    @classmethod
    def _missing_(cls, value):
        raise InvalidEnum(f"{value} is not a valid {cls.__name__}")
