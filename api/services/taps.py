"""Tap service with business logic and transformations"""

from sqlalchemy.ext.asyncio import AsyncSession

from lib import logging
from lib.tap_monitors import get_tap_monitor_lib
from services.base import transform_dict_to_camel_case

LOGGER = logging.getLogger(__name__)


class TapService:
    """Service for tap-related operations"""

    @staticmethod
    async def transform_tap_response(tap, db_session: AsyncSession, include_location=True, include_tap_monitor=False):
        """Transform tap for inclusion in dependent object response"""
        data = tap.to_dict()

        if include_location:
            await tap.awaitable_attrs.location
            if tap.location:
                from services.locations import LocationService

                data["location"] = await LocationService.transform_response(tap.location, db_session=db_session)

        if include_tap_monitor:
            await tap.awaitable_attrs.tap_monitor
            if tap.tap_monitor:
                from services.tap_monitors import TapMonitorService

                data["tap_monitor"] = await TapMonitorService.transform_response(tap.tap_monitor, db_session=db_session, include_location=False)

        return transform_dict_to_camel_case(data)

    @staticmethod
    async def transform_response(tap, db_session: AsyncSession, include_location=True, filter_unsupported_tap_monitor=False, **kwargs):
        """Transform tap model to response dict with camelCase keys"""
        if not tap:
            return None

        data = tap.to_dict()

        # Include on_tap information with batch, beer, and beverage details
        await tap.awaitable_attrs.on_tap
        if tap.on_tap:
            from services.batches import BatchService

            on_tap = tap.on_tap
            await on_tap.awaitable_attrs.batch
            batch = on_tap.batch
            data["batch"] = await BatchService.transform_response(batch, db_session=db_session, include_location=False)
            data["batch_id"] = on_tap.batch_id

            await batch.awaitable_attrs.beer
            if batch.beer:
                from services.beers import BeerService

                data["beer"] = await BeerService.transform_response(
                    batch.beer, db_session=db_session, skip_meta_refresh=True, include_batches=False, include_location=False
                )
                data["beer_id"] = batch.beer_id

            await batch.awaitable_attrs.beverage
            if batch.beverage:
                from services.beverages import BeverageService

                data["beverage"] = await BeverageService.transform_response(
                    batch.beverage, db_session=db_session, include_batches=False, include_location=False
                )
                data["beverage_id"] = batch.beverage_id

        # Include location
        if include_location:
            await tap.awaitable_attrs.location
            if tap.location:
                from services.locations import LocationService

                data["location"] = await LocationService.transform_response(tap.location, db_session=db_session)

        # Include tap monitor
        await tap.awaitable_attrs.tap_monitor
        if tap.tap_monitor:
            from services.tap_monitors import TapMonitorService

            tap_monitor_resp = await TapMonitorService.transform_response(tap.tap_monitor, db_session=db_session, include_location=False)
            tap_monitor_lib = get_tap_monitor_lib(tap.tap_monitor.monitor_type)
            if filter_unsupported_tap_monitor:
                if not tap_monitor_lib:
                    if "tap_monitor_id" in data:
                        del data["tap_monitor_id"]
                    LOGGER.warning("Unsupported tap monitor type: %s", tap.tap_monitor.monitor_type)
                else:
                    data["tap_monitor"] = tap_monitor_resp
            else:
                if not tap_monitor_lib:
                    tap_monitor_resp["error"] = f"Unsupported tap monitor type: {tap.tap_monitor.monitor_type}"
                data["tap_monitor"] = tap_monitor_resp

        # Remove on_tap_id from response
        if "on_tap_id" in data:
            del data["on_tap_id"]

        return transform_dict_to_camel_case(data)
