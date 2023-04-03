# pylint: disable=wrong-import-position
_TABLE_NAME = "taps"
_PKEY = "id"

from sqlalchemy import Column, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Index

from db import AuditedMixin, Base, DictifiableMixin, QueryMethodsMixin, beers, beverages, column_as_enum, generate_audit_trail, locations, sensors, on_tap


@generate_audit_trail
class Taps(Base, DictifiableMixin, AuditedMixin, QueryMethodsMixin):

    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    tap_number = Column(Integer, nullable=False)
    description = Column(String)
    location_id = Column(UUID, ForeignKey(f"{locations._TABLE_NAME}.{locations._PKEY}"), nullable=False)
    sensor_id = Column(UUID, ForeignKey(f"{sensors._TABLE_NAME}.{sensors._PKEY}"))
    on_tap_id = Column(UUID, ForeignKey(f"on_tap.id"))
    name_prefix = Column(String)
    name_suffix = Column(String)

    location = relationship(locations.Locations, backref=backref("Taps", cascade="all,delete"))
    sensor = relationship(sensors.Sensors)
    on_tap = relationship(on_tap.OnTap)

    __table_args__ = (
        Index("ix_taps_on_tap_id", on_tap_id, unique=False),
        Index("ix_taps_location_id", location_id, unique=False),
    )

    @classmethod
    def get_by_location(cls, session, location_id, **kwargs):
        return session.query(cls).filter_by(location_id=location_id, **kwargs)

    @classmethod
    def get_by_beer(cls, session, beer_id, **kwargs):
        return session.query(cls).join(on_tap.OnTap).filter_by(beer_id=beer_id, **kwargs)

    @classmethod
    def get_by_beverage(cls, session, beverage_id, **kwargs):
        return session.query(cls).join(on_tap.OnTap).filter_by(beverage_id=beverage_id, **kwargs)