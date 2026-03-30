import base64
from typing import Any, Dict, List

from httpx import AsyncClient

from lib.tap_monitors import TapMonitorBase
from lib.tap_monitors.exceptions import TapMonitorDependencyError

MONITOR_TYPE = "kegtron-gen1"


def _require_gen1_base_url(base_url: str | None) -> None:
    if not base_url:
        raise TapMonitorDependencyError(
            MONITOR_TYPE,
            message="Kegtron Gen1 API base URL is not configured (tap_monitors.kegtron.gen1.base_url).",
        )


class KegtronGen1(TapMonitorBase):
    def __init__(self) -> None:
        super().__init__()
        self.monitor_data_included = True

        self._data_type_to_key = {
            "percent_beer_remaining": self._get_percent_remaining,
            "total_beer_remaining": self._get_total_remaining,
            "beer_remaining_unit": self._get_vol_unit,
        }

        self.default_vol_unit = self.config.get("tap_monitors.preferred_vol_unit")
        self.base_url = self.config.get("tap_monitors.kegtron.gen1.base_url")
        api_key = self.config.get("tap_monitors.kegtron.gen1.api_key")
        self.bearer_token = base64.b64encode(api_key.encode("ascii")).decode("ascii") if api_key else None
        self.insecure = self.config.get("tap_monitors.kegtron.gen1.insecure")
        self.client_args = {}
        if self.insecure and self.base_url and self.base_url.startswith("https"):
            self.client_args["verify"] = False

    @staticmethod
    def supports_discovery():
        return True

    @staticmethod
    def reports_online_status():
        return True

    async def is_online(self, monitor_id=None, monitor=None, meta=None, db_session=None, **kwargs) -> bool:
        if not meta:
            meta = await self.extract_meta(monitor_id, monitor, meta, db_session)

        _require_gen1_base_url(self.base_url)

        device_id = meta.get("device_id")
        url = f"{self.base_url}/api/v1/devices/{device_id}/online"
        self.logger.debug("GET Request: %s", url)

        async with AsyncClient(**self.client_args) as client:
            resp = await client.get(url, timeout=10)
            self.logger.debug("GET response code: %s", resp.status_code)

            if resp.status_code == 404:
                raise TapMonitorDependencyError(
                    MONITOR_TYPE,
                    message=f"Kegtron Gen1 device '{device_id}' not found.",
                )
            if resp.status_code != 200:
                self.logger.error("Kegtron Gen1 API returned HTTP %s", resp.status_code)
                raise TapMonitorDependencyError(
                    MONITOR_TYPE,
                    message=f"Kegtron Gen1 API returned HTTP {resp.status_code}",
                )

            j = resp.json()
            self.logger.debug("GET response JSON: %s", j)
            return j.get("online", False)

    async def get(self, data_type, monitor_id=None, monitor=None, meta=None, db_session=None, **kwargs) -> Any:
        if not meta:
            meta = await self.extract_meta(monitor_id, monitor, meta, db_session)

        fn = self._data_type_to_key.get(data_type)
        if not fn:
            from lib.tap_monitors import InvalidDataType

            raise InvalidDataType(data_type)

        if callable(fn):
            return await fn(meta)

        return await self._get_from_key(fn, meta)

    async def get_all(self, monitor_id=None, monitor=None, meta=None, db_session=None, **kwargs) -> Dict:
        if not meta:
            meta = await self.extract_meta(monitor_id, monitor, meta, db_session)

        device = await self._get_device(meta)
        port = self._get_port_data(device, meta)

        return {
            "percentRemaining": self._calc_percent_remaining(port),
            "totalVolumeRemaining": self._calc_total_remaining(port),
            "displayVolumeUnit": self._get_display_unit(port),
            "onlineStatusType": "async",
        }

    async def discover(self, params=None, **kwargs) -> List[Dict]:
        devices = await self._list_devices()
        result = []
        for device in devices:
            ports = device.get("ports", {})
            for port_index_str, _ in ports.items():
                port_index = int(port_index_str)
                result.append(
                    {
                        "id": device["id"],
                        "name": device.get("name", "Unknown"),
                        "model": device.get("model", "Unknown"),
                        "port_num": port_index,
                    }
                )
        return result

    async def reset_volume(self, keg_size, start_volume, unit, monitor_id=None, monitor=None, meta=None, db_session=None):
        if not meta:
            meta = await self.extract_meta(monitor_id, monitor, meta, db_session)

        device_id = meta.get("device_id")
        port_index = meta.get("port_index")

        if device_id is None or port_index is None:
            raise ValueError("device_id and port_index must be in tap monitor metadata")

        _require_gen1_base_url(self.base_url)
        if not self.bearer_token:
            raise TapMonitorDependencyError(
                MONITOR_TYPE,
                message="Kegtron Gen1 API key is not configured (tap_monitors.kegtron.gen1.api_key).",
            )

        url = f"{self.base_url}/api/v1/devices/{device_id}/port/{port_index}/rpc/Kegtron.ResetVolume"
        data = {
            "kegSize": keg_size,
            "startVolume": start_volume,
            "unit": unit,
        }

        self.logger.debug("POST Request: %s, data: %s", url, data)
        headers = {"Authorization": f"Bearer {self.bearer_token}"}

        async with AsyncClient(**self.client_args) as client:
            resp = await client.post(url, json=data, headers=headers, timeout=10)
            self.logger.debug("POST response code: %s", resp.status_code)

            if resp.status_code == 401:
                raise TapMonitorDependencyError(
                    MONITOR_TYPE,
                    message="Kegtron Gen1 API returned a 401 unauthorized when resetting volume.",
                )
            if resp.status_code != 200:
                raise TapMonitorDependencyError(
                    MONITOR_TYPE,
                    message=f"Kegtron Gen1 API returned HTTP {resp.status_code} when resetting volume.",
                )

            return True

    async def _list_devices(self) -> List[Dict]:
        _require_gen1_base_url(self.base_url)

        url = f"{self.base_url}/api/v1/devices"
        self.logger.debug("GET Request: %s", url)

        async with AsyncClient(**self.client_args) as client:
            resp = await client.get(url, timeout=10)
            self.logger.debug("GET response code: %s", resp.status_code)

            if resp.status_code != 200:
                self.logger.error("Kegtron Gen1 API returned HTTP %s", resp.status_code)
                raise TapMonitorDependencyError(
                    MONITOR_TYPE,
                    message=f"Kegtron Gen1 API returned HTTP {resp.status_code} when listing devices.",
                )

            j = resp.json()
            self.logger.debug("GET response JSON: %s", j)
            return j

    async def _get_device(self, meta) -> Dict:
        _require_gen1_base_url(self.base_url)

        device_id = meta.get("device_id")
        url = f"{self.base_url}/api/v1/devices/{device_id}"
        self.logger.debug("GET Request: %s", url)

        async with AsyncClient(**self.client_args) as client:
            resp = await client.get(url, timeout=10)
            self.logger.debug("GET response code: %s", resp.status_code)

            if resp.status_code == 404:
                raise TapMonitorDependencyError(
                    MONITOR_TYPE,
                    message=f"Kegtron Gen1 device '{device_id}' not found.",
                )
            if resp.status_code != 200:
                self.logger.error("Kegtron Gen1 API returned HTTP %s", resp.status_code)
                raise TapMonitorDependencyError(
                    MONITOR_TYPE,
                    message=f"Kegtron Gen1 API returned HTTP {resp.status_code}",
                )

            j = resp.json()
            self.logger.debug("GET response JSON: %s", j)
            return j

    def _get_port_data(self, device, meta) -> Dict:
        port_index = meta.get("port_index")
        ports = device.get("ports", {})
        port = ports.get(str(port_index))
        if not port:
            self.logger.warning("Port %s not found on device %s", port_index, device.get("id"))
            return {}
        return port

    def _calc_percent_remaining(self, port) -> float:
        keg_size = port.get("kegSize", 0)
        if keg_size == 0:
            return 0.0

        volume_dispensed = port.get("volumeDispensed", 0)
        start_volume = port.get("startVolume", keg_size)
        remaining = start_volume - volume_dispensed
        return round((remaining / keg_size) * 100, 2)

    def _calc_total_remaining(self, port) -> float:
        volume_dispensed = port.get("volumeDispensed", 0)
        start_volume = port.get("startVolume", 0)
        remaining = start_volume - volume_dispensed
        return round(remaining, 2)

    def _get_display_unit(self, port) -> str:
        return port.get("displayUnit", self.default_vol_unit or "gal").lower()

    async def _get_percent_remaining(self, meta, device=None):
        if not device:
            device = await self._get_device(meta)
        port = self._get_port_data(device, meta)
        return self._calc_percent_remaining(port)

    async def _get_total_remaining(self, meta, device=None):
        if not device:
            device = await self._get_device(meta)
        port = self._get_port_data(device, meta)
        return self._calc_total_remaining(port)

    async def _get_vol_unit(self, meta, device=None):
        if not device:
            device = await self._get_device(meta)
        port = self._get_port_data(device, meta)
        return self._get_display_unit(port)

    async def _get_from_key(self, key, meta):
        device = await self._get_device(meta)
        port = self._get_port_data(device, meta)
        return port.get(key)
