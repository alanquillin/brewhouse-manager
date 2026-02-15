"""FastAPI routers"""

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from lib import util

__all__ = [
    "auth",
    "beers",
    "beverages",
    "batches",
    "locations",
    "tap_monitors",
    "taps",
    "users",
    "dashboard",
    "assets",
    "settings",
    "external_brew_tools",
    "image_transitions",
    "pages",
    "plaato_keg",
    "kegtron",
]


class StringValueRequest(BaseModel):
    value: str


async def get_location_id(location_identifier: str, db_session: AsyncSession) -> str:
    """Get location ID from name or UUID"""
    if util.is_valid_uuid(location_identifier):
        return location_identifier

    from db.locations import Locations as LocationsDB

    locations = await LocationsDB.query(db_session, name=location_identifier)
    if locations:
        return locations[0].id

    return None
