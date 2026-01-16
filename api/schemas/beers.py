"""Pydantic schemas for beers"""

from datetime import datetime
from typing import List, Optional
from pydantic import Field

from schemas.base import CamelCaseModel


class ImageTransition(CamelCaseModel):
    """Schema for image transitions"""

    id: Optional[str] = None
    image_url: Optional[str] = None
    duration: Optional[int] = None


class BeerBase(CamelCaseModel):
    """Base beer schema with common fields"""

    name: Optional[str] = None
    description: Optional[str] = None
    brewery: Optional[str] = None
    external_brewing_tool: Optional[str] = None
    external_brewing_tool_meta: Optional[dict] = None
    style: Optional[str] = None
    abv: Optional[float] = None
    ibu: Optional[float] = None
    srm: Optional[float] = None
    img_url: Optional[str] = None
    empty_img_url: Optional[str] = None
    untappd_id: Optional[str] = None
    image_transitions_enabled: Optional[bool] = None


class BeerCreate(BeerBase):
    """Schema for creating a beer"""

    image_transitions: Optional[List[ImageTransition]] = None


class BeerUpdate(BeerBase):
    """Schema for updating a beer"""

    image_transitions: Optional[List[ImageTransition]] = None


class BeerResponse(BeerBase):
    """Schema for beer responses"""

    id: str
    image_transitions: Optional[List[dict]] = None
    batches: Optional[List[dict]] = None
    created_on: datetime
    updated_on: datetime

    model_config = {"from_attributes": True}
