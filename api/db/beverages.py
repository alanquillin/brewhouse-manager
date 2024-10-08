# pylint: disable=wrong-import-position
_TABLE_NAME = "beverages"
_PKEY = "id"

from sqlalchemy import Column, Date, ForeignKey, Boolean, String, func
from sqlalchemy.orm import backref, relationship
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.schema import Index

from db import AuditedMixin, Base, DictifiableMixin, QueryMethodsMixin, generate_audit_trail, locations
from db.types.nested import NestedMutableDict
from lib import UsefulEnum
from lib.exceptions import InvalidExternalBrewingTool


@generate_audit_trail
class Beverages(Base, DictifiableMixin, AuditedMixin, QueryMethodsMixin):

    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    brewery = Column(String, nullable=True)
    brewery_link = Column(String, nullable=True)
    type = Column(String, nullable=True)
    flavor = Column(String, nullable=True)
    img_url = Column(String, nullable=True)
    empty_img_url = Column(String, nullable=True)
    meta = Column(NestedMutableDict.as_mutable(JSONB), nullable=True)
    image_transitions_enabled = Column(Boolean, nullable=False)
    location_id = Column(UUID, ForeignKey(f"{locations._TABLE_NAME}.{locations._PKEY}"), nullable=False)

    location = relationship(locations.Locations, backref=backref("Beverages", cascade="all,delete"))

    batches = relationship("Batches", back_populates="beverage")

    __table_args__ = (Index("beverage_name_lower_ix", func.lower(name), unique=True),)

    @classmethod
    def create(cls, session, **kwargs):
        if not kwargs.get("image_transitions_enabled"):
            kwargs["image_transitions_enabled"] = False
        return super().create(session, **kwargs)
