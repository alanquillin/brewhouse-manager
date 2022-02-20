# pylint: disable=wrong-import-position
_TABLE_NAME = "users"
_PKEY = "id"

from argon2 import PasswordHasher
from psycopg2.errors import UniqueViolation  # pylint: disable=no-name-in-module
from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Index

from db import AuditedMixin, Base, DictifiableMixin, QueryMethodsMixin, generate_audit_trail


@generate_audit_trail
class Users(Base, DictifiableMixin, AuditedMixin, QueryMethodsMixin):

    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    email = Column(String, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    profile_pic = Column(String, nullable=True)
    google_oidc_id = Column(String, nullable=True)
    password_hash = Column(String, nullable=True)

    __table_args__ = (Index("ix_user_email", email, unique=True), Index("ix_user_google_oidc_id", google_oidc_id, unique=True))

    @classmethod
    def get_by_email(cls, session, email, **kwargs):
        res = cls.query(session, email=email, **kwargs)
        if not res:
            return None

        return res[0]

    @classmethod
    def update(cls, session, pkey, password=None, **kwargs):  # pylint: disable=arguments-differ
        if password and not kwargs.get("password_hash"):
            ph = PasswordHasher()
            kwargs["password_hash"] = ph.hash(password)
        return super().update(session, pkey, **kwargs)

    @classmethod
    def create(cls, session, password=None, **kwargs):
        if password and not kwargs.get("password_hash"):
            ph = PasswordHasher()
            kwargs["password_hash"] = ph.hash(password)
        return super().create(session, **kwargs)

    @classmethod
    def disable_password(cls, session, pkey):
        return super().update(session, pkey, password_hash=None)
