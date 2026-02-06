import requests

from db import session_scope
from db.tap_monitors import TapMonitors as TapMonitorsDB
from lib.tap_monitors import InvalidDataType, TapMonitorBase


class PlaatoBlynk(TapMonitorBase):
    _data_type_to_pin = {
        "percent_beer_remaining": "v48",
        "total_beer_remaining": "v51",
        "beer_remaining_unit": "v74",
        "style": "v64",
        "og": "v65",
        "fg": "v66",
        "abv": "v68",
        "firmware_version": "v93",
    }

    def supports_discovery(self):
        return False

    def get(self, data_type, monitor_id=None, monitor=None, meta=None, **kwargs):
        if not monitor_id and not monitor and not meta:
            raise Exception("WTH!!")

        if not meta:
            if not monitor:
                with session_scope(self.config) as session:
                    monitor = TapMonitorsDB.get_by_pkey(session, monitor_id)
            meta = monitor.meta

        pin = self._data_type_to_pin.get(data_type)
        if not pin:
            raise InvalidDataType(data_type)

        return self._get(pin, meta)

    def get_all(self, monitor_id=None, monitor=None, meta=None, **kwargs):
        if not monitor_id and not monitor and not meta:
            raise Exception("WTH!!")

        if not meta:
            if not monitor:
                with session_scope(self.config) as session:
                    monitor = TapMonitorsDB.get_by_pkey(session, monitor_id)
            meta = monitor.meta

        return {
            "percentRemaining": self._get(self._data_type_to_pin["percent_beer_remaining"], meta),
            "totalVolumeRemaining": self._get(self._data_type_to_pin["total_beer_remaining"], meta),
            "displayVolumeUnit": self._get(self._data_type_to_pin["beer_remaining_unit"], meta),
            "firmwareVersion": self._get(self._data_type_to_pin["firmware_version"], meta),
        }

    def discover(self, **kwargs):
        raise NotImplementedError("Plaato Blynk does not support discovery")

    def _get(self, pin, meta, params=None):
        auth_token = meta.get("auth_token")
        base_url = self.config.get("tap_monitors.plaato_blynk.base_url", "http://plaato.blynk.cc")
        url = f"{base_url}/{auth_token}/get/{pin}"
        self.logger.debug("GET Request: %s, params: %s", url, params)
        resp = requests.get(url, params=params, timeout=10)
        self.logger.debug("GET response code: %s", resp.status_code)
        if resp.status_code != 200:
            return {}
        j = resp.json()
        self.logger.debug("GET response JSON: %s", j)
        return j
