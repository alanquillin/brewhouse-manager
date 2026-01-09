# # pylint: disable=wrong-import-position
_TABLE_NAME = "batch_locations"
_PKEY = "id"

from sqlalchemy import Column, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Index

from db import audit_columns, Base, DictifiableMixin, QueryMethodsMixin, generate_audit_trail, batches, locations, AuditedMixin

@generate_audit_trail
class BatchLocations(Base, DictifiableMixin, AuditedMixin, QueryMethodsMixin):
    __tablename__ = _TABLE_NAME
    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    batch_id = Column(UUID, ForeignKey(f"{batches._TABLE_NAME}.{batches._PKEY}"), nullable=False)
    location_id = Column(UUID, ForeignKey(f"{locations._TABLE_NAME}.{locations._PKEY}"), nullable=False)

    batch = relationship("Batches", backref=backref("BatchLocations", cascade="all,delete"))
    location = relationship(locations.Locations, backref=backref("BatchLocations", cascade="all,delete"))

    __table_args__ = (
        Index("ix_locations_batch_id", batch_id, unique=False), 
        Index("ix_locations_batch_id_location_id", batch_id, location_id, unique=True)
    )

    @classmethod
    def get_by_batch_id(cls, session, batch_id, **kwargs):
        res = cls.query(session, batch_id=batch_id, **kwargs)
        if not res:
            return None

        return res[0]