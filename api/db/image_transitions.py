# pylint: disable=wrong-import-position
_TABLE_NAME = "image_transitions"
_PKEY = "id"

import re

from psycopg2.errors import UniqueViolation  # pylint: disable=no-name-in-module
from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Index

from db import AuditedMixin, Base, DictifiableMixin, AsyncQueryMethodsMixin, generate_audit_trail, beers, beverages
from db.types.nested import NestedMutableDict


@generate_audit_trail
class ImageTransitions(Base, DictifiableMixin, AuditedMixin, AsyncQueryMethodsMixin):
    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    beer_id = Column(UUID, ForeignKey(f"{beers._TABLE_NAME}.{beers._PKEY}"), nullable=True)
    beverage_id = Column(UUID, ForeignKey(f"{beverages._TABLE_NAME}.{beverages._PKEY}"), nullable=True)
    img_url = Column(String, nullable=False)
    change_percent = Column(Integer, nullable=True)
    beer = relationship(beers.Beers, backref=backref("Beers", cascade="all,delete"))
    beverage = relationship(beverages.Beverages, backref=backref("Beverages", cascade="all,delete"))


    __table_args__ = (Index("ix_image_transition_beer_id", beer_id, unique=False),Index("ix_image_transition_beverage_id", beverage_id, unique=False))
