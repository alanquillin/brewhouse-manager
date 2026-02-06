# pylint: disable=wrong-import-position
TABLE_NAME = "beverages"
PKEY = "id"

from sqlalchemy import Boolean, Column, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.schema import Index

from db import AsyncQueryMethodsMixin, AuditedMixin, Base, DictifiableMixin, generate_audit_trail
from db.types.nested import NestedMutableDict


@generate_audit_trail
class Beverages(Base, DictifiableMixin, AuditedMixin, AsyncQueryMethodsMixin):

    __tablename__ = TABLE_NAME

    id = Column(PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
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

    batches = relationship("Batches", back_populates="beverage")

    __table_args__ = (Index("beverage_name_lower_ix", func.lower(name), unique=True),)

    @classmethod
    async def create(cls, session, **kwargs):  # pylint: disable=arguments-differ
        if not kwargs.get("image_transitions_enabled"):
            kwargs["image_transitions_enabled"] = False
        return await super().create(session, **kwargs)
