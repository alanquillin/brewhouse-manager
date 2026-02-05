"""Tap monitors router for FastAPI"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import AuthUser, get_db_session, require_user
from db.tap_monitors import TapMonitors as TapMonitorsDB
from db.taps import Taps as TapsDB
from lib import logging, util
from lib.tap_monitors import InvalidDataType, get_tap_monitor_lib
from lib.tap_monitors import get_types as get_tap_monitor_types
from services.base import transform_dict_to_camel_case
from services.tap_monitors import TapMonitorService
from schemas.tap_monitors import TapMonitorCreate, TapMonitorUpdate

router = APIRouter()
LOGGER = logging.getLogger(__name__)


async def get_location_id(location_identifier: str, db_session: AsyncSession) -> str:
    """Get location ID from name or UUID"""
    if util.is_valid_uuid(location_identifier):
        return location_identifier

    from db.locations import Locations as LocationsDB

    locations = await LocationsDB.query(db_session, name=location_identifier)
    if locations:
        return locations[0].id

    return None


@router.get("/types", response_model=List[str])
async def list_monitor_types(
    current_user: AuthUser = Depends(require_user),
):
    """List available tap monitor types"""
    return [str(t) for t in get_tap_monitor_types()]


@router.get("/discover", response_model=dict)
async def discover_tap_monitors(
    current_user: AuthUser = Depends(require_user),
):
    raise HTTPException(status_code=404, detail="Resource not found")


@router.get("/discover/{monitor_type}", response_model=List[dict])
async def discover_tap_monitors_by_type(
    monitor_type: str,
    current_user: AuthUser = Depends(require_user),
):
    """Discover tap monitors of a specific type"""
    if monitor_type not in get_tap_monitor_types():
        raise HTTPException(
            status_code=400, detail=f"Invalid monitor type: {monitor_type}"
        )

    tap_monitor_lib = get_tap_monitor_lib(monitor_type)

    if not tap_monitor_lib.supports_discovery():
        raise HTTPException(
            status_code=400, detail=f"{monitor_type} tap monitors do not support discovery"
        )

    data = await tap_monitor_lib.discover()
    return transform_dict_to_camel_case(data)


@router.get("", response_model=List[dict])
async def list_tap_monitors(
    request: Request,
    location: Optional[str] = None,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """List tap monitors accessible to the user"""
    kwargs = {}

    if location:
        location_id = await get_location_id(location, db_session)
        if not current_user.admin and location_id not in current_user.locations:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this location"
            )
        kwargs["locations"] = [location_id]
    elif not current_user.admin:
        kwargs["locations"] = current_user.locations

    tap_monitors = await TapMonitorsDB.query(db_session, **kwargs)
    include_tap_details = request.query_params.get("include_tap_details", "false").lower() in ["true", "yes", "", "1"]
    return [
        await TapMonitorService.transform_response(s, db_session=db_session, include_tap=include_tap_details)
        for s in tap_monitors
    ]


@router.post("", response_model=dict)
async def create_tap_monitor(
    tap_monitor_data: TapMonitorCreate,
    location: Optional[str] = None,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Create a new tap monitor"""
    data = tap_monitor_data.model_dump(exclude_unset=True)

    # Handle location from path parameter
    if location:
        location_id = await get_location_id(location, db_session)
        if not current_user.admin and location_id not in current_user.locations:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to create tap monitor in this location",
            )
        data["location_id"] = location_id

    # Check authorization for location in body
    if not current_user.admin and data.get("location_id") not in current_user.locations:
        raise HTTPException(
            status_code=403, detail="Not authorized to create tap monitor in this location"
        )

    LOGGER.debug("Creating tap monitor with: %s", data)
    tap_monitor = await TapMonitorsDB.create(db_session, **data)

    return await TapMonitorService.transform_response(tap_monitor, db_session=db_session)


