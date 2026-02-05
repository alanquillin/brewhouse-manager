"""Tap monitor service with business logic and transformations"""
from typing import Dict
from sqlalchemy.ext.asyncio import AsyncSession

from lib import logging
from services.base import transform_dict_to_camel_case

LOGGER = logging.getLogger(__name__)


class TapMonitorService:
    """Service for tap monitor-related operations"""

    @staticmethod
    async def transform_response(tap_monitor, db_session: AsyncSession, include_location=True, include_tap=False, **kwargs):
        """Transform tap monitor model to response dict with camelCase keys"""
        if not tap_monitor:
            return None

        data = tap_monitor.to_dict()

        # Include location if requested
        if include_location:
            await tap_monitor.awaitable_attrs.location
            if tap_monitor.location:
                from services.locations import LocationService

                data["location"] = await LocationService.transform_response(tap_monitor.location, db_session=db_session)

        if include_tap:
            from db.taps import Taps as TapsDB
            from services.taps import TapService
            taps = await TapsDB.query(db_session, tap_monitor_id=tap_monitor.id)
            if taps:
                tap = taps[0] # Only one tap can be associated with a tap monitor
                data["tap"] = await TapService.transform_response(tap, db_session, include_location=False)

        return transform_dict_to_camel_case(data)

class TapMonitorTypeService:
    """Service for tap monitor-related operations"""

    @staticmethod
    async def transform_response(data: Dict, **kwargs):
        """Transform tap monitor model to response dict with camelCase keys"""
        if not data:
            return None
        
        return transform_dict_to_camel_case(data)