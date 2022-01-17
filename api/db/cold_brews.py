# pylint: disable=wrong-import-position
_TABLE_NAME = "cold_brews"
_PKEY = "id"

from psycopg2.errors import UniqueViolation  # pylint: disable=no-name-in-module
from sqlalchemy import Column, String, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.schema import Index

from db import (
    AuditedMixin,
    Base,
    DictifiableMixin,
    QueryMethodsMixin,
    generate_audit_trail,
    locations,
)
from db.types.nested import NestedMutableDict

@generate_audit_trail
class ColdBrews(Base, DictifiableMixin, AuditedMixin, QueryMethodsMixin):

    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    location_id = Column(UUID, ForeignKey(f"{locations._TABLE_NAME}.{locations._PKEY}"))

    __table_args__ = (Index("cold_brew_name_lower_ix", func.lower(name), unique=True),)
