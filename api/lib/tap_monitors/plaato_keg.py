from datetime import datetime
from typing import Any, Dict, List

from db import async_session_scope
from db.plaato_data import PlaatoData as PlaatoDataDB
from db.tap_monitors import TapMonitors as TapMonitorsDB
from lib.devices.plaato_keg import service_handler
from lib.tap_monitors import InvalidDataType, TapMonitorBase

KEYMAP = {
    "percent_beer_remaining": "percent_of_beer_left",
    "total_beer_remaining": "amount_left",
    "beer_remaining_unit": "beer_left_unit",
    "firmware_version": "firmware_version",
    "last_updated_on": "last_updated_on",
}


class PlaatoKeg(TapMonitorBase):
    @staticmethod
    def supports_discovery():
        return True

    @staticmethod
    def reports_online_status():
        return True

    async def is_online(self, monitor_id=None, monitor=None, meta=None, device_id=None, db_session=None, **kwargs):
        if not device_id:
            if not meta:
                if not monitor:
                    if not db_session:
                        async with async_session_scope(self.config) as session:
                            return await self.is_online(monitor_id, monitor, meta, device_id, db_session=session, **kwargs)
                    else:
                        monitor = await TapMonitorsDB.get_by_pkey(db_session, monitor_id)
                meta = monitor.meta
            device_id = meta.get("device_id")
        registered_devices = service_handler.connection_handler.get_registered_device_ids()
        self.logger.debug("Checking if device %s is online. Registered devices: %s", device_id, registered_devices)
        return device_id in registered_devices

    async def get(self, data_key, monitor_id=None, monitor=None, meta=None, db_session=None, **kwargs) -> Any:
        data, meta = await self._get_data(monitor_id, monitor, meta, db_session)
        map_key = KEYMAP.get(data_key, None)

        if not map_key:
            self.logger.warning("Unknown data key: %s", data_key)
            raise InvalidDataType(data_key)
        return data.get(map_key)

    async def get_all(self, monitor_id=None, monitor=None, meta=None, db_session=None, **kwargs) -> Dict:
        data, meta = await self._get_data(monitor_id, monitor, meta, db_session)

        last_updated_on = data.get("last_updated_on")
        if last_updated_on and isinstance(last_updated_on, datetime):
            data["last_updated_on"] = last_updated_on.timestamp()

        return {
            "percentRemaining": data.get("percent_of_beer_left"),
            "totalVolumeRemaining": data.get("amount_left"),
            "displayVolumeUnit": data.get("beer_left_unit"),
            "firmwareVersion": data.get("firmware_version"),
            "lastUpdatedOn": data.get("last_updated_on"),
            "online": await self.is_online(monitor_id, monitor, meta, db_session=db_session),
        }

    async def discover(self, db_session=None, **kwargs) -> List[Dict]:
        if not db_session:
            async with async_session_scope(self.config) as db_session:
                return await self.discover(db_session=db_session, **kwargs)

        devices = await PlaatoDataDB.query(db_session)

        res = []
        if devices:
            for dev in devices:
                if dev.last_updated_on:
                    res.append({"id": dev.id, "name": dev.name})
        return res

    async def _get_data(self, monitor_id=None, monitor=None, meta=None, db_session=None) -> Dict:
        if not monitor_id and not monitor and not meta:
            raise Exception("WTH!!")

        if not meta:
            if not monitor:
                async with async_session_scope(self.config) as session:
                    monitor = await TapMonitorsDB.get_by_pkey(session, monitor_id)
            meta = monitor.meta

        device_id = meta.get("device_id")
        return await self._get(db_session, device_id), meta

    async def _get(self, db_session, device_id) -> Dict:
        if not db_session:
            async with async_session_scope(self.config) as dbsession:
                return await self._get(dbsession, device_id)

        plaato_data = await PlaatoDataDB.get_by_pkey(db_session, device_id)
        if not plaato_data:
            return {}
        return plaato_data.to_dict()
