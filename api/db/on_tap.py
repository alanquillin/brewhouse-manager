# pylint: disable=wrong-import-position
_TABLE_NAME = "on_tap"
_PKEY = "id"

from sqlalchemy import Column, Date, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Index

from db import AsyncQueryMethodsMixin, AuditedMixin, Base, DictifiableMixin, batches, column_as_enum, generate_audit_trail


@generate_audit_trail
class OnTap(Base, DictifiableMixin, AuditedMixin, AsyncQueryMethodsMixin):

    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    batch_id = Column(UUID, ForeignKey(f"{batches._TABLE_NAME}.{batches._PKEY}"), nullable=True)
    tapped_on = Column(Date, nullable=True)
    untapped_on = Column(Date, nullable=True)

    batch = relationship(batches.Batches, backref=backref("OnTap", cascade="all,delete"))

    __table_args__ = (Index("ix_on_tap_batch_id", batch_id, unique=False),)
