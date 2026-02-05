"""Sensor service with business logic and transformations"""

from sqlalchemy.ext.asyncio import AsyncSession
from typing import Union

from lib import logging
from lib.tap_monitors.plaato_keg import service_handler
from services.base import transform_dict_to_camel_case

LOGGER = logging.getLogger(__name__)

def to_int(val: Union[str, int]) -> int:
    if isinstance(val, int):
        return val
    val = clean_str(val)
    if not val:
        return None
    return int(val)

def to_float(val: Union[str, float]) -> float:
    if isinstance(val, float):
        return val
    val = clean_str(val)
    if not val:
        return None
    return float(val)

def to_bool(val: Union[str, bool]) -> bool:
    if isinstance(val, bool):
        return val
    val = clean_str(val)
    if not val:
        return None
    val = val.lower()
    return val == "true" or val == "1"

def clean_str(val: str) -> str:
    if not val:
        return None
    val = val.strip()
    if val == "":
        return None
    return val

CONVERSIONS = {
    "percent_of_beer_left": to_float,
    "is_pouring": to_bool,
    "amount_left": to_float,
    "temperature_offset": to_float,
    "keg_temperature": to_float,
    "last_pour": to_float,
    "empty_keg_weight": to_float,
    "og": to_float,
    "fg": to_float,
    "max_keg_volume": to_float,
    "wifi_signal_strength": to_int,
    "leak_detection": to_bool,
    "min_temperature": to_float,
    "max_temperature": to_float,
    "unit": to_int,
    "measure_unit": to_int,
    "calculated_abv": to_float
}

class PlaatoKegService:
    
    @staticmethod
    async def transform_response(plaato_keg, db_session: AsyncSession, **kwargs):
        if not plaato_keg:
            return None

        data = plaato_keg.to_dict()

        for key, val in data.items():
            fn = CONVERSIONS.get(key)
            if fn:
                data[key] = fn(val)
            else:
                if isinstance(val, str):
                    data[key] = clean_str(val)

        if plaato_keg.last_updated_on:
            if not data.get("og") and not data.get("fg"):
                data["mode"] = "co2"
            else:
                data["mode"] = "beer"

            unit = data.get("unit")
            measure_unit = data.get("measure_unit")
        

            if unit == 1 and measure_unit == 1:
                data["unitMode"] = "weight"
                data["unitType"] = "metric"
            elif unit == 2 and measure_unit == 2:
                data["unitMode"] = "volume"
                data["unitType"] = "us"
            elif unit == 1 and measure_unit == 2:
                data["unitMode"] = "volume"
                data["unitType"] = "metric"
            elif unit == 2 and measure_unit == 1:
                data["unitMode"] = "weight"
                data["unitType"] = "us"
            else:
                data["unitMode"] = None
                data["unitType"] = None

            data["connected"] = data["id"] in service_handler.connection_handler.get_registered_device_ids()

        return transform_dict_to_camel_case(data)