# # pylint: disable=wrong-import-position
TABLE_NAME = "batch_locations"
PKEY = "id"

from sqlalchemy import Column, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Index

from db import AsyncQueryMethodsMixin, AuditedMixin, Base, DictifiableMixin, batches, generate_audit_trail, locations


@generate_audit_trail
class BatchLocations(Base, DictifiableMixin, AuditedMixin, AsyncQueryMethodsMixin):
    __tablename__ = TABLE_NAME
    id = Column(PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    batch_id = Column(UUID, ForeignKey(f"{batches.TABLE_NAME}.{batches.PKEY}"), nullable=False)
    location_id = Column(UUID, ForeignKey(f"{locations.TABLE_NAME}.{locations.PKEY}"), nullable=False)

    batch = relationship("Batches", backref=backref("BatchLocations", cascade="all,delete"))
    location = relationship(locations.Locations, backref=backref("BatchLocations", cascade="all,delete"))

    __table_args__ = (Index("ix_locations_batch_id", batch_id, unique=False), Index("ix_locations_batch_id_location_id", batch_id, location_id, unique=True))
