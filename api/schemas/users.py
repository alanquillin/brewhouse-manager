from typing import List, Optional

from pydantic import Field

from schemas.base import CamelCaseModel


class UserBase(CamelCaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    admin: Optional[bool] = None
    password: Optional[str] = None


class UserCreate(UserBase):
    """Schema for creating a user"""

    email: str


class UserUpdate(UserBase):
    """Schema for updating a user"""

    email: Optional[str] = None


class UserLocationsUpdate(CamelCaseModel):
    """Schema for updating user locations"""

    location_ids: List[str]
