# pylint: disable=wrong-import-position
_TABLE_NAME = "locations"
_PKEY = "id"

import re

from psycopg2.errors import UniqueViolation  # pylint: disable=no-name-in-module
from sqlalchemy import Column, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.schema import Index

from db import AsyncQueryMethodsMixin, AuditedMixin, Base, DictifiableMixin, generate_audit_trail


@generate_audit_trail
class Locations(Base, DictifiableMixin, AuditedMixin, AsyncQueryMethodsMixin):
    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    __table_args__ = (Index("locations_name_lower_ix", func.lower(name), unique=True),)

    @staticmethod
    def _replace_name(data):
        if "name" in data and data.get("name"):
            data["name"] = re.sub("[^a-zA-Z0-9-]", "", data["name"].replace(" ", "-")).lower()
        return data

    @classmethod
    async def create(cls, session, **kwargs):
        kwargs = cls._replace_name(kwargs)
        return await super().create(session, **kwargs)

    @classmethod
    async def update(cls, session, pkey, **kwargs):
        kwargs = cls._replace_name(kwargs)
        return await super().update(session, pkey, **kwargs)
