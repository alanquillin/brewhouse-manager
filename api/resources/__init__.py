import logging
from operator import truediv
import os
import urllib.parse
from functools import wraps

import sqlalchemy
from flask import redirect, request, send_from_directory, session
from flask_restful import Resource
from flask_login import current_user
from schema import Schema, SchemaError, SchemaMissingKeyError

from db import session_scope
from db.image_transitions import ImageTransitions as ImageTransitionsDB
from db.locations import Locations as LocationsDB
from lib import util
from lib.config import Config
from resources.exceptions import *

LOGGER = logging.getLogger(__name__)
STATIC_URL_PATH = "static"

config = Config()

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
            if not current_user:
                LOGGER.debug("No user logged in... redirecting to login page")
                return redirect("/login?error=%s" % urllib.parse.quote_plus(exc.user_msg))
            else:
                LOGGER.debug("User %s logged in... redirecting to /unauthorized", current_user.email)
                return redirect("/unauthorized")
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

    if not isinstance(original_data, dict):
        return original_data
    
    data = {}
    for k, v in original_data.items():
        if isinstance(v, dict):
            v = transform_request_data(v)
        if isinstance(v, list):
            v = [transform_request_data(i) for i in v]
        data[util.camel_to_snake(k)] = v
    return data


def transform_response(data, transform_keys=None, remove_keys=None):
    if not data:
        return data

    if getattr(data, "to_dict", None):
        return transform_response(data.to_dict(), transform_keys=transform_keys, remove_keys=remove_keys)

    if isinstance(data, BaseResource):
        return transform_response(data.to_dict(), transform_keys=transform_keys, remove_keys=remove_keys)

    if isinstance(data, list):
        return [transform_response(d, transform_keys=transform_keys, remove_keys=remove_keys) for d in data]

    transformed = {}

    if not transform_keys:
        transform_keys = {}

    if not remove_keys:
        remove_keys = []

    for key, val in data.items():
        if key in remove_keys:
            continue

        if val is None:
            continue

        if key in transform_keys:
            _key = transform_keys[key]
        elif "_" in key:
            _key = "".join([key.title() if ix > 0 else key.lower() for ix, key in enumerate(key.split("_"))])
        else:
            _key = key

        if isinstance(val, dict):
            val = transform_response(val, transform_keys=transform_keys, remove_keys=remove_keys)

        transformed[_key] = val

    return transformed

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
    def transform_response(entity, remove_keys=None, **kwargs):
        return transform_response(entity, remove_keys=remove_keys)

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

class ImageTransitionMixin:
    def __init__(self):
        super().__init__()

        self.config = Config()
        self.logger = logging.getLogger(self.__class__.__name__)

    def process_image_transitions(self, db_session, **kwargs):
        j = request.get_json()
        data = transform_request_data(j)
        self.logger.debug("transformed request data: %s", data)

        transitions = data.get("image_transitions")
        self.logger.debug("image transition data: %s", transitions)

        if transitions:
            ret_data = []
            for transition in transitions:
                if kwargs:
                    transition.update(kwargs)
                if transition.get("id"):
                    id = transition.pop("id")
                    self.logger.debug("Updating image transition %s with: %s", id, transition)
                    ret_data.append(ImageTransitionsDB.update(db_session, id, **transition))
                else:
                    self.logger.debug("Creating image transition with: %s", transition)
                    ret_data.append(ImageTransitionsDB.create(db_session, **transition))
            return ret_data
        return None

class ImageTransitionResourceMixin(ResourceMixinBase):
    
    @staticmethod
    def transform_response(data, image_transitions, db_session=None, **kwargs):
        if not db_session:
            with session_scope(config) as db_session:
                return ImageTransitionResourceMixin.transform_response(data, image_transitions, db_session=db_session, **kwargs)

        if not image_transitions:
            image_transitions = ImageTransitionsDB.query(db_session, **kwargs)

        if image_transitions:
            data["image_transitions"] = [ResourceMixinBase.transform_response(it.to_dict()) for it in image_transitions]

        return ResourceMixinBase.transform_response(data, **kwargs)


def requires_admin(func):
    def wrapper(*args, **kwargs):
        if not current_user.admin:
            raise NotAuthorizedError()
        return func(*args, **kwargs)
    return wrapper