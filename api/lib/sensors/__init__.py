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
        if CONFIG.get("sensors.plaato_blynk.enabled", False):
            LOGGER.info("Enabling plaato-blynk sensors ")
            from lib.sensors.plaato_blynk import PlaatoBlynk

            SENSORS["plaato-blynk"] = PlaatoBlynk()
        else:
            LOGGER.info("Disabling plaato-blynk sensors")

        if CONFIG.get("sensors.kegtron.pro.enabled", False):
            LOGGER.info("Enabling kegtron pro sensors ")
            from lib.sensors.kegtron import (
                KegtronPro,
                SENSOR_TYPE as kegtron_sensor_type,
            )

            SENSORS[kegtron_sensor_type] = KegtronPro()
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

            if CONFIG.get("sensors.keg_volume_monitors.flow.enabled", False):
                LOGGER.info("Enabling keg_volume_monitors flow sensors")
                SENSORS["keg-volume-monitor-flow"] = KegVolumeMonitor()
            else:
                LOGGER.info("Disabling keg_volume_monitors flow sensors")
        else:
            LOGGER.info("Disabling keg_volume_monitors sensors types")

        if CONFIG.get("sensors.open_plaato_keg.enabled", False):
            from lib.sensors.open_plaato_keg import OpenPlaatoKeg

            LOGGER.info("Enabling open_plaato_keg sensor type")
            SENSORS["open-plaato-keg"] = OpenPlaatoKeg()
        else:
            LOGGER.info("Disabling open_plaato_keg sensors types")


def get_types():
    return SENSORS.keys()


def get_sensor_lib(_type):
    return SENSORS.get(_type)


_init_sensors()
