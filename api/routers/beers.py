"""Beer router for FastAPI"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

# isort: off
# fmt: off
from db.batches import Batches as BatchesDB  # pylint: disable=wrong-import-position
from db.batch_locations import BatchLocations as BatchLocationsDB
from db.batch_overrides import BatchOverrides as BatchOverridesDB
# isort: on
# fmt: on
from db.beers import Beers as BeersDB
from db.image_transitions import ImageTransitions as ImageTransitionsDB
from db.on_tap import OnTap as OnTapDB
from dependencies.auth import AuthUser, get_db_session, require_user
from lib import logging
from schemas.beers import BeerCreate, BeerUpdate
from services.beers import BeerService
from services.taps import TapService

router = APIRouter(prefix="/api/v1/beers", tags=["beers"])
LOGGER = logging.getLogger(__name__)


@router.get("", response_model=List[dict])
async def list_beers(
    request: Request,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """List all beers"""
    beers = await BeersDB.query(db_session)
    force_refresh = request.query_params.get("force_refresh", "false").lower() in ["true", "yes", "", "1"]

    return [await BeerService.transform_response(b, db_session=db_session, force_refresh=force_refresh) for b in beers]


@router.post("", response_model=dict, status_code=201)
async def create_beer(
    beer_data: BeerCreate,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Create a new beer"""
    # Extract data, excluding id and image_transitions
    data = beer_data.model_dump(exclude_unset=True, exclude={"id", "image_transitions"})

    data = await BeerService.verify_and_update_external_brew_tool_recipe(data)

    LOGGER.debug("Creating beer with: %s", data)
    beer = await BeersDB.create(db_session, **data)

    # Process image transitions if provided
    image_transitions = None
    if beer_data.image_transitions:
        image_transitions = await BeerService.process_image_transitions(db_session, beer_data.image_transitions, beer_id=beer.id)

    return await BeerService.transform_response(beer, db_session=db_session, image_transitions=image_transitions, skip_meta_refresh=True)


@router.get("/{beer_id}", response_model=dict)
async def get_beer(
    beer_id: str,
    request: Request,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get a specific beer"""
    beer = await BeersDB.get_by_pkey(db_session, beer_id)

    if not beer:
        raise HTTPException(status_code=404, detail="Beer not found")

    force_refresh = request.query_params.get("force_refresh", "false").lower() in ["true", "yes", "", "1"]
    return await BeerService.transform_response(beer, db_session=db_session, force_refresh=force_refresh)


@router.patch("/{beer_id}", response_model=dict)
async def update_beer(
    beer_id: str,
    beer_data: BeerUpdate,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Update a beer"""
    beer = await BeersDB.get_by_pkey(db_session, beer_id)

    if not beer:
        raise HTTPException(status_code=404, detail="Beer not found")

    # Extract data, excluding id and image_transitions
    data = beer_data.model_dump(exclude_unset=True, exclude={"id", "image_transitions"})

    skip_meta_refresh = False
    # Merge external_brewing_tool_meta if both exist
    external_brewing_tool_meta = data.get("external_brewing_tool_meta", {})
    if external_brewing_tool_meta:
        if beer.external_brewing_tool_meta:
            data["external_brewing_tool_meta"] = {**beer.external_brewing_tool_meta, **external_brewing_tool_meta}
            old_ext_recipe_id = beer.external_brewing_tool_meta.get("recipe_id")
            new_ext_recipe_id = external_brewing_tool_meta.get("recipe_id")
            if new_ext_recipe_id != old_ext_recipe_id:
                LOGGER.info("external brew tool recipe id for beer (%s) has changed.  Verifying new id.", beer_id)
                LOGGER.debug("beer (%s) external brew tool recipe id change details: old = %s, new = %s", beer_id, old_ext_recipe_id, new_ext_recipe_id)
                data = await BeerService.verify_and_update_external_brew_tool_recipe(data)
                skip_meta_refresh = True

    LOGGER.debug("Updating beer %s with data: %s", beer_id, data)
    # Update beer if there's data
    if data:
        await BeersDB.update(db_session, beer_id, **data)

    # Process image transitions
    image_transitions = None
    if beer_data.image_transitions:
        image_transitions = await BeerService.process_image_transitions(db_session, beer_data.image_transitions, beer_id=beer_id)

    # Fetch updated beer
    beer = await BeersDB.get_by_pkey(db_session, beer_id)
    await db_session.refresh(beer)

    return await BeerService.transform_response(beer, db_session=db_session, image_transitions=image_transitions, skip_meta_refresh=skip_meta_refresh)


@router.delete("/{beer_id}", status_code=204)
async def delete_beer(
    beer_id: str,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Delete a beer, cascading to archived batches only"""
    beer = await BeersDB.get_by_pkey(db_session, beer_id)

    if not beer:
        raise HTTPException(status_code=404, detail="Beer not found")

    batches = await BatchesDB.query(db_session, beer_id=beer_id)
    active_batches = [b for b in batches if b.archived_on is None]
    if active_batches:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete beer with {len(active_batches)} active batch(es). Archive all batches before deleting.",
        )

    for batch in batches:
        await TapService.clear_on_tap_references_for_batch(db_session, batch.id, autocommit=False)
        await BatchLocationsDB.delete_by(db_session, batch_id=batch.id, autocommit=False)
        await OnTapDB.delete_by(db_session, batch_id=batch.id, autocommit=False)
        await BatchOverridesDB.delete_by(db_session, batch_id=batch.id, autocommit=False)

    if batches:
        await BatchesDB.delete_by(db_session, beer_id=beer_id, autocommit=False)

    await ImageTransitionsDB.delete_by(db_session, beer_id=beer_id, autocommit=False)
    await BeersDB.delete(db_session, beer.id)
    return
