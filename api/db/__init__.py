import re
from contextlib import contextmanager
from functools import wraps
from urllib.parse import quote

from psycopg2.errors import InvalidTextRepresentation, NotNullViolation, UniqueViolation  # pylint: disable=no-name-in-module
from psycopg2.extensions import QuotedString, register_adapter
from sqlalchemy import DDL, Column, DateTime, Integer, String, create_engine, event, func, text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.properties import ColumnProperty
from sqlalchemy.orm.session import Session

from lib import exceptions as local_exc
from lib import json

Base = declarative_base()

__all__ = ["Base", "audit", "beers", "beverages", "locations", "sensors", "taps", "users", "fermentation_ctrl", "fermentation_ctrl_stats", "image_transitions"]


@event.listens_for(Base.metadata, "before_create")
def create_extensions(_target, connection, **_):
    connection.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))


@contextmanager
def convert_exception(sqla, psycopg2=None, new=None, param_names=None, str_match=""):
    if param_names is None:
        param_names = []
    try:
        yield
    except sqla as exc:
        if str_match not in str(exc):
            raise

        if param_names:
            args = [str(exc.params.get(param)) for param in param_names]
        else:
            args = [str(exc)]

        if psycopg2 is None:
            raise new() from exc

        if isinstance(exc.orig, psycopg2):
            if not param_names:
                args = [str(exc.orig)]
            raise new(*args) from exc

        raise


def create_session(config, **kwargs):
    engine_kwargs = {
        "connect_args": {"application_name": config.get("app_id", f"UNKNOWN=>({__name__})")},
        "json_serializer": json.dumps,
    }

    password = config.get("db.password")

    if not password:
        engine_kwargs["connect_args"]["sslmode"] = "require"
        rds = aws.client("rds")
        password = rds.generate_db_auth_token(config.get("db.host"), config.get("db.port"), config.get("db.username"))

    engine = create_engine(
        (
            "postgresql://"
            f"{quote(config.get('db.username'))}:{quote(password)}@{quote(config.get('db.host'))}:"
            f"{config.get('db.port')}/{quote(config.get('db.name'))}"
        ),
        **engine_kwargs,
    )

    return sessionmaker(bind=engine, **kwargs)()


@contextmanager
def session_scope(config, **kwargs):
    session = create_session(config, **kwargs)
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def application_name_suffix(session, appname):
    original_value = session.execute("SELECT current_setting('application_name')").first()[0]
    session.execute(text("SET application_name TO :appname"), {"appname": f"{original_value}{appname}"})
    try:
        yield
    finally:
        session.execute(text("SET application_name TO :appname"), {"appname": original_value})


def generate_db_enum(enum):
    name = enum.__name__
    return ENUM(
        enum,
        name=name,
        metadata=Base.metadata,
        values_callable=lambda obj: [str(attr.value) for attr in obj.__members__.values()],
    )


def _get_column_value(instance, col_name):
    try:
        return getattr(instance, col_name)
    except AttributeError:
        for attr, column in inspect(instance.__class__).c.items():
            if column.name == col_name:
                return getattr(instance, attr)
    raise AttributeError


class DictifiableMixin:
    def to_dict(self, include_relationships=None):
        result = {}

        for name, attr in inspect(self.__class__).all_orm_descriptors.items():
            if name.startswith("_"):
                continue
            if hasattr(attr, "property") and not isinstance(attr.property, ColumnProperty):
                continue

            name = getattr(attr, "name", name)
            result[name] = _get_column_value(self, name)

        if not include_relationships:
            include_relationships = []

        for rel in include_relationships:
            val = getattr(self, rel)
            if val is not None:
                result[rel] = getattr(self, rel).to_dict()

        return result

    def _json_repr_(self, *args, **kwargs):
        return self.to_dict(*args, **kwargs)


class DictMethodsMixin:
    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except AttributeError:
            return default

    def __getitem__(self, key):
        return getattr(self, key)

    def __setitem__(self, key, value):
        return setattr(self, key, value)

    def __contains__(self, key):
        return hasattr(self, key)


class AuditedMixin:
    created_app = Column(String, server_default=func.current_setting("application_name"), nullable=False)
    created_user = Column(String, server_default=func.current_user(), nullable=False)
    created_on = Column(DateTime(timezone=True), server_default=func.current_timestamp(), nullable=False)
    updated_app = Column(
        String,
        server_default=func.current_setting("application_name"),
        onupdate=func.current_setting("application_name"),
        nullable=False,
    )
    updated_user = Column(String, server_default=func.current_user(), onupdate=func.current_user(), nullable=False)
    updated_on = Column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
        nullable=False,
    )


_MERGEABLE_FIELDS_LIST = "_mergeable_fields"


def mergeable_fields(*fields_list):
    def decorator(cls):
        setattr(cls, _MERGEABLE_FIELDS_LIST, fields_list)
        return cls

    return decorator


