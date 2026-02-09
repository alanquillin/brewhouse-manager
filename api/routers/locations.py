"""Locations router for FastAPI"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from db.batch_locations import BatchLocations as BatchLocationsDB
from db.locations import Locations as LocationsDB
from db.taps import Taps as TapsDB
from db.user_locations import UserLocations as UserLocationsDB
from dependencies.auth import AuthUser, get_db_session, require_admin, require_user
from lib import logging, util
from schemas.locations import LocationCreate, LocationUpdate
from services.locations import LocationService

router = APIRouter(prefix="/api/v1/locations", tags=["locations"])
LOGGER = logging.getLogger(__name__)


async def get_location_id(location_identifier: str, db_session: AsyncSession) -> str:
    """Get location ID from name or UUID"""
    if util.is_valid_uuid(location_identifier):
        return location_identifier

    # Look up by name
    locations = await LocationsDB.query(db_session, name=location_identifier)
    if locations:
        return locations[0].id

    return None


@router.get("", response_model=List[dict])
async def list_locations(
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """List locations accessible to the user"""
    kwargs = {}
    if not current_user.admin:
        kwargs["ids"] = current_user.locations

    locations = await LocationsDB.query(db_session, **kwargs)
    return [await LocationService.transform_response(l, db_session=db_session) for l in locations]


@router.post("", response_model=dict, status_code=201)
async def create_location(
    location_data: LocationCreate,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Create a new location (admin only)"""
    data = location_data.model_dump(exclude_unset=True)

    LOGGER.debug("Creating location with: %s", data)
    location = await LocationsDB.create(db_session, **data)

    return await LocationService.transform_response(location, db_session=db_session)


@router.get("/{location}", response_model=dict)
async def get_location(
    location: str,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get a specific location by ID or name"""
    location_id = await get_location_id(location, db_session)
    if not location_id:
        raise HTTPException(status_code=404, detail="Location not found")

    loc = await LocationsDB.get_by_pkey(db_session, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")

    # Check authorization
    if not current_user.admin and location_id not in current_user.locations:
        raise HTTPException(status_code=403, detail="Not authorized to access this location")

    return await LocationService.transform_response(loc, db_session=db_session)


@router.patch("/{location}", response_model=dict)
async def update_location(
    location: str,
    location_data: LocationUpdate,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Update a location (admin only)"""
    location_id = await get_location_id(location, db_session)
    if not location_id:
        raise HTTPException(status_code=404, detail="Location not found")

    loc = await LocationsDB.get_by_pkey(db_session, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")

    data = location_data.model_dump(exclude_unset=True)

    LOGGER.debug("Updating location %s with data: %s", location_id, data)

    if data:
        await LocationsDB.update(db_session, location_id, **data)

    loc = await LocationsDB.get_by_pkey(db_session, location_id)
    await db_session.refresh(loc)
    return await LocationService.transform_response(loc, db_session=db_session)


@router.delete("/{location}", status_code=204)
async def delete_location(
    location: str,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Delete a location (admin only)"""
    location_id = await get_location_id(location, db_session)
    if not location_id:
        raise HTTPException(status_code=404, detail="Location not found")

    loc = await LocationsDB.get_by_pkey(db_session, location_id)
    if not loc:
        raise HTTPException(status_code=404, detail="Location not found")

    await TapsDB.delete_by(db_session, location_id=location_id)
    await BatchLocationsDB.delete_by(db_session, location_id=location_id)
    await UserLocationsDB.delete_by(db_session, location_id=location_id)
    await LocationsDB.delete(db_session, location_id)
    return
