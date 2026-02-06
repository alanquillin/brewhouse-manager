# pylint: disable=wrong-import-position
TABLE_NAME = "users"
PKEY = "id"

from argon2 import PasswordHasher
from sqlalchemy import Boolean, Column, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import joinedload, relationship
from sqlalchemy.schema import Index

from db import AsyncQueryMethodsMixin, AuditedMixin, Base, DictifiableMixin, generate_audit_trail, locations, user_locations


@generate_audit_trail
class Users(Base, DictifiableMixin, AuditedMixin, AsyncQueryMethodsMixin):

    __tablename__ = TABLE_NAME

    id = Column(PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    email = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    profile_pic = Column(String, nullable=True)
    google_oidc_id = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)
    admin = Column(Boolean, nullable=False, default=False)
    api_key = Column(String, nullable=True)

    locations = relationship(locations.Locations, secondary=user_locations.user_locations)

    __table_args__ = (
        Index("ix_user_email", email, unique=True),
        Index("ix_user_google_oidc_id", google_oidc_id, unique=True),
        Index("ix_user_api_key", api_key, unique=True),
    )

    @classmethod
    async def query(cls, session, **kwargs):  # pylint: disable=arguments-differ
        def q_fn(q):
            return q.options(joinedload(Users.locations))

        res = await super().query(session, q_fn=q_fn, **kwargs)
        return res

    @classmethod
    async def get_by_email(cls, session, email, **kwargs):
        res = await super().query(session, email=email, **kwargs)
        if not res:
            return None
        return res[0]

    @classmethod
    async def get_by_api_key(cls, session, api_key, **kwargs):
        res = await super().query(session, api_key=api_key, **kwargs)
        if not res:
            return None
        return res[0]

    @classmethod
    async def update(cls, session, pkey, password=None, **kwargs): # pylint: disable=arguments-renamed
        if password and not kwargs.get("password_hash"):
            ph = PasswordHasher()
            kwargs["password_hash"] = ph.hash(password)
        return await super().update(session, pkey, **kwargs)

    @classmethod
    async def create(cls, session, password=None, **kwargs): # pylint: disable=arguments-renamed
        if password and not kwargs.get("password_hash"):
            ph = PasswordHasher()
            kwargs["password_hash"] = ph.hash(password)
        return await super().create(session, **kwargs)

    @classmethod
    async def disable_password(cls, session, pkey):
        return await super().update(session, pkey, password_hash=None)