@router.get("/{tap_monitor_id}", response_model=dict)
async def get_tap_monitor(
    request: Request,
    tap_monitor_id: str,
    location: Optional[str] = None,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get a specific tap monitor"""
    if location:
        location_id = await get_location_id(location, db_session)
        if not current_user.admin and location_id not in current_user.locations:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this location"
            )

    tap_monitor = await TapMonitorsDB.get_by_pkey(db_session, tap_monitor_id)
    if not tap_monitor:
        raise HTTPException(status_code=404, detail="Tap monitor not found")

    # Check authorization
    if not current_user.admin and tap_monitor.location_id not in current_user.locations:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this tap monitor"
        )
    include_tap_details = request.query_params.get("include_tap_details", "false").lower() in ["true", "yes", "", "1"]
    return await TapMonitorService.transform_response(tap_monitor, db_session=db_session, include_tap=include_tap_details)


@router.patch("/{tap_monitor_id}", response_model=dict)
async def update_tap_monitor(
    tap_monitor_id: str,
    tap_monitor_data: TapMonitorUpdate,
    location: Optional[str] = None,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Update a tap monitor"""

    if location:
        location_id = await get_location_id(location, db_session)
        if not current_user.admin and location_id not in current_user.locations:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this location"
            )

    data = tap_monitor_data.model_dump(exclude_unset=True)

    location_id = data.get("location_id")
    if location_id:
        if not current_user.admin and location_id not in current_user.locations:
            raise HTTPException(
                status_code=403, detail="Not authorized to add tap monitor in this location"
            )

    tap_monitor = await TapMonitorsDB.get_by_pkey(db_session, tap_monitor_id)
    if not tap_monitor:
        raise HTTPException(status_code=404, detail="Tap monitor not found")

    # Check authorization
    if not current_user.admin and tap_monitor.location_id not in current_user.locations:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this tap monitor"
        )

    LOGGER.debug("Updating tap monitor %s with data: %s", tap_monitor_id, data)

    if data:
        await TapMonitorsDB.update(db_session, tap_monitor.id, **data)

    tap_monitor = TapMonitorsDB.get_by_pkey(db_session, tap_monitor_id)
    return await TapMonitorService.transform_response(tap_monitor, db_session=db_session)


@router.delete("/{tap_monitor_id}")
async def delete_tap_monitor(
    tap_monitor_id: str,
    location: Optional[str] = None,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Delete a tap monitor"""
    kwargs = {"id": tap_monitor_id}

    # if location was passed as part of the query, first check that user is associated with location
    location_id = None
    if location:
        location_id = await get_location_id(location, db_session)
        if not current_user.admin and location_id not in current_user.locations:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this location"
            )

    tap_monitor = await TapMonitorsDB.get_by_pkey(db_session, tap_monitor_id)
    if not tap_monitor:
        raise HTTPException(status_code=404, detail="Tap monitor not found")

    if location_id and (tap_monitor.location_id != location_id):
        LOGGER.warning("Tap monitor query succeeded but the user passed in a location that the tap monitor was not associated with, returning 404")
        raise HTTPException(status_code=404, detail="Tap monitor not found")

    if not current_user.admin and tap_monitor.location_id not in current_user.locations:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this location"
        )

    # update associated taps
    taps = await TapsDB.query(db_session, tap_monitor_id=tap_monitor_id)
    if taps:
        for tap in taps:
            await TapsDB.update(db_session, tap.id, tap_monitor_id=None)

    await TapMonitorsDB.delete(db_session, tap_monitor.id)
    return True


@router.get("/{tap_monitor_id}/data")
async def get_tap_monitor_data(
    tap_monitor_id: str,
    location: Optional[str] = None,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get tap monitor data (no authentication required for public access)"""
    tap_monitor = None
    if location:
        location_id = await get_location_id(location, db_session)
        kwargs = {"location_id": location_id, "id": tap_monitor_id}
        resp = await TapMonitorsDB.query(db_session, **kwargs)
        if resp:
            tap_monitor = resp[0]
    else:
        tap_monitor = await TapMonitorsDB.get_by_pkey(db_session, tap_monitor_id)

    if not tap_monitor:
        raise HTTPException(status_code=404, detail="Tap monitor not found")

    tap_monitor_lib = get_tap_monitor_lib(tap_monitor.monitor_type)
    try:
        return await tap_monitor_lib.get_all(monitor=tap_monitor, db_session=db_session)
    except InvalidDataType as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.get("/{tap_monitor_id}/data/{data_type}")
async def get_specific_tap_monitor_data(
    tap_monitor_id: str,
    data_type: str,
    location: Optional[str] = None,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get tap monitor data (no authentication required for public access)"""
    tap_monitor = None
    if location:
        location_id = await get_location_id(location, db_session)
        kwargs = {"location_id": location_id, "id": tap_monitor_id}
        resp = await TapMonitorsDB.query(db_session, **kwargs)
        if resp:
            tap_monitor = resp[0]
    else:
        tap_monitor = await TapMonitorsDB.get_by_pkey(db_session, tap_monitor_id)

    if not tap_monitor:
        raise HTTPException(status_code=404, detail="Tap monitor not found")

    tap_monitor_lib = get_tap_monitor_lib(tap_monitor.monitor_type)
    try:
        try:
            return await tap_monitor_lib.get(data_type, monitor=tap_monitor, db_session=db_session)
        except InvalidDataType as ex:
            raise HTTPException(
                status_code=400, detail=f"Invalid data type: {data_type}"
            )
    except InvalidDataType as ex:
        raise HTTPException(status_code=400, detail=str(ex))
