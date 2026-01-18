import base64

import httpx
from httpx import AsyncClient, BasicAuth

from db import async_session_scope
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
    
    async def get(self, key, sensor_id=None, sensor=None, meta=None):
        if not sensor_id and not sensor and not meta:
            raise Exception("WTH!!")

        if not meta:
            if not sensor:
                with session_scope as session:
                    sensor = await SensorsDB.get_by_pkey(session, sensor_id)
            meta = sensor.meta

        device_id = meta.get("device_id")
        data = await self._get(f"devices/{device_id}")
        return data.get(KEYMAP.get(key, "unknown"))

    async def get_all(self, sensor_id=None, sensor=None, meta=None):
        if not sensor_id and not sensor and not meta:
            raise Exception("WTH!!")

        if not meta:
            if not sensor:
                with async_session_scope as session:
                    sensor = await SensorsDB.get_by_pkey(session, sensor_id)
            meta = sensor.meta

        device_id = meta.get("device_id")
        data = await self._get(f"devices/{device_id}")
        return {
            "percentRemaining": data.get("percentRemaining"),
            "totalVolumeRemaining": data.get("totalVolumeRemaining"),
            "displayVolumeUnit": data.get("displayVolumeUnit"),
            "firmwareVersion": data.get("firmwareVersion")
        }
    
    async def discover(self):
        devices = await self._get("devices")

        return [{"id": dev["id"], "name": dev["name"]} for dev in devices]
    
    def _get_auth_header_val(self):
        api_key = self.config.get("sensors.keg_volume_monitors.api_key")
        api_key = f"svc|{api_key}"
        return f"Bearer {base64.b64encode(api_key.encode('ascii')).decode('ascii')}"

    async def _get(self, path, params=None):
        base_url = self.config.get("sensors.keg_volume_monitors.base_url") 
        headers = {
            "Authorization": self._get_auth_header_val()
        }
        
        url = f"{base_url}/api/v1/{path}"
        self.logger.debug("GET Request: %s, params: %s", url, params)
        
        async with AsyncClient() as client:
            resp = client.get(url, params=params, headers=headers)
            self.logger.debug("GET response code: %s", resp.status_code)
            
            j = resp.json()
            self.logger.debug("GET response JSON: %s", j)
            return j
    
