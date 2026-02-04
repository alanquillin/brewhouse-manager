# pylint: disable=wrong-import-position
_TABLE_NAME = "plaato_data"
_PKEY = "id"

from sqlalchemy import Column, String, Date
from sqlalchemy.orm import backref, relationship

from db import AuditedMixin, Base, DictifiableMixin, AsyncQueryMethodsMixin, generate_audit_trail


@generate_audit_trail
class PlaatoData(Base, DictifiableMixin, AuditedMixin, AsyncQueryMethodsMixin):

    __tablename__ = _TABLE_NAME

    id = Column(_PKEY, String, primary_key=True)
    name = Column(String, nullable=True)
    last_pour_string = Column(String, nullable=True)
    percent_of_beer_left = Column(String, nullable=True)
    is_pouring = Column(String, nullable=True)
    amount_left = Column(String, nullable=True)
    temperature_offset = Column(String, nullable=True)
    keg_temperature = Column(String, nullable=True)
    last_pour = Column(String, nullable=True)
    tare = Column(String, nullable=True)
    known_weight_calibrate = Column(String, nullable=True)
    empty_keg_weight = Column(String, nullable=True)
    beer_style = Column(String, nullable=True)
    og = Column(String, nullable=True)
    fg = Column(String, nullable=True)
    date = Column(String, nullable=True)
    calculated_abv = Column(String, nullable=True)
    keg_temperature_string = Column(String, nullable=True)
    calculated_alcohol_string = Column(String, nullable=True)
    unit = Column(String, nullable=True)
    calculate = Column(String, nullable=True)
    beer_left_unit = Column(String, nullable=True)
    measure_unit = Column(String, nullable=True)
    max_keg_volume = Column(String, nullable=True)
    temperature_unit = Column(String, nullable=True)
    wifi_signal_strength = Column(String, nullable=True)
    volume_unit = Column(String, nullable=True)
    leak_detection = Column(String, nullable=True)
    min_temperature = Column(String, nullable=True)
    max_temperature = Column(String, nullable=True)
    keg_mode_c02_beer = Column(String, nullable=True)
    sensitivity = Column(String, nullable=True)
    chip_temperature_string = Column(String, nullable=True)
    firmware_version = Column(String, nullable=True)
    max_keg_volume = Column(String, nullable=True)
    last_updated_on = Column(Date, nullable=True)