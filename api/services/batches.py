"""Batch service with business logic and transformations"""

import logging
from datetime import datetime, timedelta, date

from sqlalchemy.ext.asyncio import AsyncSession

from db.taps import Taps as TapsDB
from lib.config import Config
from lib.external_brew_tools import get_tool as get_external_brewing_tool
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
            taps = await TapsDB.query(db_session, batch_id=batch.id)
            if taps:
                from services.taps import TapService

                data["taps"] = [await TapService.transform_tap_response(tap, db_session=db_session) for tap in taps]

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
                    refresh_reason = ex_details.get(
                        "_refresh_reason", "The batch was marked by the external brewing tool for refresh, reason unknown."
                    )

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
                    ex_details = tool.get_batch_details(batch=batch)
                    if ex_details:
                        ex_details["_last_refreshed_on"] = now.isoformat()
                        LOGGER.debug("Extended batch details: %s, updating database", ex_details)
                        from db.batches import Batches as BatchesDB

                        await BatchesDB.update(db_session, batch.id, external_brewing_tool_meta={**meta, "details": ex_details})
                        data["external_brewing_tool_meta"] = {**meta, "details": ex_details}
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
