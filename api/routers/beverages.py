"""Beverage router for FastAPI"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import AuthUser, get_db_session, require_user
from db.beverages import Beverages as BeveragesDB
from schemas.beverages import BeverageCreate, BeverageResponse, BeverageUpdate
from services.beverages import BeverageService

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


@router.post("", response_model=dict)
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
        image_transitions = await BeverageService.process_image_transitions(
            db_session, beverage_data.image_transitions, beverage_id=beverage.id
        )

    return await BeverageService.transform_response(
        beverage, db_session=db_session, image_transitions=image_transitions
    )


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
        image_transitions = await BeverageService.process_image_transitions(
            db_session, beverage_data.image_transitions, beverage_id=beverage_id
        )

    # Fetch updated beverage
    beverage = await BeveragesDB.get_by_pkey(db_session, beverage_id)

    return await BeverageService.transform_response(
        beverage, db_session=db_session, image_transitions=image_transitions
    )


@router.delete("/{beverage_id}")
async def delete_beverage(
    beverage_id: str,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Delete a beverage (requires authentication)"""
    beverage = await BeveragesDB.get_by_pkey(db_session, beverage_id)

    if not beverage:
        raise HTTPException(status_code=404, detail="Beverage not found")

    await BeveragesDB.delete(db_session, beverage.id)
    return True
