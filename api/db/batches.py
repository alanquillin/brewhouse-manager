# pylint: disable=wrong-import-position
_TABLE_NAME = "batches"
_PKEY = "id"

from sqlalchemy import Column, ForeignKey, Float, String, func, Date, or_
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Index

from db import AuditedMixin, Base, DictifiableMixin, QueryMethodsMixin, beers, beverages, column_as_enum, generate_audit_trail
from db.types.nested import NestedMutableDict


@generate_audit_trail
class Batches(Base, DictifiableMixin, AuditedMixin, QueryMethodsMixin):

    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    name = Column(String, nullable=True)
    batch_number = Column(String, nullable=True)
    beer_id = Column(UUID, ForeignKey(f"{beers._TABLE_NAME}.{beers._PKEY}"), nullable=True)
    beverage_id = Column(UUID, ForeignKey(f"{beverages._TABLE_NAME}.{beers._PKEY}"), nullable=True)
    external_brewing_tool = Column(String, nullable=True)
    external_brewing_tool_meta = Column(NestedMutableDict.as_mutable(JSONB), nullable=True)
    abv = Column(Float, nullable=True)
    ibu = Column(Float, nullable=True)
    srm = Column(Float, nullable=True)
    img_url = Column(String, nullable=True)
    brew_date = Column(Date, nullable=True)
    keg_date = Column(Date, nullable=True)
    archived_on = Column(Date, nullable=True)

    beer = relationship(beers.Beers, backref=backref("Batches", cascade="all,delete"))
    beverage = relationship(beverages.Beverages, backref=backref("Batches", cascade="all,delete"))

    #overrides = relationship("BatchOverrides", back_populates="batch")

    __table_args__ = (
        Index("ix_batches_beer_id", beer_id, unique=False),
        Index("ix_batches_beverage_id", beverage_id, unique=False),
    )

    @classmethod
    def get_by_beer(cls, session, beer_id, **kwargs):
        return session.query(cls).filter_by(beer_id=beer_id, **kwargs)

    @classmethod
    def get_by_beverage(cls, session, beverage_id, **kwargs):
        return session.query(cls).filter_by(beverage_id=beverage_id, **kwargs)

    @classmethod
    def get_by_location(cls, session, location_id):
        return session.query(cls).filter(or_(Batches.beer.has(location_id=location_id), Batches.beverage.has(location_id=location_id)))