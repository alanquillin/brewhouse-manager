# pylint: disable=wrong-import-position
TABLE_NAME = "taps"
PKEY = "id"

from sqlalchemy import Column, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Index

from db import (
    AsyncQueryMethodsMixin,
    AuditedMixin,
    Base,
    DictifiableMixin,
    generate_audit_trail,
    locations,
    on_tap,
    tap_monitors,
)


@generate_audit_trail
class Taps(Base, DictifiableMixin, AuditedMixin, AsyncQueryMethodsMixin):

    __tablename__ = TABLE_NAME

    id = Column(PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    tap_number = Column(Integer, nullable=False)
    description = Column(String)
    location_id = Column(UUID, ForeignKey(f"{locations.TABLE_NAME}.{locations.PKEY}"), nullable=False)
    tap_monitor_id = Column(UUID, ForeignKey(f"{tap_monitors.TABLE_NAME}.{tap_monitors.PKEY}"))
    on_tap_id = Column(UUID, ForeignKey("on_tap.id"))
    name_prefix = Column(String)
    name_suffix = Column(String)

    location = relationship(locations.Locations, backref=backref("Taps", cascade="all,delete"))
    tap_monitor = relationship(tap_monitors.TapMonitors)
    on_tap = relationship(on_tap.OnTap)

    __table_args__ = (
        Index("ix_taps_on_tap_id", on_tap_id, unique=False),
        Index("ix_taps_location_id", location_id, unique=False),
    )

    @classmethod
    async def get_by_location(cls, session, location_id, **kwargs):
        def _q_fn(q):
            return q.filter_by(location_id=location_id, **kwargs)

        return await super().query(session, q_fn=_q_fn)

    @classmethod
    async def get_by_batch(cls, session, batch_id, **kwargs):
        def _q_fn(q):
            return q.join(on_tap.OnTap).filter_by(batch_id=batch_id, **kwargs)

        return await super().query(session, q_fn=_q_fn)
