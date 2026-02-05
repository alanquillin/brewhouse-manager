import base64

import httpx
from httpx import AsyncClient, BasicAuth

from db import async_session_scope
from db.tap_monitors import TapMonitors as TapMonitorsDB
from lib.tap_monitors import InvalidDataType, TapMonitorBase
from lib.tap_monitors.exceptions import TapMonitorDependencyError

KEYMAP = {
    "percent_beer_remaining": "percentRemaining",
    "total_beer_remaining": "totalVolumeRemaining",
    "beer_remaining_unit": "displayVolumeUnit",
    "firmware_version": "firmwareVersion",
}


class KegVolumeMonitor(TapMonitorBase):
    def supports_discovery(self):
        return True

    async def get(self, key, monitor_id=None, monitor=None, meta=None, **kwargs):
        if not monitor_id and not monitor and not meta:
            raise Exception("WTH!!")

        if not meta:
            if not monitor:
                with async_session_scope(self.config) as session:
                    monitor = await TapMonitorsDB.get_by_pkey(session, monitor_id)
            meta = monitor.meta

        device_id = meta.get("device_id")
        data = await self._get(f"devices/{device_id}")
        return data.get(KEYMAP.get(key, "unknown"))

    async def get_all(self, monitor_id=None, monitor=None, meta=None, **kwargs):
        if not monitor_id and not monitor and not meta:
            raise Exception("WTH!!")

        if not meta:
            if not monitor:
                with async_session_scope(self.config) as session:
                    monitor = await TapMonitorsDB.get_by_pkey(session, monitor_id)
            meta = monitor.meta

        device_id = meta.get("device_id")
        data = await self._get(f"devices/{device_id}")
        return {
            "percentRemaining": data.get("percentRemaining"),
            "totalVolumeRemaining": data.get("totalVolumeRemaining"),
            "displayVolumeUnit": data.get("displayVolumeUnit"),
            "firmwareVersion": data.get("firmwareVersion"),
        }

    async def discover(self, **kwargs):
        devices = await self._get("devices")

        return [{"id": dev["id"], "name": dev["name"]} for dev in devices]

    def _get_auth_header_val(self):
        api_key = self.config.get("tap_monitors.keg_volume_monitors.api_key")
        api_key = f"svc|{api_key}"
        return f"Bearer {base64.b64encode(api_key.encode('ascii')).decode('ascii')}"

    async def _get(self, path, params=None):
        base_url = self.config.get("tap_monitors.keg_volume_monitors.base_url")
        headers = {"Authorization": self._get_auth_header_val()}

        url = f"{base_url}/api/v1/{path}"
        self.logger.debug("GET Request: %s, params: %s", url, params)

        async with AsyncClient() as client:
            resp = await client.get(url, params=params, headers=headers)
            self.logger.debug("GET response code: %s", resp.status_code)

            j = resp.json()
            self.logger.debug("GET response JSON: %s", j)

            if resp.status_code == 401:
                raise TapMonitorDependencyError(
                    "Keg Volume Monitor returned a 401 Unauthorized.  Check your credencials in the config."
                )
            return j
