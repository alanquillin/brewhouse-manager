# pylint: disable=wrong-import-position
_TABLE_NAME = "fermentation_controller"
_PKEY = "id"

from sqlalchemy import Column, String, Integer, func, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.schema import Index

from db import AuditedMixin, Base, DictifiableMixin, QueryMethodsMixin, generate_audit_trail

@generate_audit_trail
class FermentationController(Base, DictifiableMixin, AuditedMixin, QueryMethodsMixin):

    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, UUID, server_default=func.uuid_generate_v4(), primary_key=True)
    manufacturer_id = Column(String, nullable=False)
    description = Column(String)
    manufacturer = Column(String, nullable=False)
    model = Column(String, nullable=False)
    target_temperature = Column(Float)
    calibration_differential = Column(Float)
    temperature_precision = Column(Float)
    cooling_differential = Column(Float) # This is value of allowed drift from the target temp before cooling is started
    heating_differential = Column(Float) # This is value of allowed drift from the target temp before heating is started
    program = Column(String)
    
    __table_args__ = (
        Index("ix_unique_manufacturer_manufacturer_id_model", manufacturer_id, manufacturer, model, unique=True),
    )