import uuid
from datetime import datetime
from typing import Optional

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


class TapMonitorResponse(TapMonitorBase):
    id: uuid.UUID
    name: str
    monitor_type: str
    location_id: Optional[uuid.UUID] = None
    location: Optional[dict] = None
    reports_online_status: Optional[bool] = None


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


class TapMonitorData(CamelCaseModel):
    percent_remaining: Optional[float] = None
    total_volume_remaining: Optional[float] = None
    display_volume_unit: Optional[str] = None
    firmware_version: Optional[str] = None
    last_updated_on: Optional[float] = None
    online: Optional[bool] = None
