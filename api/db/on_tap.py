# pylint: disable=wrong-import-position
TABLE_NAME = "on_tap"
PKEY = "id"

from sqlalchemy import Column, Date, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Index

from db import AsyncQueryMethodsMixin, AuditedMixin, Base, DictifiableMixin, batches, generate_audit_trail


@generate_audit_trail
class OnTap(Base, DictifiableMixin, AuditedMixin, AsyncQueryMethodsMixin):

    __tablename__ = TABLE_NAME

    id = Column(PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    batch_id = Column(UUID, ForeignKey(f"{batches.TABLE_NAME}.{batches.PKEY}"), nullable=True)
    tapped_on = Column(Date, nullable=True)
    untapped_on = Column(Date, nullable=True)

    batch = relationship(batches.Batches, backref=backref("OnTap", cascade="all,delete"))

    __table_args__ = (Index("ix_on_tap_batch_id", batch_id, unique=False),)
