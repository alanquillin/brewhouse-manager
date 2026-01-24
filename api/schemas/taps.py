from typing import List, Optional
from pydantic import Field

from schemas.base import CamelCaseModel

class TapBase(CamelCaseModel):
    sensor_id: Optional[str] = None
    batch_id: Optional[str] = None
    name_prefix: Optional[str] = None
    name_suffix: Optional[str] = None


class TapCreate(TapBase):
    """Schema for creating a tap"""

    description: str = None
    tap_number: int = None
    location_id: str = None

class TapUpdate(TapBase):
    """Schema for updating a tap"""

    description: Optional[str] = None
    tap_number: Optional[int] = None
    location_id: Optional[str] = None