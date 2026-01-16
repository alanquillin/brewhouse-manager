"""Tap service with business logic and transformations"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession

from services.base import transform_dict_to_camel_case

LOGGER = logging.getLogger(__name__)


class TapService:
    """Service for tap-related operations"""

    @staticmethod
    async def transform_tap_response(tap, db_session: AsyncSession):
        """Transform tap for inclusion in batch response"""
        data = tap.to_dict()

        if tap.location:
            from services.locations import LocationService

            data["location"] = await LocationService.transform_response(tap.location, db_session=db_session)

        return transform_dict_to_camel_case(data)

    @staticmethod
    async def transform_response(tap, db_session: AsyncSession, include_location=True, **kwargs):
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
                    batch.beer,
                    db_session=db_session,
                    skip_meta_refresh=True,
                    include_batches=False,
                    include_location=False
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

        # Include sensor
        await tap.awaitable_attrs.sensor
        if tap.sensor:
            from services.sensors import SensorService

            data["sensor"] = await SensorService.transform_response(tap.sensor, db_session=db_session, include_location=False)

        # Remove on_tap_id from response
        if "on_tap_id" in data:
            del data["on_tap_id"]

        return transform_dict_to_camel_case(data)
