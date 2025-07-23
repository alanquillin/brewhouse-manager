from lib import Error, logging
from lib.config import Config

CONFIG = Config()
LOGGER = logging.getLogger(__name__)

SENSORS = {}

class InvalidDataType(Error):
    def __init__(self, data_type, message=None):
        if not message:
            message = f"Invalid data type '{data_type}'"

        super().__init__(message)

        self.data_type = data_type


class SensorBase:
    def __init__(self) -> None:
        self.config = Config()
        self.logger = logging.getLogger(self.__class__.__name__)


def _init_sensors():
    global SENSORS

    LOGGER.info("Initializing Sensors")
    if not SENSORS:
        if CONFIG.get("sensors.plaato_keg.enabled", False):
            LOGGER.info("Enabling plaato-keg sensors ")
            from lib.sensors.plaato_key import PlaatoKeg
            SENSORS["plaato-keg"] = PlaatoKeg()
        else: 
            LOGGER.info("Disabling plaato-keg sensors")

        if CONFIG.get("sensors.kegtron.pro.enabled", False):
            LOGGER.info("Enabling kegtron pro sensors ")
            from lib.sensors.kegtron import KegtronPro
            SENSORS["kegtron-pro"] = KegtronPro()
        else:
            LOGGER.info("Disabling kegtron pro sensors")
            
        if CONFIG.get("sensors.keg_volume_monitors.enabled", False):
            from lib.sensors.keg_volume_monitor import KegVolumeMonitor
            LOGGER.info("Enabling keg_volume_monitors sensors types")

            if CONFIG.get("sensors.keg_volume_monitors.weight.enabled", False):
                LOGGER.info("Enabling keg_volume_monitors weight sensors")
                SENSORS["keg-volume-monitor-weight"] = KegVolumeMonitor()
            else:
                LOGGER.info("Disabling keg_volume_monitors weight sensors")
            
            if(CONFIG.get("sensors.keg_volume_monitors.flow.enabled", False)):
                LOGGER.info("Enabling keg_volume_monitors flow sensors")
                SENSORS["keg-volume-monitor-flow"] = KegVolumeMonitor()
            else:
                LOGGER.info("Disabling keg_volume_monitors flow sensors")
        else:
            LOGGER.info("Disabling keg_volume_monitors sensors types")


def get_types():
    return SENSORS.keys()


def get_sensor_lib(_type):
    return SENSORS.get(_type)


_init_sensors()
