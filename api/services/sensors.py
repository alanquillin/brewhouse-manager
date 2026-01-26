"""Sensor service with business logic and transformations"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from services.base import transform_dict_to_camel_case

LOGGER = logging.getLogger(__name__)


class SensorService:
    """Service for sensor-related operations"""

    @staticmethod
    async def transform_response(sensor, db_session: AsyncSession, include_location=True, **kwargs):
        """Transform sensor model to response dict with camelCase keys"""
        if not sensor:
            return None

        data = sensor.to_dict()

        # Include location if requested
        if include_location:
            await sensor.awaitable_attrs.location
            if sensor.location:
                from services.locations import LocationService

                data["location"] = await LocationService.transform_response(sensor.location, db_session=db_session)

        return transform_dict_to_camel_case(data)
