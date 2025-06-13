import base64

import requests
from requests import auth
from requests.auth import HTTPBasicAuth

from db import session_scope
from db.sensors import Sensors as SensorsDB
from lib.sensors import InvalidDataType, SensorBase

KEYMAP = {
    "percent_beer_remaining": "percentRemaining",
    "total_beer_remaining": "totalVolumeRemaining",
    "beer_remaining_unit": "displayVolumeUnit",
    "firmware_version": "firmwareVersion"
}

class KegVolumeMonitor(SensorBase):
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
        data = self._get(f"devices/{device_id}")
        return data.get(KEYMAP.get(key, "unknown"))

    def get_all(self, sensor_id=None, sensor=None, meta=None):
        if not sensor_id and not sensor and not meta:
            raise Exception("WTH!!")

        if not meta:
            if not sensor:
                with session_scope as session:
                    sensor = SensorsDB.get_by_pkey(session, sensor_id)
            meta = sensor.meta

        device_id = meta.get("device_id")
        data = self._get(f"devices/{device_id}")
        return {
            "percentRemaining": data.get("percentRemaining"),
            "totalVolumeRemaining": data.get("totalVolumeRemaining"),
            "displayVolumeUnit": data.get("displayVolumeUnit"),
            "firmwareVersion": data.get("firmwareVersion")
        }
    
    def discover(self):
        devices = self._get("devices")

        return [{"sensor_id": dev["id"], "sensor_name": dev["name"]} for dev in devices]
    
    def _get_auth_header_val(self):
        api_key = self.config.get("sensors.keg_volume_monitors.api_key")
        api_key = f"svc|{api_key}"
        return f"Bearer {base64.b64encode(api_key.encode('ascii')).decode('ascii')}"

    def _get(self, path, params=None):
        base_url = self.config.get("sensors.keg_volume_monitors.base_url") 
        headers = {
            "Authorization": self._get_auth_header_val()
        }
        
        url = f"{base_url}/api/v1/{path}"
        self.logger.debug("GET Request: %s, params: %s", url, params)
        
        resp = requests.get(url, params=params, headers=headers)
        self.logger.debug("GET response code: %s", resp.status_code)
        
        j = resp.json()
        self.logger.debug("GET response JSON: %s", j)
        return j
    
