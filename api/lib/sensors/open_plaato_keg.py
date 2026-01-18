import base64

import httpx
from httpx import BasicAuth, AsyncClient

from db import async_session_scope
from db.sensors import Sensors as SensorsDB
from lib.sensors import SensorBase, InvalidDataType

KEYMAP = {
    "percent_beer_remaining": "percent_of_beer_left",
    "total_beer_remaining": "amount_left",
    "beer_remaining_unit": "beer_left_unit",
    "firmware_version": "firmware_version"
}

class OpenPlaatoKeg(SensorBase):
    def supports_discovery(self):
        return True
    
    async def get(self, data_key, sensor_id=None, sensor=None, meta=None):
        data = await self._get_data(sensor_id, sensor, meta)
        map_key = KEYMAP.get(data_key, None)

        if not map_key:
            self.logger.warning(f"Unknown data key: {map_key}")
            raise InvalidDataType(data_key)
        return data.get(map_key)

    async def get_all(self, sensor_id=None, sensor=None, meta=None):
        data = await self._get_data(sensor_id, sensor, meta)

        return {
            "percentRemaining": data.get("percent_of_beer_left"),
            "totalVolumeRemaining": data.get("amount_left"),
            "displayVolumeUnit": data.get("beer_left_unit"),
            "firmwareVersion": data.get("firmware_version")
        }
    
    async def discover(self):
        devices = await self._get("kegs")

        return [{"id": dev["id"], "name": dev.get("name", "unknown")} for dev in devices]
    

    async def _get_data(self, sensor_id=None, sensor=None, meta=None):
        if not sensor_id and not sensor and not meta:
            raise Exception("WTH!!")

        if not meta:
            if not sensor:
                with async_session_scope as session:
                    sensor = await SensorsDB.get_by_pkey(session, sensor_id)
            meta = sensor.meta

        device_id = meta.get("device_id")
        return await self._get(f"kegs/{device_id}")

    async def _get(self, path, params=None):
        kwargs = {}
        base_url = self.config.get("sensors.open_plaato_keg.base_url") 
        insecure = self.config.get("sensors.open_plaato_keg.insecure")

        if insecure:
            kwargs["verify"] = False 
        
        url = f"{base_url}/api/{path}"
        self.logger.debug("GET Request: %s, params: %s", url, params)
        
        async with AsyncClient() as client:
            resp = client.get(url, params=params, **kwargs)
            self.logger.debug("GET response code: %s", resp.status_code)
            
            j = resp.json()
            self.logger.debug("GET response JSON: %s", j)
            return j
