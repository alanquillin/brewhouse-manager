"""Pydantic schemas for batches"""

from typing import List, Optional

from pydantic import Field

from schemas.base import CamelCaseModel


class BatchBase(CamelCaseModel):
    beer_id: Optional[str] = None
    beverage_id: Optional[str] = None
    name: Optional[str] = None
    brew_date: Optional[float] = None  # Unix timestamp
    keg_date: Optional[float] = None  # Unix timestamp
    abv: Optional[float] = None
    ibu: Optional[float] = None
    srm: Optional[float] = None
    archived_on: Optional[float] = None  # Unix timestamp
    external_brewing_tool: Optional[str] = None
    external_brewing_tool_meta: Optional[dict] = None
    location_ids: Optional[List[str]] = None
    img_url: Optional[str] = None
    batch_number: Optional[str] = None

    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        ext_brew_tool_meta = data.get("external_brewing_tool_meta")
        if ext_brew_tool_meta:
            ext_brew_tool_meta = self.transform_meta(ext_brew_tool_meta)
            data["external_brewing_tool_meta"] = ext_brew_tool_meta
        return data


class BatchCreate(BatchBase):
    """Schema for creating a batch"""


class BatchUpdate(BatchBase):
    """Schema for updating a batch"""
