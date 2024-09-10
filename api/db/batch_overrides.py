# pylint: disable=wrong-import-position
_TABLE_NAME = "batch_overrides"
_PKEY = "id"

from sqlalchemy import Column, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Index

from db import AuditedMixin, Base, DictifiableMixin, QueryMethodsMixin, batches, generate_audit_trail


@generate_audit_trail
class BatchOverrides(Base, DictifiableMixin, AuditedMixin, QueryMethodsMixin):

    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    batch_id = Column(UUID, ForeignKey(f"{batches._TABLE_NAME}.{batches._PKEY}"), nullable=True)
    key = Column(String, nullable=False)
    value = Column(String, nullable=False)

    batch = relationship(batches.Batches, backref=backref("BatchOverrides", cascade="all,delete"))

    __table_args__ = (
        Index("ix_batch_overrides_batch_id", batch_id, unique=False),
    )

    @classmethod
    def get_by_batch(cls, session, batch_id, **kwargs):
        return session.query(cls).filter_by(batch_id=batch_id, **kwargs)
