"""Beverage router for FastAPI"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

# isort: off
# fmt: off
from db.batches import Batches as BatchesDB  # pylint: disable=wrong-import-position
from db.batch_locations import BatchLocations as BatchLocationsDB
from db.batch_overrides import BatchOverrides as BatchOverridesDB
# isort: on
# fmt: on
from db.beverages import Beverages as BeveragesDB
from db.image_transitions import ImageTransitions as ImageTransitionsDB
from db.on_tap import OnTap as OnTapDB
from dependencies.auth import AuthUser, get_db_session, require_user
from lib import logging
from schemas.beverages import BeverageCreate, BeverageUpdate
from services.beverages import BeverageService
from services.taps import TapService

router = APIRouter(prefix="/api/v1/beverages", tags=["beverages"])
LOGGER = logging.getLogger(__name__)


@router.get("", response_model=List[dict])
async def list_beverages(
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """List all beverages (public endpoint)"""
    beverages = await BeveragesDB.query(db_session)
    return [await BeverageService.transform_response(b, db_session=db_session) for b in beverages]


@router.post("", response_model=dict, status_code=201)
async def create_beverage(
    beverage_data: BeverageCreate,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Create a new beverage (requires authentication)"""
    # Extract data, excluding id and image_transitions
    data = beverage_data.model_dump(exclude_unset=True, exclude={"id", "image_transitions"})

    LOGGER.debug("Creating beverage with: %s", data)
    beverage = await BeveragesDB.create(db_session, **data)

    # Process image transitions if provided
    image_transitions = None
    if beverage_data.image_transitions:
        image_transitions = await BeverageService.process_image_transitions(db_session, beverage_data.image_transitions, beverage_id=beverage.id)

    return await BeverageService.transform_response(beverage, db_session=db_session, image_transitions=image_transitions)


@router.get("/{beverage_id}", response_model=dict)
async def get_beverage(
    beverage_id: str,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get a specific beverage (public endpoint)"""
    beverage = await BeveragesDB.get_by_pkey(db_session, beverage_id)

    if not beverage:
        raise HTTPException(status_code=404, detail="Beverage not found")

    return await BeverageService.transform_response(beverage, db_session=db_session)


@router.patch("/{beverage_id}", response_model=dict)
async def update_beverage(
    beverage_id: str,
    beverage_data: BeverageUpdate,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Update a beverage (requires authentication)"""
    beverage = await BeveragesDB.get_by_pkey(db_session, beverage_id)

    if not beverage:
        raise HTTPException(status_code=404, detail="Beverage not found")

    # Extract data, excluding id and image_transitions
    data = beverage_data.model_dump(exclude_unset=True, exclude={"id", "image_transitions"})

    LOGGER.debug("Updating beverage %s with data: %s", beverage_id, data)

    # Update beverage if there's data
    if data:
        await BeveragesDB.update(db_session, beverage_id, **data)

    # Process image transitions
    image_transitions = None
    if beverage_data.image_transitions:
        image_transitions = await BeverageService.process_image_transitions(db_session, beverage_data.image_transitions, beverage_id=beverage_id)

    # Fetch updated beverage
    beverage = await BeveragesDB.get_by_pkey(db_session, beverage_id)
    await db_session.refresh(beverage)

    return await BeverageService.transform_response(beverage, db_session=db_session, image_transitions=image_transitions)


@router.delete("/{beverage_id}", status_code=204)
async def delete_beverage(
    beverage_id: str,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Delete a beverage, cascading to archived batches only"""
    beverage = await BeveragesDB.get_by_pkey(db_session, beverage_id)

    if not beverage:
        raise HTTPException(status_code=404, detail="Beverage not found")

    batches = await BatchesDB.query(db_session, beverage_id=beverage_id)
    active_batches = [b for b in batches if b.archived_on is None]
    if active_batches:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot delete beverage with {len(active_batches)} active batch(es). Archive all batches before deleting.",
        )

    for batch in batches:
        await TapService.clear_on_tap_references_for_batch(db_session, batch.id, autocommit=False)
        await BatchLocationsDB.delete_by(db_session, batch_id=batch.id, autocommit=False)
        await OnTapDB.delete_by(db_session, batch_id=batch.id, autocommit=False)
        await BatchOverridesDB.delete_by(db_session, batch_id=batch.id, autocommit=False)

    if batches:
        await BatchesDB.delete_by(db_session, beverage_id=beverage_id, autocommit=False)

    await ImageTransitionsDB.delete_by(db_session, beverage_id=beverage_id, autocommit=False)
    await BeveragesDB.delete(db_session, beverage.id)
    return