def flatten_relationship(relationship_name, property_name, cls_):
    def decorator(cls):

        # Setup hybrid property
        def prop(self):
            return getattr(self, relationship_name)

        def expr(cls):
            return getattr(cls, relationship_name)

        def setter(self, value):
            target = getattr(self, relationship_name, None)
            if target is None:
                setattr(self, relationship_name, cls_(**value))
            else:
                for k, v in value.items():
                    target[k] = v

        prop = hybrid_property(prop).expression(expr).setter(setter)

        setattr(cls, property_name, prop)

        return cls

    return decorator


_ENUM_EXC_MAP = "_custom_exception_map"


def _adapt_enum(value):
    return QuotedString(str(value))


def column_as_enum(existing_field, property_name, python_enum, custom_exc=local_exc.InvalidEnum):
    def decorator(cls):

        register_adapter(python_enum, _adapt_enum)

        # Setup hybrid property
        def prop(self):
            db_val = getattr(self, existing_field)
            if db_val is not None:
                return python_enum(db_val)
            return None

        def expr(cls):
            return getattr(cls, existing_field)

        def setter(self, value):
            if value is None:
                setattr(self, existing_field, None)
            else:
                setattr(self, existing_field, python_enum(value).value)

        prop = hybrid_property(prop).expression(expr).setter(setter)

        setattr(cls, property_name, prop)

        # Setup custom exception map
        exc_map = getattr(cls, _ENUM_EXC_MAP, {})
        exc_map[python_enum.__name__] = custom_exc
        setattr(cls, _ENUM_EXC_MAP, exc_map)

        return cls

    return decorator


def _merge_into(target, updates):
    if target is None:
        return updates

    for k, v in updates.items():
        if k in target and isinstance(v, dict) and isinstance(target[k], dict):
            _merge_into(target[k], v)
        elif k in target and isinstance(v, list) and isinstance(target[k], list):
            target[k].extend(v)
        else:
            target[k] = v
    return target


class QueryMethodsMixin:
    @classmethod
    def query(cls, session, q=None, slice_start=None, slice_end=None, **kwargs):
        if q is None:
            q = session.query(cls).filter_by(**kwargs)

        if not None in [slice_start, slice_end]:
            q = q.slice(slice_start, slice_end)

        try:
            return q.all()
        except DataError as err:
            if not isinstance(err.orig, InvalidTextRepresentation):
                raise
            if "invalid input value for enum" not in str(err.orig):
                raise

            # somewhat finicky parsing of the PG error here
            # expected format returned by str(err.orig):
            # E       psycopg2.errors.InvalidTextRepresentation: invalid input value for enum "OrderType": "invalid"
            # E       LINE 3: ...3-4b88-a6b0-5a01d901233f' AND orders.order_type = 'invalid' ...
            # E                                                                    ^

            msg, desc, pointer, _ = str(err.orig).split("\n")

            # get Enum name from the first line
            enum_name = msg.split("for enum ")[1].split(":")[0].strip('"')
            exc = getattr(cls, _ENUM_EXC_MAP).get(enum_name, local_exc.InvalidEnum)

            # Use the indicator on the third line to find the column name in the second line
            err_ix = pointer.index("^")
            _, column_name = desc[:err_ix].split()[-2].split(".")

            raise exc(err.params.get(column_name, "could not find offending value")) from err

    @classmethod
    def get_by_pkey(cls, session, pkey):
        return session.query(cls).get(pkey)

    @classmethod
    def create(cls, session, autocommit=True, **kwargs):
        for key in kwargs:
            if not hasattr(cls, key):
                raise local_exc.InvalidParameter(key)

        row = cls(**kwargs)
        session.add(row)

        if autocommit:
            try:
                with convert_exception(IntegrityError, psycopg2=NotNullViolation, new=local_exc.RequiredParameterNotFound), convert_exception(
                    IntegrityError, psycopg2=UniqueViolation, new=local_exc.ItemAlreadyExists, str_match="_pkey"
                ):
                    session.commit()
            except:
                session.rollback()
                raise

        return row

    @classmethod
    def update_query(cls, session, filters=None, **updates):
        if filters is None:
            filters = {}

        session.query(cls).filter_by(**filters).update(updates)

    @classmethod
    def update(cls, session, pkey, merge_nested=False, autocommit=True, **kwargs):
        merge_fields = getattr(cls, _MERGEABLE_FIELDS_LIST, [])
        row = cls.get_by_pkey(session, pkey)

        for key, value in kwargs.items():
            if not hasattr(cls, key):
                raise local_exc.InvalidParameter(key)

            if merge_nested and key in merge_fields:
                current = getattr(row, key, {})
                value = _merge_into(current, value)

            setattr(row, key, value)

        session.add(row)
        if autocommit:
            try:
                session.commit()
            except:
                session.rollback()
                raise

        return row

    @classmethod
    def delete(cls, session, pkey, autocommit=True):
        session.delete(cls.get_by_pkey(session, pkey))

        if autocommit:
            try:
                session.commit()
            except:
                session.rollback()
                raise


from .audit import setup_trigger  # pylint: disable=wrong-import-position,cyclic-import


def generate_audit_trail(cls):
    setup_trigger(cls)
    return cls
