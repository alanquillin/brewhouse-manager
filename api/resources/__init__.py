import logging
import os
import urllib.parse
from functools import wraps

import dns.exception
import dns.resolver
import sqlalchemy
from flask import redirect, request, send_from_directory, session
from flask_restful import Resource
from schema import Schema, SchemaError, SchemaMissingKeyError

from db import session_scope
from db.locations import Locations as LocationsDB
from lib import util
from lib.config import Config
from resources.exceptions import *

LOGGER = logging.getLogger(__name__)
STATIC_URL_PATH = "static"

config = Config()


def _fetch_dns_records(domain, record_type="A", resolver=None):
    if not resolver:
        resolver = dns.resolver

    response_field = "address"
    if record_type == "SOA":
        response_field = "mname"

    return [getattr(resp, response_field) for resp in resolver.resolve(domain, record_type).rrset]


def convert_exceptions(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (SchemaError, SchemaMissingKeyError) as exc:
            LOGGER.exception(str(exc))
            return {"message": str(exc)}, 400
        except sqlalchemy.exc.StatementError as exc:
            if isinstance(exc.orig, ValueError):
                return {"message": f"Bad value: {str(exc.orig)}"}, 400
            raise
        except UserMessageError as exc:
            LOGGER.exception(exc.server_msg)
            return {"message": exc.user_msg}, exc.response_code
        except Exception as exc:  # pylint: disable=broad-except
            LOGGER.exception("Unknown exception while processing request:")
            return {"message": "An unhandled error occurred while processing the request"}, 500

    return decorator


def convert_ui_exceptions(func):
    @wraps(func)
    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except NotAuthorizedError as exc:
            LOGGER.error(exc.server_msg)
            return redirect("/login?error=%s" % urllib.parse.quote_plus(exc.user_msg))
        except ForbiddenError as exc:
            LOGGER.error(exc.server_msg)
            return redirect("/forbidden")
        except UserMessageError as exc:
            LOGGER.exception(exc.server_msg)
            return redirect("/error")
        except Exception:  # pylint: disable=broad-except
            LOGGER.exception("An unknown or unexpected error has occurred.  Redirecting to /error")
            return redirect("/error")

    return decorator


def with_schema_validation(schema):
    def wrapper(f):
        @wraps(f)
        def strict_schema(*args, **kwargs):
            schema.validate(request.get_json(force=True))
            return f(*args, **kwargs)

        return strict_schema

    return wrapper


def transform_request_data(original_data):
    if not original_data:
        return {}

    data = {}
    for k, v in original_data.items():
        if isinstance(v, dict):
            v = transform_request_data(v)
        data[util.camel_to_snake(k)] = v
    return data


def transform_response(data, transform_keys=None, filtered_keys=None):
    if not data:
        return data

    if isinstance(data, BaseResource):
        return transform_response(data.to_dict())
    transformed = {}

    if not transform_keys:
        transform_keys = {}

    if not filtered_keys:
        filtered_keys = {}

    def get_filtered(obj, paths):
        if paths == {}:
            return None
        if not paths:
            return obj
        deleted = []
        for key in obj:
            obj[key] = get_filtered(obj.get(key), paths.get(key))
            if not obj[key]:
                deleted.append(key)

        for key in deleted:
            del obj[key]
        return obj

    for key, val in data.items():
        val = get_filtered(val, filtered_keys.get(key))

        if val is None:
            continue

        if key in transform_keys:
            _key = transform_keys[key]
        else:
            _key = "".join([key.title() if ix > 0 else key.lower() for ix, key in enumerate(key.split("_"))])

        if isinstance(val, dict):
            val = transform_response(val)

        transformed[_key] = val

    return transformed


def generate_filtered_keys(key_list):
    def get(obj, key):
        obj[key] = obj.get(key, {})
        return obj[key]

    key_set = {}
    for key in key_list:
        path = str.split(key, ".")
        current = key_set

        for field in path:
            current = get(current, field)

    return key_set


class BaseResource(Resource):
    schema = Schema({})

    method_decorators = [convert_exceptions]

    def __init__(self):
        super().__init__()

        self.config = Config()
        self.logger = logging.getLogger(self.__class__.__name__)


class UIBaseResource(BaseResource):
    schema = Schema({})

    def __init__(self):
        super().__init__()
        self.method_decorators = [convert_ui_exceptions] + self.method_decorators

    @staticmethod
    def serve_app():
        dir_path = os.path.join(os.getcwd(), STATIC_URL_PATH)
        return send_from_directory(dir_path, "index.html")


class ResourceMixinBase:
    def __init__(self):
        super().__init__()

        self.config = Config()
        self.logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def get_request_data(remove_key=[]):
        j = request.get_json()

        if remove_key:
            data = {}
            for k, v in j.items():
                if k not in remove_key:
                    data[k] = v
        else:
            data = j

        return transform_request_data(data)

    @staticmethod
    def transform_response(entity, filtered_keys=None):
        return transform_response(entity, filtered_keys=filtered_keys)

    def _get_location_id(self, location_name, db_session=None):
        if not db_session:
            with session_scope(self.config) as db_session:
                return self._get_location_id(location_name, db_session)

        res = LocationsDB.query(db_session, name=location_name)
        loc = None
        if res:
            loc = res[0].id
        return loc

    def get_location_id(self, location, db_session=None):
        if util.is_valid_uuid(location):
            return location

        return self._get_location_id(location, db_session)
