# pylint: disable=wrong-import-position
TABLE_NAME = "beers"
PKEY = "id"

from sqlalchemy import Boolean, Column, Float, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Index

from db import AsyncQueryMethodsMixin, AuditedMixin, Base, DictifiableMixin, generate_audit_trail
from db.types.nested import NestedMutableDict


@generate_audit_trail
class Beers(Base, DictifiableMixin, AuditedMixin, AsyncQueryMethodsMixin):

    __tablename__ = TABLE_NAME

    id = Column(PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    brewery = Column(String, nullable=True)
    external_brewing_tool = Column(String, nullable=True)
    external_brewing_tool_meta = Column(NestedMutableDict.as_mutable(JSONB), nullable=True)
    style = Column(String, nullable=True)
    abv = Column(Float, nullable=True)
    ibu = Column(Float, nullable=True)
    srm = Column(Float, nullable=True)
    img_url = Column(String, nullable=True)
    empty_img_url = Column(String, nullable=True)
    untappd_id = Column(String, nullable=True)
    image_transitions_enabled = Column(Boolean, nullable=False)

    batches = relationship("Batches", back_populates="beer")

    __table_args__ = (Index("beer_name_lower_ix", func.lower(name), unique=True),)

    @classmethod
    async def create(cls, session, **kwargs):  # pylint: disable=arguments-differ
        if not kwargs.get("image_transitions_enabled"):
            kwargs["image_transitions_enabled"] = False
        return await super().create(session, **kwargs)
