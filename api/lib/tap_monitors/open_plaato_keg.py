from httpx import AsyncClient

from db import async_session_scope
from db.tap_monitors import TapMonitors as TapMonitorsDB
from lib.tap_monitors import InvalidDataType, TapMonitorBase

KEYMAP = {
    "percent_beer_remaining": "percent_of_beer_left",
    "total_beer_remaining": "amount_left",
    "beer_remaining_unit": "beer_left_unit",
    "firmware_version": "firmware_version",
}


class OpenPlaatoKeg(TapMonitorBase):
    @staticmethod
    def supports_discovery():
        return True

    @staticmethod
    def reports_online_status():
        return False

    async def is_online(self, **kwargs):
        raise NotImplementedError("open-plaato-keg does not support reporting online")

    async def get(self, data_key, monitor_id=None, monitor=None, meta=None, **kwargs):
        data = await self._get_data(monitor_id, monitor, meta)
        map_key = KEYMAP.get(data_key, None)

        if not map_key:
            self.logger.warning("Unknown data key: %s", data_key)
            raise InvalidDataType(data_key)
        return data.get(map_key)

    async def get_all(self, monitor_id=None, monitor=None, meta=None, **kwargs):
        data = await self._get_data(monitor_id, monitor, meta)

        return {
            "percentRemaining": data.get("percent_of_beer_left"),
            "totalVolumeRemaining": data.get("amount_left"),
            "displayVolumeUnit": data.get("beer_left_unit"),
            "firmwareVersion": data.get("firmware_version"),
        }

    async def discover(self, **kwargs):
        devices = await self._get("kegs")

        return [{"id": dev["id"], "name": dev.get("name", "unknown")} for dev in devices]

    async def _get_data(self, monitor_id=None, monitor=None, meta=None):
        if not monitor_id and not monitor and not meta:
            raise ValueError("monitor_id, monitor, or meta must be provided")

        if not meta:
            if not monitor:
                async with async_session_scope(self.config) as session:
                    monitor = await TapMonitorsDB.get_by_pkey(session, monitor_id)
            meta = monitor.meta

        device_id = meta.get("device_id")
        return await self._get(f"kegs/{device_id}")

    async def _get(self, path, params=None):
        kwargs = {}
        client_kwargs = {}
        base_url = self.config.get("tap_monitors.open_plaato_keg.base_url")
        insecure = self.config.get("tap_monitors.open_plaato_keg.insecure")

        if insecure:
            client_kwargs["verify"] = False

        url = f"{base_url}/api/{path}"
        self.logger.debug("GET Request: %s, params: %s", url, params)

        async with AsyncClient(**client_kwargs) as client:
            resp = await client.get(url, params=params, **kwargs)
            self.logger.debug("GET response code: %s", resp.status_code)

            j = resp.json()
            self.logger.debug("GET response JSON: %s", j)
            return j
