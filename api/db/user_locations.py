# # pylint: disable=wrong-import-position
TABLE_NAME = "user_locations"
PKEY = "id"

from sqlalchemy import Column, ForeignKey, Table, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.schema import Index

from db import AsyncQueryMethodsMixin, Base, DictifiableMixin, audit_columns, generate_audit_trail, locations, users

user_locations = Table(
    TABLE_NAME,
    Base.metadata,
    Column(PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True),
    Column("user_id", ForeignKey(f"{users.TABLE_NAME}.{users.PKEY}"), nullable=False),
    Column("location_id", ForeignKey(f"{locations.TABLE_NAME}.{locations.PKEY}"), nullable=False),
    *audit_columns,
)


@generate_audit_trail
class UserLocations(Base, DictifiableMixin, AsyncQueryMethodsMixin):
    __table__ = user_locations
    __tablename__ = TABLE_NAME
    __table_args__ = (
        Index("ix_locations_user_id", user_locations.c.user_id, unique=False),
        Index("ix_locations_user_id_location_id", user_locations.c.user_id, user_locations.c.location_id, unique=True),
    )
