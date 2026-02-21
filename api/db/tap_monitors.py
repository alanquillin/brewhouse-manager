# pylint: disable=wrong-import-position
TABLE_NAME = "tap_monitors"
PKEY = "id"

from sqlalchemy import Column, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Index

from db import AsyncQueryMethodsMixin, AuditedMixin, Base, DictifiableMixin, generate_audit_trail, locations
from db.types.nested import NestedMutableDict


@generate_audit_trail
class TapMonitors(Base, DictifiableMixin, AuditedMixin, AsyncQueryMethodsMixin):

    __tablename__ = TABLE_NAME

    id = Column(PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    name = Column(String, nullable=False)
    location_id = Column(UUID, ForeignKey(f"{locations.TABLE_NAME}.{locations.PKEY}"), nullable=False)
    monitor_type = Column("monitor_type", String, nullable=False)
    meta = Column(NestedMutableDict.as_mutable(JSONB), nullable=True)

    location = relationship(locations.Locations, backref=backref("TapMonitors", cascade="all,delete"))

    __table_args__ = (Index("ix_tap_monitor_location_id", location_id, unique=False),)
