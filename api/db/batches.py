# pylint: disable=wrong-import-position
TABLE_NAME = "batches"
PKEY = "id"

from sqlalchemy import Column, Date, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Index

from db import AsyncQueryMethodsMixin, AuditedMixin, Base, DictifiableMixin, batch_locations, beers, beverages, generate_audit_trail, locations
from db.types.nested import NestedMutableDict


@generate_audit_trail
class Batches(Base, DictifiableMixin, AuditedMixin, AsyncQueryMethodsMixin):

    __tablename__ = TABLE_NAME

    id = Column(PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    name = Column(String, nullable=True)
    batch_number = Column(String, nullable=True)
    beer_id = Column(UUID, ForeignKey(f"{beers.TABLE_NAME}.{beers.PKEY}"), nullable=True)
    beverage_id = Column(UUID, ForeignKey(f"{beverages.TABLE_NAME}.{beverages.PKEY}"), nullable=True)
    external_brewing_tool = Column(String, nullable=True)
    external_brewing_tool_meta = Column(NestedMutableDict.as_mutable(JSONB), nullable=True)
    abv = Column(Float, nullable=True)
    ibu = Column(Float, nullable=True)
    srm = Column(Float, nullable=True)
    img_url = Column(String, nullable=True)
    brew_date = Column(Date, nullable=True)
    keg_date = Column(Date, nullable=True)
    archived_on = Column(Date, nullable=True)

    locations = relationship(locations.Locations, secondary=batch_locations.BatchLocations.__table__)
    beer = relationship(beers.Beers, backref=backref("Batches", cascade="all,delete"))
    beverage = relationship(beverages.Beverages, backref=backref("Batches", cascade="all,delete"))

    # overrides = relationship("BatchOverrides", back_populates="batch")

    __table_args__ = (
        Index("ix_batches_beer_id", beer_id, unique=False),
        Index("ix_batches_beverage_id", beverage_id, unique=False),
    )
