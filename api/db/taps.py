# pylint: disable=wrong-import-position
_TABLE_NAME = "taps"
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
    locations,
    column_as_enum,
    beers,
    cold_brews,
    sensors,
)

from lib.exceptions import InvalidTapType
from lib import UsefulEnum

class TapType(UsefulEnum):
    COLD_BREW = "cold-brew"
    BEER = "beer"

    @classmethod
    def _missing_(cls, value):
        raise InvalidTapType(value)

@generate_audit_trail
@column_as_enum("_tap_type", "tap_type", TapType, custom_exc=InvalidTapType)
class Taps(Base, DictifiableMixin, AuditedMixin, QueryMethodsMixin):

    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    tap_number = Column(Integer, nullable=False)
    description = Column(String)
    location_id = Column(UUID, ForeignKey(f"{locations._TABLE_NAME}.{locations._PKEY}"), nullable=False)
    _tap_type = Column("tap_type", String, nullable=False)
    beer_id = Column(UUID, ForeignKey(f"{beers._TABLE_NAME}.{beers._PKEY}"))
    cold_brew_id = Column(UUID, ForeignKey(f"{cold_brews._TABLE_NAME}.{cold_brews._PKEY}"))
    sensor_id = Column(UUID, ForeignKey(f"{sensors._TABLE_NAME}.{sensors._PKEY}"))

    location = relationship(locations.Locations)
    beer = relationship(beers.Beers)
    cold_brew = relationship(cold_brews.ColdBrews)
    sensor = relationship(sensors.Sensors)

    __table_args__ = (
        Index("ix_taps_beer_id", beer_id, unique=False),
        Index("ix_taps_cold_brew_id", cold_brew_id, unique=False),
        Index("ix_taps_location_id", location_id, unique=False),
    )

    @classmethod
    def get_by_location(cls, session, location_id, **kwargs):
        return session.query(cls).filter_by(location_id=location_id, **kwargs)
