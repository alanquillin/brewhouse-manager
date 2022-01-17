import itertools

from sqlalchemy.ext.mutable import Mutable

__all__ = ["NestedMutableList", "NestedMutableDict"]


class TrackedObject:
    _type_mapping = {}

    def __init__(self, *args, **kwds):
        self.parent = None
        super().__init__(*args, **kwds)

    def changed(self):
        if self.parent is not None:
            self.parent.changed()
        elif isinstance(self, Mutable):
            super().changed()

    @classmethod
    def register(cls, origin_type):
        def decorator(tracked_type):
            cls._type_mapping[origin_type] = tracked_type
            return tracked_type

        return decorator

    @classmethod
    def convert(cls, obj, parent):
        replacement_type = cls._type_mapping.get(type(obj))
        if replacement_type is not None:
            new = replacement_type(obj)
            new.parent = parent
            return new
        return obj

    def convert_iterable(self, iterable):
        return (self.convert(item, self) for item in iterable)

    def convert_items(self, items):
        return ((key, self.convert(value, self)) for key, value in items)

    def convert_mapping(self, mapping):
        if isinstance(mapping, dict):
            return self.convert_items(mapping.items())
        return self.convert_items(mapping)

    def _repr(self):
        return "<%(namespace)s.%(type)s object at 0x%(address)0xd>" % {
            "namespace": __name__,
            "type": type(self).__name__,
            "address": id(self),
        }


@TrackedObject.register(dict)
class TrackedDict(TrackedObject, dict):
    def __init__(self, source=(), **kwds):
        super().__init__(itertools.chain(self.convert_mapping(source), self.convert_mapping(kwds)))

    def __setitem__(self, key, value):
        self.changed()
        super().__setitem__(key, self.convert(value, self))

    def __delitem__(self, key):
        self.changed()
        super().__delitem__(key)

    def clear(self):
        self.changed()
        super().clear()

    def pop(self, *key_and_default):
        self.changed()
        return super().pop(*key_and_default)

    def popitem(self):
        self.changed()
        return super().popitem()

    def update(self, source=(), **kwds):
        self.changed()
        super().update(itertools.chain(self.convert_mapping(source), self.convert_mapping(kwds)))

    def setdefault(self, key, default=None):
        if key in self:
            return self[key]

        self[key] = default
        return self[key]


@TrackedObject.register(list)
class TrackedList(TrackedObject, list):
    def __init__(self, iterable=()):
        super().__init__(self.convert_iterable(iterable))

    def __setitem__(self, key, value):
        self.changed()
        super().__setitem__(key, self.convert(value, self))

    def __delitem__(self, key):
        self.changed()
        super().__delitem__(key)

    def append(self, item):
        self.changed()
        super().append(self.convert(item, self))

    def extend(self, iterable):
        self.changed()
        super().extend(self.convert_iterable(iterable))

    def remove(self, value):
        self.changed()
        return super().remove(value)

    def pop(self, index):
        self.changed()
        return super().pop(index)

    def sort(self, cmp=None, key=None, reverse=False):
        self.changed()
        super().sort(cmp=cmp, key=key, reverse=reverse)


class NestedMutableDict(Mutable, TrackedDict):
    @classmethod
    def coerce(cls, key, value):
        if isinstance(value, cls):
            return value
        if isinstance(value, dict):
            return cls(value)
        return Mutable.coerce(key, value)


class NestedMutableList(Mutable, TrackedList):
    @classmethod
    def coerce(cls, key, value):
        if isinstance(value, cls):
            return value
        if isinstance(value, list):
            return cls(value)
        return Mutable.coerce(key, value)
