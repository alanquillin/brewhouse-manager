"""Batch service with business logic and transformations"""

from datetime import date, datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.taps import Taps as TapsDB
from lib import logging
from lib.config import Config
from lib.external_brew_tools import get_tool as get_external_brewing_tool
from lib.external_brew_tools.exceptions import ResourceNotFoundError
from lib.time import parse_iso8601_utc, utcnow_aware
from services.base import transform_dict_to_camel_case

LOGGER = logging.getLogger(__name__)
CONFIG = Config()


class BatchService:
    """Service for batch-related operations"""

    @staticmethod
    async def transform_response(
        batch,
        db_session: AsyncSession,
        skip_meta_refresh=False,
        include_location=True,
        include_tap_details=False,
        force_refresh=False,
        **kwargs,
    ):
        """Transform batch model to response dict with camelCase keys"""
        if not batch:
            return None

        data = batch.to_dict()

        # Handle locations
        locations = []
        location_ids = []
        await batch.awaitable_attrs.locations
        if batch.locations:
            location_ids = [l.id for l in batch.locations]
            if include_location:
                from services.locations import LocationService

                locations = [await LocationService.transform_response(l, db_session=db_session) for l in batch.locations]

        data["locationIds"] = location_ids
        data["locations"] = locations

        # Include tap details if requested
        if include_tap_details:
            taps = await TapsDB.get_by_batch(db_session, batch_id=batch.id)
            if taps:
                from services.taps import TapService

                data["taps"] = [await TapService.transform_tap_response(tap, db_session=db_session, include_tap_monitor=True) for tap in taps]

        # Refresh external brewing tool metadata if needed
        if not skip_meta_refresh:
            tool_type = batch.external_brewing_tool
            meta = data.get("external_brewing_tool_meta", {})

            if tool_type and meta:
                refresh_data = False
                refresh_reason = "UNKNOWN"
                refresh_buffer = CONFIG.get(f"external_brew_tools.{tool_type}.refresh_buffer_sec.soft")
                now = utcnow_aware()

                ex_details = meta.get("details", {})

                if not ex_details:
                    refresh_data = True
                    refresh_reason = "No cached details exist in DB."
                elif force_refresh:
                    refresh_data = True
                    refresh_reason = "Forced refresh requested via query string parameter."
                elif ex_details.get("_refresh_on_next_check", False):
                    refresh_data = True
                    refresh_reason = ex_details.get("_refresh_reason", "The batch was marked by the external brewing tool for refresh, reason unknown.")

                if not refresh_data:
                    last_refresh = ex_details.get("_last_refreshed_on")
                    if last_refresh:
                        skip_until = parse_iso8601_utc(last_refresh) + timedelta(seconds=refresh_buffer)

                        LOGGER.debug("Checking is last refresh date '%s' > now '%s'", skip_until.isoformat(), now.isoformat())
                        if skip_until < now:
                            LOGGER.info(
                                "Refresh skip buffer exceeded, refreshing data. Tool: %s, batch_id: %s, skip_until: %s",
                                tool_type,
                                batch.id,
                                skip_until.isoformat(),
                            )
                            refresh_data = True
                            refresh_reason = "Refresh skip buffer exceeded"
                    else:
                        refresh_data = True
                        refresh_reason = "No _last_refreshed_on date recorded, refreshing."

                if refresh_data:
                    LOGGER.info("Refreshing data from %s for %s. Reason: %s", tool_type, batch.id, refresh_reason)
                    tool = get_external_brewing_tool(tool_type)
                    ex_details = await tool.get_batch_details(batch=batch)
                    if ex_details:
                        u_meta = BatchService.store_metadata(meta, ex_details, now=now)
                        LOGGER.debug(f"Updated brew tool metadata: {u_meta}, updating database")
                        from db.batches import Batches as BatchesDB

                        await BatchesDB.update(db_session, batch.id, external_brewing_tool_meta=u_meta)
                        data["external_brewing_tool_meta"] = u_meta
                    else:
                        LOGGER.warning(
                            "There was an error or no details from %s for %s",
                            tool_type,
                            {k: v for k, v in meta.items() if k != "details"},
                        )

        # Convert dates to timestamps
        for k in ["brew_date", "keg_date", "archived_on"]:
            d = data.get(k)
            if d and isinstance(d, date):
                data[k] = datetime.timestamp(datetime.fromordinal(d.toordinal()))

        return transform_dict_to_camel_case(data)

    @staticmethod
    async def can_user_see_batch(user, batch=None, location_ids=None):
        """Check if user has access to batch based on locations"""
        if user.admin:
            return True

        if batch:
            await batch.awaitable_attrs.locations
            location_ids = [l.id for l in batch.locations]

        if not location_ids:
            return False

        for id in location_ids:
            if id in user.locations:
                return True

        return False

    @staticmethod
    async def verify_and_update_external_brew_tool_batch(request_data):
        LOGGER.debug("Checking if the beer is associated with an external brew tool and verifying data")
        tool_type = request_data.get("external_brewing_tool")
        if tool_type:
            meta = request_data.get("external_brewing_tool_meta", {})
            LOGGER.debug(f"Beer is associated with {tool_type} batch.  Metadata: {meta}.  Verifying...")
            batch_id = meta.get("batch_id")
            if not batch_id:
                raise HTTPException(status_code=400, detail=f"batch id is required when external brewing tool is set, but was not provided")
            LOGGER.debug(f"Checking {tool_type} for batch with id: {batch_id}.")
            tool = get_external_brewing_tool(tool_type)
            try:
                data = await tool.get_batch_details(meta=meta)
                if not data:
                    LOGGER.error(f"{tool_type} did not return data for batch id: {batch_id}.")
                    raise HTTPException(status_code=400, detail=f"{tool_type} return no data for batch with id '{batch_id}'")
                data["_last_refreshed_on"] = utcnow_aware().isoformat()
                request_data["external_brewing_tool_meta"] = BatchService.store_metadata(meta, data)
            except ResourceNotFoundError:
                LOGGER.error(f"{tool_type} returned a 404 for batch id: {batch_id}.")
                raise HTTPException(status_code=400, detail=f"{tool_type} batch with id '{batch_id}' not found")
        return request_data

    @staticmethod
    def store_metadata(metadata, ex_details, now=None):
        if not now:
            now = utcnow_aware()
        ex_details["_last_refreshed_on"] = now.isoformat()
        return {**metadata, "details": ex_details}
