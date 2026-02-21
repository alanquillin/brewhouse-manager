"""Location service with business logic and transformations"""

from sqlalchemy.ext.asyncio import AsyncSession

from lib import logging
from services.base import transform_dict_to_camel_case

LOGGER = logging.getLogger(__name__)


class LocationService:
    """Service for location-related operations"""

    @staticmethod
    async def transform_response(location, **kwargs):
        """Transform location model to response dict with camelCase keys"""
        if not location:
            return None

        data = location.to_dict()
        return transform_dict_to_camel_case(data)
