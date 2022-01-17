from lib.config import Config
from lib import logging

SENSORS = {}

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