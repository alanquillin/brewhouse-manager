import base64

import httpx
from httpx import BasicAuth, AsyncClient

from db import async_session_scope
from db.tap_monitors import TapMonitors as TapMonitorsDB
from lib.tap_monitors import TapMonitorBase
from lib.units import from_ml
from lib.tap_monitors.exceptions import TapMonitorDependencyError


class KegtronBase(TapMonitorBase):
    def __init__(self):
        super().__init__()


MONITOR_TYPE = "kegtron-pro"


class KegtronPro(TapMonitorBase):
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

    def __init__(self) -> None:
        super().__init__()
        self.monitor_data_included = True

        self._data_type_to_key = {
            "percent_beer_remaining": self._get_percent_remaining,
            "total_beer_remaining": self._get_total_remaining,
            "beer_remaining_unit": self._get_vol_unit,
        }

        self.default_vol_unit = self.config.get("tap_monitors.preferred_vol_unit")
        self.kegtron_customer_api_key = self.config.get(
            "tap_monitors.kegtron.pro.auth.customer_api_key"
        )
        self.kegtron_username = self.config.get("tap_monitors.kegtron.pro.auth.username")
        self.kegtron_password = self.config.get("tap_monitors.kegtron.pro.auth.password")

    def supports_discovery(self):
        return True

    async def get(self, data_type, monitor_id=None, monitor=None, meta=None, **kwargs):
        if not monitor_id and not monitor and not meta:
            raise Exception("monitor_id, monitor, or meta must be provided")

        if not meta:
            if not monitor:
                with async_session_scope(self.config) as db_session:
                    monitor = await TapMonitorsDB.get_by_pkey(db_session, monitor_id)
            meta = monitor.meta

        fn = self._data_type_to_key[data_type]

        if callable(fn):
            return await fn(meta)

        return self._get_from_key(fn, meta)

    def _get_device_access_token(self, meta):
        return meta.get("access_token")

    async def _get_total_remaining(self, meta, params=None):
        _, start, disp = await self._get_served_data(meta, params)

        remaining = start - disp
        unit = await self._get_vol_unit(meta, params=params)
        return from_ml(remaining, unit)

    async def _get_percent_remaining(self, meta, params=None):
        max, start, disp = await self._get_served_data(meta, params)

        remaining = start - disp
        return round((remaining / max) * 100, 2)

    async def _get_vol_unit(self, meta, params=None):
        self.logger.debug(f"meta: {meta}")
        self.logger.debug(f"default_vol_unit: {self.default_vol_unit}")
        return meta.get("unit", self.default_vol_unit).lower()

    async def _get_served_data(self, meta, params=None):
        self.logger.debug("retrieving served data.")
        device = await self._get(meta, params)
        port = self._get_port_data(device, meta, params=params)
        self.logger.debug(f"port data: {port}")

        max = port.get("volSize", 0)
        start = port.get("volStart", 0)
        disp = port.get("volDisp", 0)

        self.logger.debug(
            f"serve data: max = {max}, start = {start}, dispensed = {disp}"
        )
        return max, start, disp

    def _get_from_key(self, key, meta, params=None):
        device = self._get(meta, params)
        port = self._get_port_data(device, meta, params=params)

        return port.get(key, None)

    def _get_port_data(self, device, meta, params=None):
        port_num = meta["port_num"]
        for port in device["ports"]:
            if port["num"] == port_num:
                return port

        return {}

    async def _get(self, meta, params=None):
        if not params:
            params = {}

        access_token = self._get_device_access_token(meta)
        params["access_token"] = access_token
        url = "https://mdash.net/api/v2/m/device"
        self.logger.debug(
            f"Retriving devive data for access token {access_token}. GET Request: {url}, params: {params}"
        )
        async with AsyncClient() as client:
            resp = await client.get(url, params=params)
            self.logger.debug("GET response code: %s", resp.status_code)
            j = resp.json()
            self.logger.debug("GET response JSON: %s", j)
            if resp.status_code == 401:
                self.logger.error("Kegtron API returned a 401")
                raise TapMonitorDependencyError(
                    MONITOR_TYPE,
                    message=f"Kegtron API returned a 401 unauthorized when retrieving device details.",
                )

            return self.parse_resp(j)

    def parse_resp(self, j):
        self.logger.debug(f"parsing kegtron pro response: {j}")
        id = j.get("id")
        self.logger.debug(f"id: {id}")
        shdw = j.get("shadow", {})
        self.logger.debug(f"shadow: {shdw}")
        state = shdw.get("state", {})
        self.logger.debug(f"state: {state}")
        rprtd = state.get("reported", {})
        self.logger.debug(f"reported: {rprtd}")
        ota = rprtd.get("ota", {})
        self.logger.debug(f"ota: {ota}")
        cfg = rprtd.get("config", {})
        self.logger.debug(f"config: {cfg}")
        cfg_ro = rprtd.get("config_readonly", {})
        self.logger.debug(f"config_readonly: {cfg_ro}")

        device = {
            "id": id,
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
        self.logger.debug(f"device: {device}")

        ports = []
        for i in range(device["port_count"]):
            port_key = f"port{i}"
            port = {"num": i, "key": port_key}
            self.logger.debug(f"port_num: {i}")
            self.logger.debug(f"port key: {port_key}")
            port_cfg = cfg.get(port_key)
            self.logger.debug(f"port config: {port_cfg}")
            port_cfg_ro = cfg_ro.get(port_key)
            self.logger.debug(f"port config readonly: {port_cfg_ro}")
            port.update(port_cfg_ro | port_cfg)
            self.logger.debug(f"port: {port}")
            ports.append(port)

        device["ports"] = ports

        return device

    async def discover(self, params=None, **kwargs):
        if not params:
            params = {}
        kwargs = {}
        url = "https://mdash.net/customer"
        if self.kegtron_customer_api_key:
            self.logger.debug(
                "Discovering kegtron pro devices - using customer api key auth"
            )
            params["access_token"] = self.kegtron_customer_api_key
        else:
            self.logger.debug(
                "Discovering kegtron pro devices - using username/password auth"
            )
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

    async def update_device(
        self, data, monitor_id=None, monitor=None, meta=None, params=None
    ):
        if not monitor_id and not monitor and not meta:
            raise Exception("WTH!!")

        if not meta:
            if not monitor:
                with async_session_scope(self.config) as db_session:
                    monitor = await TapMonitorsDB.get_by_pkey(db_session, monitor_id)
            meta = monitor.meta

        d_data = {}
        for k, v in data.items():
            if k in self.supported_device_keys:
                d_data[k] = v
            else:
                self.warn(
                    f"ignoring unsupported kegtron pro device data with key `{k}`"
                )
        data = {"shadow": {"state": {"desired": {"config": d_data}}}}
        return await self._update(data, meta, params)

    async def update_port(
        self, port_num, data, monitor_id=None, monitor=None, meta=None, params=None
    ):
        if not monitor_id and not monitor and not meta:
            raise Exception("WTH!!")

        if not meta:
            if not monitor:
                with async_session_scope(self.config) as db_session:
                    monitor = await TapMonitorsDB.get_by_pkey(db_session, monitor_id)
            meta = monitor.meta
        port_num = meta.get("port_num")
        if not port_num:
            raise Exception("Port num not found... WTH!?!?!")

        p_data = {}
        for k, v in data.items():
            if k in self.supported_port_keys:
                p_data[k] = v
            else:
                self.warn(
                    f"ignoring unsupported kegtron pro device data with key `{k}`"
                )

        data = {
            "shadow": {"state": {"desired": {"config": {f"port{port_num}": p_data}}}}
        }
        return await self._update(data, meta, params)

    async def _update(self, data, meta, params=None):
        if not params:
            params = {}
        access_token = self._get_device_access_token(meta)
        params["access_token"] = access_token
        url = "https://mdash.net/api/v2/m/device"
        self.logger.debug("GET Request: %s, params: %s", url, params)
        async with AsyncClient() as client:
            resp = await client.post(url, json=data, params=params)
            self.logger.debug("GET response code: %s", resp.status_code)

            return resp.status_code == 200
