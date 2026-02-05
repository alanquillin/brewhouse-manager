from typing import Dict, List

from lib import Error, logging
from lib.config import Config

CONFIG = Config()
LOGGER = logging.getLogger(__name__)

TAP_MONITORS = {}


class InvalidDataType(Error):
    def __init__(self, data_type, message=None):
        if not message:
            message = f"Invalid data type '{data_type}'"

        super().__init__(message)

        self.data_type = data_type


class TapMonitorBase:
    def __init__(self) -> None:
        self.config = Config()
        self.logger = logging.getLogger(self.__class__.__name__)


def _init_tap_monitors():
    global TAP_MONITORS

    LOGGER.info("Initializing Tap Monitors")
    if not TAP_MONITORS:
        if CONFIG.get("tap_monitors.plaato_blynk.enabled", False):
            LOGGER.info("Enabling plaato-blynk tap monitors type")
            from lib.tap_monitors.plaato_blynk import PlaatoBlynk

            TAP_MONITORS["plaato-blynk"] = PlaatoBlynk()
        else:
            LOGGER.info("Disabling plaato-blynk tap monitors")

        if CONFIG.get("tap_monitors.kegtron.pro.enabled", False):
            LOGGER.info("Enabling kegtron pro tap monitors ")
            from lib.tap_monitors.kegtron import (
                KegtronPro,
                MONITOR_TYPE as kegtron_monitor_type,
            )

            TAP_MONITORS[kegtron_monitor_type] = KegtronPro()
        else:
            LOGGER.info("Disabling kegtron pro tap monitors")

        if CONFIG.get("tap_monitors.keg_volume_monitors.enabled", False):
            from lib.tap_monitors.keg_volume_monitor import KegVolumeMonitor

            LOGGER.info("Enabling keg_volume_monitors tap monitor types")

            if CONFIG.get("tap_monitors.keg_volume_monitors.weight.enabled", False):
                LOGGER.info("Enabling keg_volume_monitors weight tap monitors")
                TAP_MONITORS["keg-volume-monitor-weight"] = KegVolumeMonitor()
            else:
                LOGGER.info("Disabling keg_volume_monitors weight tap monitors")

            if CONFIG.get("tap_monitors.keg_volume_monitors.flow.enabled", False):
                LOGGER.info("Enabling keg_volume_monitors flow tap monitors")
                TAP_MONITORS["keg-volume-monitor-flow"] = KegVolumeMonitor()
            else:
                LOGGER.info("Disabling keg_volume_monitors flow tap monitors")
        else:
            LOGGER.info("Disabling keg_volume_monitors tap monitor types")

        if CONFIG.get("tap_monitors.open_plaato_keg.enabled", False):
            from lib.tap_monitors.open_plaato_keg import OpenPlaatoKeg

            LOGGER.info("Enabling open_plaato_keg tap monitor type")
            TAP_MONITORS["open-plaato-keg"] = OpenPlaatoKeg()
        else:
            LOGGER.info("Disabling open_plaato_keg tap monitor types")

        if CONFIG.get("tap_monitors.plaato_keg.enabled", False):
            from lib.tap_monitors.plaato_keg import PlaatoKeg

            LOGGER.info("Enabling plaato_keg tap monitor type")
            TAP_MONITORS["plaato-keg"] = PlaatoKeg()
        else:
            LOGGER.info("Disabling plaato_keg tap monitor types")

    
def get_types() -> List[Dict]:
    res = []
    for k, v in  TAP_MONITORS.items():
        res.append({"type": k, "supports_discovery": v.supports_discovery()})
    return res


def get_tap_monitor_lib(_type):
    return TAP_MONITORS.get(_type)


_init_tap_monitors()
