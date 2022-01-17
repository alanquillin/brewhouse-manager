from lib.config import Config
from lib import logging, Error

SENSORS = {}

class InvalidDataType(Error):
    def __init__(self, data_type, message=None):
        if not message:
            message = f"Invalid data type '{data_type}'"

        super().__init__(message)
        
        self.data_type = data_type

class SensorBase():
    def __init__(self) -> None:
        self.config = Config()
        self.logger = logging.getLogger(self.__class__.__name__)

def _init_sensors():
    global SENSORS
    if not SENSORS:
        from lib.sensors.plaato_key import PlaatoKeg
        
        SENSORS = {
            "plaato-keg": PlaatoKeg()
        }

def get_types():
    return SENSORS.keys()

def get_sensor_lib(_type):
    return SENSORS.get(_type)

_init_sensors()