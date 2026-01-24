"""Pydantic schemas for beverages"""

from datetime import datetime
from typing import List, Optional

from schemas.base import CamelCaseModel


class ImageTransition(CamelCaseModel):
    """Schema for image transitions"""

    id: Optional[str] = None
    image_url: Optional[str] = None
    duration: Optional[int] = None


class BeverageBase(CamelCaseModel):
    """Base beverage schema with common fields"""

    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    brewery: Optional[str] = None
    brewery_link: Optional[str] = None
    flavor: Optional[str] = None
    img_url: Optional[str] = None
    empty_img_url: Optional[str] = None
    image_transitions_enabled: Optional[bool] = None
    meta: Optional[dict] = None

    def model_dump(self, *args, **kwargs):
        data = super().model_dump(*args, **kwargs)
        meta = data.get("meta")
        if meta:
            meta = self.transform_meta(meta)
            data["meta"] = meta
        return data


class BeverageCreate(BeverageBase):
    """Schema for creating a beverage"""

    image_transitions: Optional[List[ImageTransition]] = None


class BeverageUpdate(BeverageBase):
    """Schema for updating a beverage"""

    image_transitions: Optional[List[ImageTransition]] = None


class BeverageResponse(BeverageBase):
    """Schema for beverage responses"""

    id: str
    image_transitions: Optional[List[dict]] = None
    batches: Optional[List[dict]] = None
    created_on: datetime
    updated_on: datetime

    model_config = {"from_attributes": True}
