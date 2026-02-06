"""FastAPI routers"""

from typing import Optional

from pydantic import BaseModel

# Import routers as they are created
from . import assets, auth, batches, beers, beverages, dashboard, external_brew_tools, image_transitions, locations, pages, settings, tap_monitors, taps, users

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
    "plaato",
]


class StringValueRequest(BaseModel):
    value: str
