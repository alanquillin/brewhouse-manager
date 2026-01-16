"""Beer router for FastAPI"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import AuthUser, get_db_session, require_user
from db.beers import Beers as BeersDB
from schemas.beers import BeerCreate, BeerResponse, BeerUpdate
from services.beers import BeerService

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

    return [
        await BeerService.transform_response(b, db_session=db_session, force_refresh=force_refresh) for b in beers
    ]


@router.post("", response_model=dict)
async def create_beer(
    beer_data: BeerCreate,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Create a new beer"""
    # Extract data, excluding id and image_transitions
    data = beer_data.model_dump(exclude_unset=True, exclude={"id", "image_transitions"})

    LOGGER.debug("Creating beer with: %s", data)
    beer = await BeersDB.create(db_session, **data)

    # Process image transitions if provided
    image_transitions = None
    if beer_data.image_transitions:
        image_transitions = await BeerService.process_image_transitions(
            db_session, beer_data.image_transitions, beer_id=beer.id
        )

    return await BeerService.transform_response(beer, db_session=db_session, image_transitions=image_transitions)


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

    # Merge external_brewing_tool_meta if both exist
    external_brewing_tool_meta = data.get("external_brewing_tool_meta", {})
    if external_brewing_tool_meta and beer.external_brewing_tool_meta:
        data["external_brewing_tool_meta"] = {**beer.external_brewing_tool_meta, **external_brewing_tool_meta}

    LOGGER.debug("Updating beer %s with data: %s", beer_id, data)

    # Update beer if there's data
    if data:
        await BeersDB.update(db_session, beer_id, **data)

    # Process image transitions
    image_transitions = None
    if beer_data.image_transitions:
        image_transitions = await BeerService.process_image_transitions(
            db_session, beer_data.image_transitions, beer_id=beer_id
        )

    # Fetch updated beer
    beer = await BeersDB.get_by_pkey(db_session, beer_id)

    return await BeerService.transform_response(beer, db_session=db_session, image_transitions=image_transitions)


@router.delete("/{beer_id}")
async def delete_beer(
    beer_id: str,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Delete a beer"""
    beer = await BeersDB.get_by_pkey(db_session, beer_id)

    if not beer:
        raise HTTPException(status_code=404, detail="Beer not found")

    await BeersDB.delete(db_session, beer.id)
    return True
