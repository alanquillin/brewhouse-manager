import base64

import requests
from requests import auth
from requests.auth import HTTPBasicAuth

from db import session_scope
from db.sensors import Sensors as SensorsDB
from lib.sensors import SensorBase

KEYMAP = {
    "percent_beer_remaining": "percent_of_beer_left",
    "total_beer_remaining": "amount_left",
    "beer_remaining_unit": "beer_left_unit",
    "firmware_version": "firmware_version"
}

class OpenPlaatoKeg(SensorBase):
    def supports_discovery(self):
        return True
    
    def get(self, key, sensor_id=None, sensor=None, meta=None):
        if not sensor_id and not sensor and not meta:
            raise Exception("WTH!!")

        if not meta:
            if not sensor:
                with session_scope as session:
                    sensor = SensorsDB.get_by_pkey(session, sensor_id)
            meta = sensor.meta

        device_id = meta.get("device_id")
        data = self._get(f"kegs/{device_id}")
        key = KEYMAP.get(key, None)

        if not key:
            return None
        return data.get(key)

    def get_all(self, sensor_id=None, sensor=None, meta=None):
        if not sensor_id and not sensor and not meta:
            raise Exception("WTH!!")

        if not meta:
            if not sensor:
                with session_scope as session:
                    sensor = SensorsDB.get_by_pkey(session, sensor_id)
            meta = sensor.meta

        device_id = meta.get("device_id")
        data = self._get(f"kegs/{device_id}")

        return {
            "percentRemaining": data.get("percent_of_beer_left"),
            "totalVolumeRemaining": data.get("amount_left"),
            "displayVolumeUnit": data.get("beer_left_unit"),
            "firmwareVersion": data.get("firmware_version")
        }
    
    def discover(self):
        devices = self._get("kegs")

        return [{"id": dev["id"], "name": dev["name"]} for dev in devices]
    

    def _get(self, path, params=None):
        kwargs = {}
        base_url = self.config.get("sensors.open_plaato_keg.base_url") 
        insecure = self.config.get("sensors.open_plaato_keg.insecure")

        if insecure:
            kwargs["verify"] = False 
        
        url = f"{base_url}/api/{path}"
        self.logger.debug("GET Request: %s, params: %s", url, params)
        
        resp = requests.get(url, params=params, **kwargs)
        self.logger.debug("GET response code: %s", resp.status_code)
        
        j = resp.json()
        self.logger.debug("GET response JSON: %s", j)
        return j
