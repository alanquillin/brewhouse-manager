from enum import IntEnum
from typing import List, Any, Optional, Dict

from lib import logging
from lib.sensors.plaato_keg.blynk_protocol import BlynkMessage, BlynkCommand, encode_command as encode_blynk_command

LOGGER = logging.getLogger(__name__)



# NOTES on the the different pin values
#
# MODE:   PIN 88
#   Not sure why but I cannot get the device to send this value... however, when in beer mode, you get the OG and FG values, when in CO2 mode, these valkues are empty
#   This can be used to help determine which mode is set
#   01 - Set mode = Beer
#   02 - Set moe = CO2
#
# UNITs:  This can be set by setting pin 71 (UNIT) and 75 (MEASURE_UNIT).  
#   These affect the readonly pins: 74 (BEER_LEFT_UNIT) and 82 (VOLUME_UNIT)
#   Both set to 1 - Metric (BEER_LEFT_UNIT = Kg, VOLUME_UNIT = L)               Mode = weight (metric)
#   Both set to 2 - US (BEER_LEFT_UNIT = gal, VOLUME_UNIT = gal)                Mode = vol   (US)
#   UNIT = 1 and MEASURE_UNIT = 2 = both (BEER_LEFT_UNIT and VOLUME_UNIT) = L   Mode = vol   (metric)
#   UNIT = 2 and MEASURE_UNIT = 1 = BEER_LEFT_UNIT - lbs, VOLUME_UNIT = gal     Mode = weight (US)



def validate_and_pad_1_and_2(val:str) -> Optional[str]:
    if not val:
        return #TODO throw error
    
    if len(val) == 1:
        val = f"0{val}"

    if val != "01" and val != "02":
        return None #TODO throw error
    
    return val

class PlaatoPin(IntEnum):
    LAST_POUR_STR = 47
    PERCENT_BEER_LEFT = 48
    IS_POURING = 49
    AMOUNT_LEFT = 51
    TEMPERATURE_OFFSET = 52
    TEMPERATURE = 56
    LAST_POUR = 59
    TARE = 60
    CALIBRATE = 61
    EMPTY_KEG_WEIGHT = 62
    BEER_STYLE = 64
    OG = 65
    FG = 66
    DATE = 67
    ABV = 68
    TEMPERATURE_STR = 69
    CALCULATED_ABV_STR = 70
    UNIT = 71
    CALCULATE = 72
    BEER_LEFT_UNIT = 74
    MEASURE_UNIT = 75
    MAX_KEG_VOLUME = 76
    TEMP_UNIT = 80
    WIFI_SIGNAL_STRENGTH = 81
    VOLUME_UNIT = 82
    LEAK_DETECTION = 83
    MIN_TEMP = 86
    MAX_TEMP = 87
    MODE = 88
    SENSITIVITY = 89
    CHIP_TEMPERATURE_STR = 92
    FIRMWARE_VERSION = 93


class PlaatoMessage(BlynkMessage):
    kind: Optional[str]
    id_val: Optional[str]
    data: Optional[Any]

    def __init__(self, msg: BlynkMessage, kind: str = None, id_val: str = None, data = None, **kwargs):
        super().__init__(command=msg.command, msg_id=msg.msg_id, status=msg.status, length=msg.length, body=msg.body)
        self.kind = kind
        self.id_val = id_val
        self.data = data
    
    def __repr__(self):
        if self.command == BlynkCommand.RESPONSE:
            return f"PlaatoMessage(command=RESPONSE, msg_id={self.msg_id}, status={self.status}, data={self.data})"
        return f"PlaatoMessage(command={self.command}, msg_id={self.msg_id}, length={self.length}, kind={self.kind}, id_val={self.id_val}, data={self.data})"


def decode_list(msgs: List[BlynkMessage]) -> List[PlaatoMessage]:
    """Decode a list of commands"""
    return [decode(msg) for msg in msgs]

def decode(msg: BlynkMessage) -> PlaatoMessage:
    """Decode a single Plaato protocol message"""
    if msg.command == BlynkCommand.INTERNAL:
        return _decode_internal(msg)
    else:
        return _decode(msg)

def _decode_internal(msg: BlynkMessage) -> PlaatoMessage:
    """Decode internal message containing device properties"""
    data = msg.body
    if isinstance(data, bytes):
        data = data.decode('utf-8', errors='ignore')
        
    parts = data.split('\0')
    parts = [p for p in parts if p]
    
    internal_props = {}
    for i in range(0, len(parts), 2):
        if i + 1 < len(parts):
            key = parts[i]
            value = parts[i + 1]
            internal_props[key] = value
    data = internal_props
    
    return PlaatoMessage(msg, kind="not_relevant", id_val="not_relevant", data=data)

def _decode(msg: BlynkMessage) -> PlaatoMessage:
    """Decode standard hardware/property messages"""
    if msg.command == BlynkCommand.NOTIFY or msg.command == BlynkCommand.PING:
        return PlaatoMessage(msg)
    
    data = msg.body
    if isinstance(data, bytes):
        data = data.decode('utf-8', errors='ignore')
        
    parts = data.split('\0')
    parts = [p for p in parts if p]
    
    kind = "not_relevant"
    id_val = "not_relevant"
    if len(parts) == 1:
        data = parts[0]
    elif len(parts) == 3:
        kind = parts[0]
        id_val = parts[1]
        data = parts[2]
    else:
        data = parts
    
    return PlaatoMessage(msg, kind=kind, id_val=id_val, data=data)