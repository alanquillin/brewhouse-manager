from typing import Dict

from httpx import AsyncClient, BasicAuth

from db import async_session_scope
from db.tap_monitors import TapMonitors as TapMonitorsDB
from lib.tap_monitors import TapMonitorBase
from lib.tap_monitors.exceptions import TapMonitorDependencyError
from lib.units import from_ml


class KegtronBase(TapMonitorBase):
    pass


MONITOR_TYPE = "kegtron-pro"


class KegtronPro(KegtronBase):
    supported_device_keys = ["beaconEna", "cleanEna"]
    supported_port_keys = [
        "abv",
        "beaconEna",
        "userName",
        "userDesc",
        "ibu",
        "maker",
        "style",
        "volSize",
    ]
    supported_port_user_override_keys = ["dateTapped", "dateCleaned", "volStart"]

    def __init__(self) -> None:
        super().__init__()
        self.monitor_data_included = True

        self._data_type_to_key = {
            "percent_beer_remaining": self._get_percent_remaining,
            "total_beer_remaining": self._get_total_remaining,
            "beer_remaining_unit": self._get_vol_unit,
        }

        self.default_vol_unit = self.config.get("tap_monitors.preferred_vol_unit")
        self.kegtron_customer_api_key = self.config.get("tap_monitors.kegtron.pro.auth.customer_api_key")
        self.kegtron_username = self.config.get("tap_monitors.kegtron.pro.auth.username")
        self.kegtron_password = self.config.get("tap_monitors.kegtron.pro.auth.password")

    @staticmethod
    def supports_discovery():
        return True

    @staticmethod
    def reports_online_status():
        return True

    async def is_online(self, monitor_id=None, monitor=None, meta=None, db_session=None, device=None, **kwargs) -> bool:
        if not meta:
            meta = await self.extract_meta(monitor_id, monitor, meta, db_session)

        if not device:
            device = await self._get(meta)

        if not device:
            return False

        return device.get("online", False)

    async def get(self, data_type, monitor_id=None, monitor=None, meta=None, db_session=None, **kwargs) -> any:
        if not meta:
            meta = await self.extract_meta(monitor_id, monitor, meta, db_session)

        fn = self._data_type_to_key[data_type]

        if callable(fn):
            return await fn(meta)

        return await self._get_from_key(fn, meta)

    async def get_all(self, monitor_id=None, monitor=None, meta=None, db_session=None, **kwargs) -> Dict:
        if not meta:
            meta = await self.extract_meta(monitor_id, monitor, meta, db_session)

        device = await self._get(meta)

        return {
            "percentRemaining": await self._get_percent_remaining(meta, device),
            "totalVolumeRemaining": await self._get_total_remaining(meta, device),
            "displayVolumeUnit": await self._get_vol_unit(meta),
            "online": await self.is_online(meta=meta, db_session=db_session, device=None, **kwargs),
        }

    def _get_device_access_token(self, meta):
        return meta.get("access_token")

    async def _get_total_remaining(self, meta, device=None, params=None):
        _, start, disp = await self._get_served_data(meta, device, params)

        remaining = start - disp
        unit = await self._get_vol_unit(meta, params=params)
        return from_ml(remaining, unit)

    async def _get_percent_remaining(self, meta, device=None, params=None):
        _max, start, disp = await self._get_served_data(meta, device, params)

        remaining = start - disp
        return round((remaining / _max) * 100, 2)

    async def _get_vol_unit(self, meta, params=None):
        self.logger.debug("meta: %s", meta)
        self.logger.debug("default_vol_unit: %s", self.default_vol_unit)
        return meta.get("unit", self.default_vol_unit).lower()


    async def _get_served_data(self, meta, device=None, params=None):
        self.logger.debug("retrieving served data.")
        if not device:
            device = await self._get(meta, params)
        port = self._get_port_data(device, meta, params=params)
        self.logger.debug("port data: %s", port)

        _max = port.get("volSize", 0)
        start = port.get("volStart", 0)
        disp = port.get("volDisp", 0)

        self.logger.debug("serve data: max = %s, start = %s, dispensed = %s", _max, start, disp)
        return _max, start, disp

    async def _get_from_key(self, key, meta, params=None):
        device = await self._get(meta, params)
        port = self._get_port_data(device, meta, params=params)

        return port.get(key, None)

    def _get_port_data(self, device, meta, params=None):
        port_num = meta["port_num"]
        for port in device["ports"]:
            if port["num"] == port_num:
                return port

        return {}

    async def _get(self, meta, params=None) -> Dict:
        if not params:
            params = {}

        access_token = self._get_device_access_token(meta)
        params["access_token"] = access_token
        url = "https://mdash.net/api/v2/m/device"
        self.logger.debug("Retrieving device data for access token %s. GET Request: %s, params: %s", access_token, url, params)
        async with AsyncClient() as client:
            resp = await client.get(url, params=params)
            self.logger.debug("GET response code: %s", resp.status_code)
            j = resp.json()
            self.logger.debug("GET response JSON: %s", j)
            if resp.status_code == 401:
                self.logger.error("Kegtron API returned a 401")
                raise TapMonitorDependencyError(
                    MONITOR_TYPE,
                    message="Kegtron API returned a 401 unauthorized when retrieving device details.",
                )

            return self.parse_resp(j)

    def parse_resp(self, j) -> Dict:
        self.logger.debug("parsing kegtron pro response: %s", j)
        _id = j.get("id")
        self.logger.debug("id: %s", _id)
        shdw = j.get("shadow", {})
        self.logger.debug("shadow: %s", shdw)
        state = shdw.get("state", {})
        self.logger.debug("state: %s", state)
        rprtd = state.get("reported", {})
        self.logger.debug("reported: %s", rprtd)
        ota = rprtd.get("ota", {})
        self.logger.debug("ota: %s", ota)
        cfg = rprtd.get("config", {})
        self.logger.debug("config: %s", cfg)
        cfg_ro = rprtd.get("config_readonly", {})
        self.logger.debug("config_readonly: %s", cfg_ro)

        device = {
            "id": _id,
            "ota": ota.get("id"),
            "online": rprtd.get("online", False),
            "port_count": cfg_ro.get("portCount", 0),
            "temp": cfg_ro.get("temp"),
            "fw_rev": cfg_ro.get("fwRev"),
            "humidity": cfg_ro.get("humidity"),
            "hw_rev": cfg_ro.get("hwRev"),
            "model_num": cfg_ro.get("modelNum"),
            "mac": cfg_ro.get("macAddr"),
            "clean_active": cfg.get("cleanActive"),
            "site_name": cfg.get("siteName"),
            "beacon_enabled": cfg.get("beaconEna", False),
            "serial_num": cfg_ro.get("serialNum"),
        }
        self.logger.debug("device: %s", device)

        ports = []
        for i in range(device["port_count"]):
            port_key = f"port{i}"
            port = {"num": i, "key": port_key}
            self.logger.debug("port_num: %s", i)
            self.logger.debug("port key: %s", port_key)
            port_cfg = cfg.get(port_key)
            self.logger.debug("port config: %s", port_cfg)
            port_cfg_ro = cfg_ro.get(port_key)
            self.logger.debug("port config readonly: %s", port_cfg_ro)
            port.update(port_cfg_ro | port_cfg)
            self.logger.debug("port: %s", port)
            ports.append(port)

        device["ports"] = ports

        return device

    async def discover(self, params=None, **kwargs):
        if not params:
            params = {}
        kwargs = {}
        url = "https://mdash.net/customer"
        if self.kegtron_customer_api_key:
            self.logger.debug("Discovering kegtron pro devices - using customer api key auth")
            params["access_token"] = self.kegtron_customer_api_key
        else:
            self.logger.debug("Discovering kegtron pro devices - using username/password auth")
            kwargs["auth"] = BasicAuth(self.kegtron_username, self.kegtron_password)

        async with AsyncClient() as client:
            self.logger.debug("GET Request: %s, params: %s", url, params)
            resp = await client.get(url, params=params, **kwargs)
            self.logger.debug("GET response code: %s", resp.status_code)
            j = resp.json()
            self.logger.debug("GET response JSON: %s", j)
            if resp.status_code == 401:
                self.logger.error("Kegtron API returned a 401 when retrieving customer details to get the device access tokens")
                raise TapMonitorDependencyError(MONITOR_TYPE)

            device_keys = j.get("pubkeys", {})
            devices = []
            for key, _ in device_keys.items():
                device = await self._get({"access_token": key}, params)
                if device:
                    for port in device["ports"]:
                        _device = {
                            "id": f"{device['id']}",
                            "name": f"{device['site_name']}",
                            "model": device["model_num"],
                            "port_num": port["num"],
                            "token": key,
                        }
                        devices.append(_device)

            return devices

    async def update_device(self, data, monitor_id=None, monitor=None, meta=None, params=None, db_session=None):
        if not meta:
            meta = await self.extract_meta(monitor_id, monitor, meta, db_session)

        d_data = {}
        for k, v in data.items():
            if k in self.supported_device_keys:
                d_data[k] = v
            else:
                self.logger.warning("ignoring unsupported kegtron pro device data with key `%s`", k)
        data = {"shadow": {"state": {"desired": {"config": d_data}}}}
        return await self._update(data, meta, params=params)

    async def update_port(self, data, monitor_id=None, monitor=None, meta=None, params=None, db_session=None):
        if not meta:
            meta = await self.extract_meta(monitor_id, monitor, meta, db_session)

        port_num = meta.get("port_num")
        if port_num is None:
            raise ValueError("port_num not found in tap monitor metadata")

        p_data = {}
        for k, v in data.items():
            if k in self.supported_port_keys:
                p_data[k] = v
            else:
                self.logger.warning("ignoring unsupported kegtron pro device data with key `%s`", k)

        data = {"shadow": {"state": {"desired": {"config": {f"port{port_num}": p_data}}}}}
        return await self._update(data, meta, params=params)
    
    async def update_user_overrides(self, data, monitor_id=None, monitor=None, meta=None, params=None, db_session=None):
        if not meta:
            meta = await self.extract_meta(monitor_id, monitor, meta, db_session)

        port_num = meta.get("port_num")
        if port_num is None:
            raise ValueError("port_num not found in tap monitor metadata.  Meta: %s", meta)

        p_data = {}
        for k, v in data.items():
            if k in self.supported_port_user_override_keys:
                p_data[k] = v
            else:
                self.logger.warning("ignoring unsupported kegtron pro device data with key `%s`", k)

        data = {"state": {"config_readonly": {f"port{port_num}": p_data}}}
        return await self._update(data, meta, path="/rpc/Kegtron.UserOverride", params=params)
    
    async def reset_volume(self, monitor_id=None, monitor=None, meta=None, params=None, db_session=None):
        if not meta:
            meta = await self.extract_meta(monitor_id, monitor, meta, db_session)

        port_num = meta.get("port_num")
        if port_num is None:
            raise ValueError("port_num not found in tap monitor metadata")

        data = {"port": port_num}
        return await self._update(data, meta, path="/rpc/Kegtron.ResetVolume", params=params)
    
    async def reset_kegs_served(self, monitor_id=None, monitor=None, meta=None, params=None, db_session=None):
        if not meta:
            meta = await self.extract_meta(monitor_id, monitor, meta, db_session)

        port_num = meta.get("port_num")
        if port_num is None:
            raise ValueError("port_num not found in tap monitor metadata")

        data = {"port": port_num}
        return await self._update(data, meta, path="/rpc/Kegtron.ResetKegsServed", params=params)

    async def _update(self, data, meta, path="", params=None):
        if not params:
            params = {}
        access_token = self._get_device_access_token(meta)
        params["access_token"] = access_token
        url = f"https://mdash.net/api/v2/m/device{path}"
        self.logger.debug("POST Request: %s, params: %s, data: %s", url, params, data)
        async with AsyncClient() as client:
            resp = await client.post(url, json=data, params=params, timeout=10)
            self.logger.debug("GET response code: %s", resp.status_code)

            return resp.status_code == 200
