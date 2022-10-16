# pylint: disable=wrong-import-position
_TABLE_NAME = "beers"
_PKEY = "id"

from psycopg2.errors import UniqueViolation  # pylint: disable=no-name-in-module
from sqlalchemy import Column, Date, Float, ForeignKey, Boolean, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.schema import Index

from db import AuditedMixin, Base, DictifiableMixin, QueryMethodsMixin, generate_audit_trail, locations
from db.types.nested import NestedMutableDict
from lib import UsefulEnum
from lib.exceptions import InvalidExternalBrewingTool


@generate_audit_trail
class Beers(Base, DictifiableMixin, AuditedMixin, QueryMethodsMixin):

    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    name = Column(String, nullable=True)
    description = Column(String, nullable=True)
    brewery = Column(String, nullable=True)
    external_brewing_tool = Column(String, nullable=True)
    external_brewing_tool_meta = Column(NestedMutableDict.as_mutable(JSONB), nullable=True)
    style = Column(String, nullable=True)
    abv = Column(Float, nullable=True)
    ibu = Column(Float, nullable=True)
    srm = Column(Float, nullable=True)
    img_url = Column(String, nullable=True)
    empty_img_url = Column(String, nullable=True)
    untappd_id = Column(String, nullable=True)
    brew_date = Column(Date, nullable=True)
    keg_date = Column(Date, nullable=True)
    image_transitions_enabled = Column(Boolean, nullable=False)

    __table_args__ = (Index("beer_name_lower_ix", func.lower(name), unique=True),)

    @classmethod
    def create(cls, session, **kwargs):
        if not kwargs.get("image_transitions_enabled"):
            kwargs["image_transitions_enabled"] = False
        return super().create(session, **kwargs)
