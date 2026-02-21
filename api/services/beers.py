"""Beer service with business logic and transformations"""

from datetime import timedelta

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.beers import Beers as BeersDB
from db.image_transitions import ImageTransitions as ImageTransitionsDB
from lib import logging
from lib.config import Config
from lib.external_brew_tools import get_tool as get_external_brewing_tool
from lib.external_brew_tools.exceptions import ResourceNotFoundError
from lib.time import parse_iso8601_utc, utcnow_aware
from services.base import transform_dict_to_camel_case

LOGGER = logging.getLogger(__name__)
CONFIG = Config()


class BeerService:
    """Service for beer-related operations"""

    @staticmethod
    async def transform_response(
        beer,
        db_session: AsyncSession,
        skip_meta_refresh=False,
        include_batches=True,
        image_transitions=None,
        include_location=True,
        force_refresh=False,
        **kwargs,
    ):
        """Transform beer model to response dict with camelCase keys"""
        if not beer:
            return None

        data = beer.to_dict()

        # Include batches if requested
        if include_batches:
            await beer.awaitable_attrs.batches
            if beer.batches:
                from services.batches import BatchService

                data["batches"] = [
                    await BatchService.transform_response(
                        b,
                        db_session=db_session,
                        skip_meta_refresh=skip_meta_refresh,
                        include_location=include_location,
                    )
                    for b in beer.batches
                ]

        # Refresh external brewing tool metadata if needed
        if not skip_meta_refresh:
            tool_type = beer.external_brewing_tool
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
                        "_refresh_reason",
                        "The beer was marked by the external brewing tool for refresh, reason unknown.",
                    )

                if not refresh_data:
                    last_refresh = ex_details.get("_last_refreshed_on")
                    if last_refresh:
                        skip_until = parse_iso8601_utc(last_refresh) + timedelta(seconds=refresh_buffer)

                        LOGGER.debug(
                            "Checking is last refresh date '%s' > now '%s'",
                            skip_until.isoformat(),
                            now.isoformat(),
                        )
                        if skip_until < now:
                            LOGGER.info(
                                "Refresh skip buffer exceeded, refreshing data. Tool: %s, beer_id: %s, skip_until: %s",
                                tool_type,
                                beer.id,
                                skip_until.isoformat(),
                            )
                            refresh_data = True
                            refresh_reason = "Refresh skip buffer exceeded"
                    else:
                        refresh_data = True
                        refresh_reason = "No _last_refreshed_on date recorded, refreshing."

                if refresh_data:
                    LOGGER.info("Refreshing data from %s for %s. Reason: %s", tool_type, beer.id, refresh_reason)
                    tool = get_external_brewing_tool(tool_type)
                    try:
                        ex_details = await tool.get_recipe_details(beer=beer)
                    except ResourceNotFoundError:
                        ex_details["error"] = f"{tool_type} recipe could not be found"
                    if ex_details:
                        u_meta = BeerService.store_metadata(meta, ex_details, now=now)
                        LOGGER.debug(f"Updated brew tool metadata: {u_meta}, updating database")
                        await BeersDB.update(db_session, beer.id, external_brewing_tool_meta=u_meta)
                        data["external_brewing_tool_meta"] = u_meta
                    else:
                        LOGGER.warning(
                            "There was an error or no details from %s for %s",
                            tool_type,
                            {k: v for k, v in meta.items() if k != "details"},
                        )

        # Add image transitions
        if not image_transitions:
            image_transitions = await ImageTransitionsDB.query(db_session, beer_id=beer.id)

        if image_transitions:
            data["image_transitions"] = [transform_dict_to_camel_case(it.to_dict()) for it in image_transitions]

        return transform_dict_to_camel_case(data)

    @staticmethod
    async def process_image_transitions(db_session: AsyncSession, image_transitions_data, **kwargs):
        """Process image transitions from request"""
        if not image_transitions_data:
            return None

        ret_data = []
        for transition in image_transitions_data:
            transition_dict = transition.model_dump() if hasattr(transition, "model_dump") else transition
            transition_dict.update(kwargs)

            if transition_dict.get("id"):
                transition_id = transition_dict.pop("id")
                LOGGER.debug("Updating image transition %s with: %s", transition_id, transition_dict)
                res = await ImageTransitionsDB.update(db_session, transition_id, **transition_dict)
                if res:
                    it = await ImageTransitionsDB.get_by_pkey(db_session, transition_id)
                    await db_session.refresh(it)
                    ret_data.append(it)
            else:
                LOGGER.debug("Creating image transition with: %s", transition_dict)
                ret_data.append(await ImageTransitionsDB.create(db_session, **transition_dict))

        return ret_data

    @staticmethod
    async def verify_and_update_external_brew_tool_recipe(request_data):
        LOGGER.debug("Checking if the beer is associated with an external brew tool and verifying data")
        tool_type = request_data.get("external_brewing_tool")
        if tool_type:
            meta = request_data.get("external_brewing_tool_meta", {})
            LOGGER.debug(f"Beer is associated with {tool_type} recipe.  Metadata: {meta}.  Verifying...")
            recipe_id = meta.get("recipe_id")
            if not recipe_id:
                raise HTTPException(status_code=400, detail=f"recipe id is required when external brewing tool is set, but was not provided")
            LOGGER.debug(f"Checking {tool_type} for recipe with id: {recipe_id}.")
            tool = get_external_brewing_tool(tool_type)
            try:
                data = await tool.get_recipe_details(meta=meta)
                if not data:
                    LOGGER.error(f"{tool_type} did not return data for recipe id: {recipe_id}.")
                    raise HTTPException(status_code=400, detail=f"{tool_type} return no data for recipe with id '{recipe_id}'")
                request_data["external_brewing_tool_meta"] = BeerService.store_metadata(meta, data)
            except ResourceNotFoundError:
                LOGGER.error(f"{tool_type} returned a 404 for recipe id: {recipe_id}.")
                raise HTTPException(status_code=400, detail=f"{tool_type} recipe with id '{recipe_id}' not found")
        return request_data

    @staticmethod
    def store_metadata(metadata, ex_details, now=None):
        if not now:
            now = utcnow_aware()
        ex_details["_last_refreshed_on"] = now.isoformat()
        return {**metadata, "details": ex_details}
