import base64

import requests
from requests import auth
from requests.auth import HTTPBasicAuth

from lib.sensors import SensorBase
from db import session_scope
from db.sensors import Sensors as SensorsDB

class PlaatoKeg(SensorBase):
    _data_type_to_pin = {
        "percent_beer_remaining": "v48"
    }

    def get(self, data_type, sensor_id=None, sensor=None, meta=None):
        if not sensor_id and not sensor and not meta:
            raise Exception("WTH!!")

        if not meta:
            if not sensor:
                with session_scope as session:
                    sensor = SensorsDB.get_by_pkey(session, sensor_id)
            meta = sensor.meta

        pin = self._data_type_to_pin.get(data_type)
        return self._get(pin, meta)

    def _get(self, pin, meta, params=None):  
        auth_token = meta.get("auth_token")
        url = f"http://plaato.blynk.cc/{auth_token}/get/{pin}"
        self.logger.debug("GET Request: %s, params: %s", url, params)
        resp = requests.get(url, params=params)
        self.logger.debug("GET response code: %s", resp.status_code)
        j = resp.json()
        self.logger.debug("GET response JSON: %s", j)
        return j