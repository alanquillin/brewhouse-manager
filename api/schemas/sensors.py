from typing import List, Optional
from pydantic import Field

from schemas.base import CamelCaseModel

class SensorBase(CamelCaseModel):
    meta: Optional[dict] = None

    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        meta = data.get("meta")
        if meta:
            meta = self.transform_meta(meta)
            data["meta"] = meta
        return data

class SensorCreate(SensorBase):
    """Schema for creating a sensor"""

    name: str
    sensor_type: str
    location_id: str = None

class SensorUpdate(SensorBase):
    """Schema for updating a sensor"""

    name: Optional[str] = None
    sensor_type: Optional[str] = None
    location_id: Optional[str] = None