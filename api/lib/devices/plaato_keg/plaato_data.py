from typing import Dict, Tuple, Optional, Any, List

from lib import logging
from lib.devices.plaato_keg.blynk_protocol import BlynkCommand
from lib.devices.plaato_keg.plaato_protocol import PlaatoMessage, PlaatoPin

LOGGER = logging.getLogger(__name__)

USER_OVERRIDEABLE: Dict[str, str] = {
    str(PlaatoPin.UNIT): "user_unit",
    str(PlaatoPin.MEASURE_UNIT): "user_measure_unit",
    str(PlaatoPin.MODE): "user_keg_mode_c02_beer"
}
    
PLAATO_DATA_MAP: Dict[Tuple[str, str, str], str] = {
    ("hardware", "vw", str(PlaatoPin.LAST_POUR_STR)): "last_pour_string",
    ("hardware", "vw", str(PlaatoPin.PERCENT_BEER_LEFT)): "percent_of_beer_left",
    ("hardware", "vw", str(PlaatoPin.IS_POURING)): "is_pouring",
    ("hardware", "vw", str(PlaatoPin.AMOUNT_LEFT)): "amount_left",
    ("hardware", "vw", str(PlaatoPin.TEMPERATURE_OFFSET)): "temperature_offset",
    ("hardware", "vw", str(PlaatoPin.TEMPERATURE)): "keg_temperature",
    ("hardware", "vw", str(PlaatoPin.LAST_POUR)): "last_pour",
    ("hardware", "vw", str(PlaatoPin.TARE)): "tare",
    ("hardware", "vw", str(PlaatoPin.CALIBRATE)): "known_weight_calibrate",
    ("hardware", "vw", str(PlaatoPin.EMPTY_KEG_WEIGHT)): "empty_keg_weight",
    ("hardware", "vw", str(PlaatoPin.BEER_STYLE)): "beer_style",
    ("hardware", "vw", str(PlaatoPin.OG)): "og",
    ("hardware", "vw", str(PlaatoPin.FG)): "fg",
    ("hardware", "vw", str(PlaatoPin.DATE)): "date",
    ("hardware", "vw", str(PlaatoPin.ABV)): "calculated_abv",
    ("hardware", "vw", str(PlaatoPin.TEMPERATURE_STR)): "keg_temperature_string",
    ("hardware", "vw", str(PlaatoPin.CALCULATED_ABV_STR)): "calculated_alcohol_string",
    ("hardware", "vw", str(PlaatoPin.UNIT)): "unit",
    ("hardware", "vw", str(PlaatoPin.CALCULATE)): "calculate",
    ("hardware", "vw", str(PlaatoPin.BEER_LEFT_UNIT)): "beer_left_unit",
    ("hardware", "vw", str(PlaatoPin.MEASURE_UNIT)): "measure_unit",
    ("hardware", "vw", str(PlaatoPin.MAX_KEG_VOLUME)): "max_keg_volume",
    ("hardware", "vw", str(PlaatoPin.TEMP_UNIT)): "temperature_unit",
    ("hardware", "vw", str(PlaatoPin.WIFI_SIGNAL_STRENGTH)): "wifi_signal_strength",
    ("hardware", "vw", str(PlaatoPin.VOLUME_UNIT)): "volume_unit",
    ("hardware", "vw", str(PlaatoPin.LEAK_DETECTION)): "leak_detection",
    ("hardware", "vw", str(PlaatoPin.MIN_TEMP)): "min_temperature",
    ("hardware", "vw", str(PlaatoPin.MAX_TEMP)): "max_temperature",
    ("hardware", "vw", str(PlaatoPin.MODE)): "keg_mode_c02_beer",
    ("hardware", "vw", str(PlaatoPin.SENSITIVITY)): "sensitivity",
    ("hardware", "vw", str(PlaatoPin.CHIP_TEMPERATURE_STR)): "chip_temperature_string",
    ("hardware", "vw", str(PlaatoPin.FIRMWARE_VERSION)): "firmware_version",
    ("property", "51", "max"): "max_keg_volume",
}
    
def decode_list(msgs: List[PlaatoMessage]) -> List[Tuple[str, Any]]:
    """Decode a list of commands"""
    decoded = []
    for cmd in msgs:
        result = decode(cmd)
        if result is not None:
            decoded.append(result)
    return decoded

def decode(msg: PlaatoMessage) -> Optional[Tuple[str, Any]]:
    """Decode a single Plaato data message"""

    LOGGER.debug(f"processing plaato message to plaato data: {msg}.  cmd_type: {msg.command}, msg_id: {msg.msg_id}, status: {msg.status}, length: {msg.length}, kind: {msg.kind}, id_val: {msg.id_val}, dataL {msg.data}")
        
    if msg.command == BlynkCommand.GET_SHARED_DASH:
        return ("id", msg.data, msg.id_val)
    elif msg.command == BlynkCommand.INTERNAL:
        return ("internal", msg.data, msg.id_val)
    elif msg.command == BlynkCommand.HARDWARE or msg.command == BlynkCommand.PROPERTY:
        return _decode_hardware_property(msg)
    
    LOGGER.debug(f"Unknown data kind: {msg}")
    return None

def _decode_hardware_property(msg: PlaatoMessage, include_unknown_data: bool = False) -> Optional[Tuple[str, Any]]:
    cmd = "hardware"
    if msg.command == BlynkCommand.PROPERTY:
        cmd = "property"
    
    key = (cmd, msg.kind, msg.id_val)
    
    if key in PLAATO_DATA_MAP:
        name = PLAATO_DATA_MAP[key]
        return (name, msg.data, msg.id_val)
    else:
        LOGGER.debug(f"Unknown data type: {msg}")
        
        if include_unknown_data:
            return (f"_{cmd}_{msg.kind}_{msg.id_val}", msg.data, msg.id_val)
        
        return None