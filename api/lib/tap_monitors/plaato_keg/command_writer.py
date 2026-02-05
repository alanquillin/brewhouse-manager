from enum import IntEnum, StrEnum
from typing import List, Any, Optional, Dict

from lib import logging
from lib.tap_monitors.plaato_keg.blynk_protocol import BlynkCommand, encode_command as encode_blynk_command
from lib.tap_monitors.plaato_keg.plaato_protocol import PlaatoPin, validate_and_pad_1_and_2
LOGGER = logging.getLogger(__name__)


class Commands(StrEnum):
    SET_MODE = "set-mode"
    SET_UNIT = "set-unit"
    SET_MEASURE_UNIT = "set-measure-unit"
    SET_EMPTY_KEG_WEIGHT = "set-empty-keg-weight"
    SET_MAX_KEG_VOLUME = "set-max-keg-volume"

COMMAND_MAPP: Dict[str, Dict[int, Optional[Any]]] = {
    Commands.SET_MODE: {"pin": PlaatoPin.MODE, "fn": validate_and_pad_1_and_2},
    Commands.SET_UNIT: {"pin": PlaatoPin.UNIT, "fn": validate_and_pad_1_and_2},
    Commands.SET_MEASURE_UNIT: {"pin": PlaatoPin.MEASURE_UNIT, "fn": validate_and_pad_1_and_2},
    Commands.SET_EMPTY_KEG_WEIGHT: {"pin": PlaatoPin.EMPTY_KEG_WEIGHT},
    Commands.SET_MAX_KEG_VOLUME: {"pin": PlaatoPin.MAX_KEG_VOLUME},

    # "calibrate": {"pin": PlaatoPin.CALIBRATE},
    # "tare": {"pin": PlaatoPin.TARE, "value": "1"},
    # "tare-release": {"pin": PlaatoPin.TARE, "value": "0"},
    
    # "set-date": {"pin": PlaatoPin.DATE},
    # "set-og": {"pin": PlaatoPin.OG},
    # "set-fg": {"pin": PlaatoPin.FG},
    # "set-abv": {"pin": PlaatoPin.ABV},
    
}

def sanitize_command(command: str) -> str:
    return command.lower().replace("_","-")

class CommandWriter:
    """Handles sending commands to Plaato Keg devices"""
    
    def __init__(self, connection_handler):
        self.connection_handler = connection_handler
        self.msg_id_counter = 1
        
    def _get_next_msg_id(self) -> int:
        """Get next message ID"""
        msg_id = self.msg_id_counter
        self.msg_id_counter += 1
        if self.msg_id_counter > 65535:
            self.msg_id_counter = 1
        return msg_id
        
    async def _send_hardware_command(self, device_id: str, pin: int, value: str) -> bool:
        """Send a hardware command to a keg"""
        LOGGER.debug(f"Device command details. device_id: {device_id}, pin: {pin}, data: {value}")
        body = f"vw\x00{pin}\x00{value}".encode('utf-8')
        LOGGER.debug(f"formatted command body: {body}")
        msg_id = self._get_next_msg_id()
        command = encode_blynk_command(BlynkCommand.HARDWARE, msg_id, body)
        LOGGER.debug(f"Encoded command: {command}")
        
        success = await self.connection_handler.send_command_to_keg(device_id, command)
        if success:
            LOGGER.info(f"Sent hardware command to keg {device_id}: pin={pin}, value={value}")
        else:
            LOGGER.error(f"Failed to send hardware command to keg {device_id}")
        return success
    
    async def send_command(self, device_id:str, command: str, value: Any = None) -> bool:
        command_info = COMMAND_MAPP.get(sanitize_command(command))

        if not command_info:
            return False #TODO raise exception
        
        static_val = command_info.get("value")
        if static_val:
            value = static_val

        if not value:
            return False #TODO raise exception
        
        LOGGER.debug(f"Sending device command: {command}, data: {value}")
        return await self._send_hardware_command(device_id, command_info["pin"], str(value))
        
    def get_connected_kegs(self):
        """Get list of currently connected kegs"""
        return self.connection_handler.get_connected_kegs()
