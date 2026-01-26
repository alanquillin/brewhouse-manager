"""FastAPI routers"""

# Import routers as they are created
from . import (
    auth, beers, beverages, batches, locations, sensors, taps, users,
    dashboard, assets, settings, external_brew_tools, image_transitions,
    pages
)

__all__ = [
    "auth", "beers", "beverages", "batches", "locations", "sensors", "taps", "users",
    "dashboard", "assets", "settings", "external_brew_tools", "image_transitions",
    "pages"
]
