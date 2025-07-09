import base64

import requests
from requests import auth
from requests.auth import HTTPBasicAuth

from db import session_scope
from db.sensors import Sensors as SensorsDB
from lib.sensors import InvalidDataType, SensorBase


class PlaatoKeg(SensorBase):
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
    
    def get(self, data_type, sensor_id=None, sensor=None, meta=None):
        if not sensor_id and not sensor and not meta:
            raise Exception("WTH!!")

        if not meta:
            if not sensor:
                with session_scope as session:
                    sensor = SensorsDB.get_by_pkey(session, sensor_id)
            meta = sensor.meta

        pin = self._data_type_to_pin.get(data_type)
        if not pin:
            raise InvalidDataType(data_type)

        return self._get(pin, meta)

    def get_all(self, sensor_id=None, sensor=None, meta=None):
        if not sensor_id and not sensor and not meta:
            raise Exception("WTH!!")

        if not meta:
            if not sensor:
                with session_scope as session:
                    sensor = SensorsDB.get_by_pkey(session, sensor_id)
            meta = sensor.meta

        return {
            "percentRemaining": self._get(self._data_type_to_pin["percent_beer_remaining"], meta),
            "totalVolumeRemaining": self._get(self._data_type_to_pin["total_beer_remaining"], meta),
            "displayVolumeUnit": self._get(self._data_type_to_pin["beer_remaining_unit"], meta),
            "firmwareVersion": self._get(self._data_type_to_pin["firmware_version"], meta)
        }

    def _get(self, pin, meta, params=None):
        auth_token = meta.get("auth_token")
        url = f"http://plaato.blynk.cc/{auth_token}/get/{pin}"
        self.logger.debug("GET Request: %s, params: %s", url, params)
        resp = requests.get(url, params=params)
        self.logger.debug("GET response code: %s", resp.status_code)
        if resp.status_code != 200:
            return {}
        j = resp.json()
        self.logger.debug("GET response JSON: %s", j)
        return j
