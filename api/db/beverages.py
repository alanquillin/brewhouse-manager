# pylint: disable=wrong-import-position
_TABLE_NAME = "beverages"
_PKEY = "id"

from psycopg2.errors import UniqueViolation  # pylint: disable=no-name-in-module
from sqlalchemy import Column, Date, Float, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.schema import Index

from db import AuditedMixin, Base, DictifiableMixin, QueryMethodsMixin, generate_audit_trail, locations
from db.types.nested import NestedMutableDict
from lib import UsefulEnum
from lib.exceptions import InvalidExternalBrewingTool


@generate_audit_trail
class Beverages(Base, DictifiableMixin, AuditedMixin, QueryMethodsMixin):

    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    brewery = Column(String, nullable=True)
    brewery_link = Column(String, nullable=True)
    type = Column(String, nullable=True)
    flavor = Column(String, nullable=True)
    img_url = Column(String, nullable=True)
    brew_date = Column(Date, nullable=True)
    keg_date = Column(Date, nullable=True)
    meta = Column(NestedMutableDict.as_mutable(JSONB), nullable=True)

    __table_args__ = (Index("beverage_name_lower_ix", func.lower(name), unique=True),)
