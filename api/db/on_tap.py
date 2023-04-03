# pylint: disable=wrong-import-position
_TABLE_NAME = "on_tap"
_PKEY = "id"

from sqlalchemy import Column, ForeignKey, Integer, String, func, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Index

from db import AuditedMixin, Base, DictifiableMixin, QueryMethodsMixin, beers, beverages, column_as_enum, generate_audit_trail


@generate_audit_trail
class OnTap(Base, DictifiableMixin, AuditedMixin, QueryMethodsMixin):

    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    beer_id = Column(UUID, ForeignKey(f"{beers._TABLE_NAME}.{beers._PKEY}"), nullable=True)
    beverage_id = Column(UUID, ForeignKey(f"{beverages._TABLE_NAME}.{beers._PKEY}"), nullable=True)
    tapped_on = Column(Date, nullable=True)
    untapped_on = Column(Date, nullable=True)

    beer = relationship(beers.Beers, backref=backref("OnTap", cascade="all,delete"))
    beverage = relationship(beverages.Beverages, backref=backref("OnTap", cascade="all,delete"))

    __table_args__ = (
        Index("ix_on_tap_beer_id", beer_id, unique=False),
        Index("ix_on_tap_beverage_id", beverage_id, unique=False),
    )

    @classmethod
    def get_by_beer(cls, session, beer_id, **kwargs):
        return session.query(cls).filter_by(beer_id=beer_id, **kwargs)

    @classmethod
    def get_by_beverage(cls, session, beverage_id, **kwargs):
        return session.query(cls).filter_by(beverage_id=beverage_id, **kwargs)
