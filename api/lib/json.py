# pylint: disable=unused-import
# by importing these names, we're exposing the standard lib JSON functionality to library clients

import json
from datetime import datetime
from json import dump
from json import dumps as _dumps
from json import load, loads
from uuid import UUID
import simplejson

from lib import UsefulEnum


class CloudCommonJsonEncoder(simplejson.JSONEncoder):
    def default(self, o):  # pylint: disable=method-hidden
        if isinstance(o, datetime):
            return o.isoformat()
        if isinstance(o, UsefulEnum):
            return str(o)
        if hasattr(o, "_json_repr_"):
            return o._json_repr_()  # pylint: disable=protected-access
        if isinstance(o, UUID):
            # if the obj is uuid, we simply return the value of uuid
            return o.hex
        return super().default(o)


def dumps(data, *_, **kwargs):
    kwargs["cls"] = CloudCommonJsonEncoder
    return _dumps(data, **kwargs)
