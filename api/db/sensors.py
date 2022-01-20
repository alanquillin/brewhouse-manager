# pylint: disable=wrong-import-position
_TABLE_NAME = "sensors"
_PKEY = "id"

from psycopg2.errors import UniqueViolation  # pylint: disable=no-name-in-module
from sqlalchemy import CheckConstraint, Column, String, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Index

from db import (
    AuditedMixin,
    Base,
    DictifiableMixin,
    QueryMethodsMixin,
    generate_audit_trail,
    locations
)
from db.types.nested import NestedMutableDict

@generate_audit_trail
class Sensors(Base, DictifiableMixin, AuditedMixin, QueryMethodsMixin):

    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    name = Column(String, nullable=False)
    location_id = Column(UUID, ForeignKey(f"{locations._TABLE_NAME}.{locations._PKEY}"), nullable=False)
    sensor_type = Column("sensor_type", String, nullable=False)
    meta = Column(NestedMutableDict.as_mutable(JSONB), nullable=True)

    location = relationship(locations.Locations, backref=backref("Sensors", cascade="all,delete"))

    __table_args__ = (
        Index("ix_sensor_location_id", location_id, unique=False),
    )
        
    @classmethod
    def get_by_location(cls, session, location_id, **kwargs):
        return session.query(cls).filter_by(location_id=location_id, **kwargs)