from typing import List, Optional

from pydantic import Field

from schemas.base import CamelCaseModel


class LocationBase(CamelCaseModel):
    description: Optional[str] = None


class LocationCreate(LocationBase):
    """Schema for creating a location"""

    name: str


class LocationUpdate(LocationBase):
    """Schema for updating a location"""

    name: Optional[str] = None
