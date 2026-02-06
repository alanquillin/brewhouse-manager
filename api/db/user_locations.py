# # pylint: disable=wrong-import-position
_TABLE_NAME = "user_locations"
_PKEY = "id"

from argon2 import PasswordHasher
from sqlalchemy import Column, ForeignKey, Table, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.schema import Index

from db import AsyncQueryMethodsMixin, Base, DictifiableMixin, audit_columns, generate_audit_trail, locations, users

user_locations = Table(
    _TABLE_NAME,
    Base.metadata,
    Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True),
    Column("user_id", ForeignKey(f"{users._TABLE_NAME}.{users._PKEY}"), nullable=False),
    Column("location_id", ForeignKey(f"{locations._TABLE_NAME}.{locations._PKEY}"), nullable=False),
    *audit_columns,
)


@generate_audit_trail
class UserLocations(Base, DictifiableMixin, AsyncQueryMethodsMixin):
    __table__ = user_locations
    __tablename__ = _TABLE_NAME
    __table_args__ = (
        Index("ix_locations_user_id", user_locations.c.user_id, unique=False),
        Index("ix_locations_user_id_location_id", user_locations.c.user_id, user_locations.c.location_id, unique=True),
    )
