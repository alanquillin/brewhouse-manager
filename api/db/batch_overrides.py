# pylint: disable=wrong-import-position
TABLE_NAME = "batch_overrides"
PKEY = "id"

from sqlalchemy import Column, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Index

from db import AsyncQueryMethodsMixin, AuditedMixin, Base, DictifiableMixin, batches, generate_audit_trail


@generate_audit_trail
class BatchOverrides(Base, DictifiableMixin, AuditedMixin, AsyncQueryMethodsMixin):

    __tablename__ = TABLE_NAME

    id = Column(PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    batch_id = Column(UUID, ForeignKey(f"{batches.TABLE_NAME}.{batches.PKEY}"), nullable=True)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)

    batch = relationship(batches.Batches, backref=backref("BatchOverrides", cascade="all,delete"))

    __table_args__ = (Index("ix_batch_overrides_batch_id", batch_id, unique=False),)
