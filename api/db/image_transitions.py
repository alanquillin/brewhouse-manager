# pylint: disable=wrong-import-position
TABLE_NAME = "image_transitions"
PKEY = "id"

from sqlalchemy import Column, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Index

from db import AsyncQueryMethodsMixin, AuditedMixin, Base, DictifiableMixin, beers, beverages, generate_audit_trail


@generate_audit_trail
class ImageTransitions(Base, DictifiableMixin, AuditedMixin, AsyncQueryMethodsMixin):
    __tablename__ = TABLE_NAME

    id = Column(PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    beer_id = Column(UUID, ForeignKey(f"{beers.TABLE_NAME}.{beers.PKEY}"), nullable=True)
    beverage_id = Column(UUID, ForeignKey(f"{beverages.TABLE_NAME}.{beverages.PKEY}"), nullable=True)
    img_url = Column(String, nullable=False)
    change_percent = Column(Integer, nullable=True)
    beer = relationship(beers.Beers, backref=backref("Beers", cascade="all,delete"))
    beverage = relationship(beverages.Beverages, backref=backref("Beverages", cascade="all,delete"))

    __table_args__ = (Index("ix_image_transition_beer_id", beer_id, unique=False), Index("ix_image_transition_beverage_id", beverage_id, unique=False))
