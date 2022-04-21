# pylint: disable=wrong-import-position
_TABLE_NAME = "fermentation_controller_stats"
_PKEY = "id"

from sqlalchemy import Column, String, Integer, Float, func, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import backref, relationship
from sqlalchemy.schema import Index

from db import (
    Base,
    DictifiableMixin,
    QueryMethodsMixin,
    fermentation_ctrl
)


class FermentationControllerStats(Base, DictifiableMixin, QueryMethodsMixin):

    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    fermentation_controller_id = Column(UUID, ForeignKey(f"{fermentation_ctrl._TABLE_NAME}.{fermentation_ctrl._PKEY}"), nullable=False)
    event_time = Column(DateTime(timezone=True), nullable=False)
    temperature = Column(Float, nullable=False)

    fermentation_controller = relationship(fermentation_ctrl.FermentationController, backref=backref("FermentationControllerStats", cascade="all,delete"))

    __table_args__ = (Index("ix_fermentation_controller_stats_parent_id", fermentation_controller_id, unique=False),)

    @classmethod
    def get_by_fermentation_controller_id(cls, session, fermentation_controller_id, **kwargs):
        return session.query(cls).filter_by(fermentation_controller_id=fermentation_controller_id, **kwargs)