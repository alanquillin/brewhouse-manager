"""Sensor service with business logic and transformations"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from services.base import transform_dict_to_camel_case

LOGGER = logging.getLogger(__name__)


class SensorService:
    """Service for sensor-related operations"""

    @staticmethod
    async def transform_response(sensor, db_session: AsyncSession, include_location=True, include_tap=False, **kwargs):
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

        if include_tap:
            from db.taps import Taps as TapsDB
            from services.taps import TapService
            taps = await TapsDB.query(db_session, sensor_id=sensor.id)
            if taps:
                tap = taps[0] #there can only be 1
                data["tap"] = await TapService.transform_response(tap, db_session, include_location=False)

        return transform_dict_to_camel_case(data)
