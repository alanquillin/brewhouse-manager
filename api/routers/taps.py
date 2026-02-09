"""Taps router for FastAPI"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.batches import Batches as BatchesDB
from db.on_tap import OnTap as OnTapDB
from db.taps import Taps as TapsDB
from dependencies.auth import AuthUser, get_db_session, require_user
from lib import logging
from routers import get_location_id
from schemas.taps import TapCreate, TapUpdate
from services.taps import TapService

router = APIRouter()
LOGGER = logging.getLogger(__name__)


@router.get("", response_model=List[dict])
async def list_taps(
    location: Optional[str] = None,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """List taps accessible to the user"""
    kwargs = {}

    if location:
        location_id = await get_location_id(location, db_session)
        if not current_user.admin and location_id not in current_user.locations:
            raise HTTPException(status_code=403, detail="Not authorized to access this location")
        kwargs["locations"] = [location_id]
    elif not current_user.admin:
        kwargs["locations"] = current_user.locations

    taps = await TapsDB.query(db_session, **kwargs)
    return [await TapService.transform_response(t, db_session=db_session) for t in taps]


@router.post("", response_model=dict, status_code=201)
async def create_tap(
    tap_data: TapCreate,
    location: Optional[str] = None,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Create a new tap"""
    data = tap_data.model_dump(exclude_unset=True)

    # Handle location from path parameter
    if location:
        location_id = await get_location_id(location, db_session)
        if not current_user.admin and location_id not in current_user.locations:
            raise HTTPException(status_code=403, detail="Not authorized to create tap in this location")
        data["location_id"] = location_id

    # Check authorization for location in body
    if not current_user.admin and data.get("location_id") not in current_user.locations:
        raise HTTPException(status_code=403, detail="Not authorized to create tap in this location")

    # Handle batch_id and create on_tap entry
    batch_id = data.get("batch_id")
    if batch_id == "":
        batch_id = None

    if batch_id:
        batch = await BatchesDB.get_by_pkey(db_session, batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")

        on_tap = await OnTapDB.create(db_session, batch_id=batch_id, tapped_on=datetime.utcnow())
        data["on_tap_id"] = on_tap.id

    # Remove batch_id from data as it's not a direct field
    if "batch_id" in data:
        del data["batch_id"]

    LOGGER.debug("Creating tap with: %s", data)
    tap = await TapsDB.create(db_session, **data)

    return await TapService.transform_response(tap, db_session=db_session)


@router.get("/{tap_id}", response_model=dict)
async def get_tap(
    tap_id: str,
    location: Optional[str] = None,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get a specific tap"""
    kwargs = {"id": tap_id}

    if location:
        location_id = await get_location_id(location, db_session)
        if not current_user.admin and location_id not in current_user.locations:
            raise HTTPException(status_code=403, detail="Not authorized to access this location")
        kwargs["locations"] = [location_id]

    taps = await TapsDB.query(db_session, **kwargs)
    if not taps:
        raise HTTPException(status_code=404, detail="Tap not found")

    tap = taps[0]

    # Check authorization
    if not current_user.admin and tap.location_id not in current_user.locations:
        raise HTTPException(status_code=403, detail="Not authorized to access this tap")

    return await TapService.transform_response(tap, db_session=db_session)


@router.patch("/{tap_id}", response_model=dict)
async def update_tap(
    tap_id: str,
    tap_data: TapUpdate,
    location: Optional[str] = None,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Update a tap"""
    kwargs = {"id": tap_id}

    if location:
        location_id = await get_location_id(location, db_session)
        if not current_user.admin and location_id not in current_user.locations:
            raise HTTPException(status_code=403, detail="Not authorized to access this location")
        kwargs["locations"] = [location_id]

    taps = await TapsDB.query(db_session, **kwargs)
    if not taps:
        raise HTTPException(status_code=404, detail="Tap not found")

    tap = taps[0]

    # Check authorization
    if not current_user.admin and tap.location_id not in current_user.locations:
        raise HTTPException(status_code=403, detail="Not authorized to update this tap")

    data = tap_data.model_dump(exclude_unset=True)

    # Get current batch_id
    current_batch_id = None
    await tap.awaitable_attrs.on_tap
    if tap.on_tap:
        current_batch_id = tap.on_tap.batch_id

    # Handle batch_id updates
    new_batch_id = data.get("batch_id")
    if new_batch_id == "":
        new_batch_id = None

    if "batch_id" in data:
        del data["batch_id"]  # Remove from data as it's not a direct field

        # Check if batch changed
        if new_batch_id != current_batch_id:
            # Remove old on_tap entry if exists
            if tap.on_tap_id:
                await OnTapDB.update(db_session, tap.on_tap_id, untapped_on=datetime.utcnow())
                data["on_tap_id"] = None

            # Create new on_tap entry if batch_id provided
            if new_batch_id:
                batch = await BatchesDB.get_by_pkey(db_session, new_batch_id)
                if not batch:
                    raise HTTPException(status_code=404, detail="Batch not found")

                on_tap = await OnTapDB.create(
                    db_session,
                    batch_id=new_batch_id,
                    tapped_on=datetime.utcnow(),
                )
                data["on_tap_id"] = on_tap.id

    LOGGER.debug("Updating tap %s with data: %s", tap_id, data)

    if data:
        await TapsDB.update(db_session, tap.id, **data)

    # Refresh tap to get updated relationships
    tap = await TapsDB.get_by_pkey(db_session, tap_id)
    await db_session.refresh(tap)

    return await TapService.transform_response(tap, db_session=db_session)


@router.delete("/{tap_id}", status_code=204)
async def delete_tap(
    tap_id: str,
    location: Optional[str] = None,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Delete a tap"""
    kwargs = {"id": tap_id}

    if location:
        location_id = await get_location_id(location, db_session)
        if not current_user.admin and location_id not in current_user.locations:
            raise HTTPException(status_code=403, detail="Not authorized to access this location")
        kwargs["locations"] = [location_id]

    taps = await TapsDB.query(db_session, **kwargs)
    if not taps:
        raise HTTPException(status_code=404, detail="Tap not found")

    tap = taps[0]

    # Check authorization
    if not current_user.admin and tap.location_id not in current_user.locations:
        raise HTTPException(status_code=403, detail="Not authorized to delete this tap")

    # Delete on_tap entry if exists
    if tap.on_tap_id:
        await OnTapDB.delete(db_session, tap.on_tap_id)

    await TapsDB.delete(db_session, tap.id)
    return
