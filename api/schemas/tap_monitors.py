from typing import List, Optional

from pydantic import Field

from schemas.base import CamelCaseModel


class TapMonitorBase(CamelCaseModel):
    meta: Optional[dict] = None

    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        meta = data.get("meta")
        if meta:
            meta = self.transform_meta(meta)
            data["meta"] = meta
        return data


class TapMonitorCreate(TapMonitorBase):
    """Schema for creating a tap monitor"""

    name: str
    monitor_type: str
    location_id: str = None


class TapMonitorUpdate(TapMonitorBase):
    """Schema for updating a tap monitor"""

    name: Optional[str] = None
    monitor_type: Optional[str] = None
    location_id: Optional[str] = None


class TapMonitorTypeBase(CamelCaseModel):
    type: str
    supports_discovery: bool
    reports_online_status: bool