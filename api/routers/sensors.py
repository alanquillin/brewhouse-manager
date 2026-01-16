"""Sensors router for FastAPI"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import AuthUser, get_db_session, require_user
from db.sensors import Sensors as SensorsDB
from services.sensors import SensorService
from lib import util

router = APIRouter(prefix="/api/v1/sensors", tags=["sensors"])
LOGGER = logging.getLogger(__name__)


class SensorCreate(BaseModel):
    """Schema for creating a sensor"""

    name: str
    sensor_type: str
    location_id: Optional[str] = None
    config: Optional[dict] = None


class SensorUpdate(BaseModel):
    """Schema for updating a sensor"""

    name: Optional[str] = None
    sensor_type: Optional[str] = None
    location_id: Optional[str] = None
    config: Optional[dict] = None


async def get_location_id(location_identifier: str, db_session: AsyncSession) -> str:
    """Get location ID from name or UUID"""
    if util.is_valid_uuid(location_identifier):
        return location_identifier

    from db.locations import Locations as LocationsDB

    locations = await LocationsDB.query(db_session, name=location_identifier)
    if locations:
        return locations[0].id

    return None


@router.get("", response_model=List[dict])
async def list_sensors(
    location: Optional[str] = None,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """List sensors accessible to the user"""
    kwargs = {}

    if location:
        location_id = await get_location_id(location, db_session)
        if not current_user.admin and location_id not in current_user.locations:
            raise HTTPException(status_code=403, detail="Not authorized to access this location")
        kwargs["locations"] = [location_id]
    elif not current_user.admin:
        kwargs["locations"] = current_user.locations

    sensors = await SensorsDB.query(db_session, **kwargs)
    return [await SensorService.transform_response(s, db_session=db_session) for s in sensors]


@router.post("", response_model=dict)
async def create_sensor(
    sensor_data: SensorCreate,
    location: Optional[str] = None,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Create a new sensor"""
    data = sensor_data.model_dump(exclude_unset=True)

    # Handle location from path parameter
    if location:
        location_id = await get_location_id(location, db_session)
        if not current_user.admin and location_id not in current_user.locations:
            raise HTTPException(status_code=403, detail="Not authorized to create sensor in this location")
        data["location_id"] = location_id

    # Check authorization for location in body
    if not current_user.admin and data.get("location_id") not in current_user.locations:
        raise HTTPException(status_code=403, detail="Not authorized to create sensor in this location")

    LOGGER.debug("Creating sensor with: %s", data)
    sensor = await SensorsDB.create(db_session, **data)

    return await SensorService.transform_response(sensor, db_session=db_session)


@router.get("/{sensor_id}", response_model=dict)
async def get_sensor(
    sensor_id: str,
    location: Optional[str] = None,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get a specific sensor"""
    kwargs = {"id": sensor_id}

    if location:
        location_id = await get_location_id(location, db_session)
        if not current_user.admin and location_id not in current_user.locations:
            raise HTTPException(status_code=403, detail="Not authorized to access this location")
        kwargs["locations"] = [location_id]

    sensors = await SensorsDB.query(db_session, **kwargs)
    if not sensors:
        raise HTTPException(status_code=404, detail="Sensor not found")

    sensor = sensors[0]

    # Check authorization
    if not current_user.admin and sensor.location_id not in current_user.locations:
        raise HTTPException(status_code=403, detail="Not authorized to access this sensor")

    return await SensorService.transform_response(sensor, db_session=db_session)


@router.patch("/{sensor_id}", response_model=dict)
async def update_sensor(
    sensor_id: str,
    sensor_data: SensorUpdate,
    location: Optional[str] = None,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Update a sensor"""
    kwargs = {"id": sensor_id}

    if location:
        location_id = await get_location_id(location, db_session)
        if not current_user.admin and location_id not in current_user.locations:
            raise HTTPException(status_code=403, detail="Not authorized to access this location")
        kwargs["locations"] = [location_id]

    sensors = await SensorsDB.query(db_session, **kwargs)
    if not sensors:
        raise HTTPException(status_code=404, detail="Sensor not found")

    sensor = sensors[0]

    # Check authorization
    if not current_user.admin and sensor.location_id not in current_user.locations:
        raise HTTPException(status_code=403, detail="Not authorized to update this sensor")

    data = sensor_data.model_dump(exclude_unset=True)

    LOGGER.debug("Updating sensor %s with data: %s", sensor_id, data)

    if data:
        sensor = await SensorsDB.update(db_session, sensor.id, **data)

    return await SensorService.transform_response(sensor, db_session=db_session)


@router.delete("/{sensor_id}")
async def delete_sensor(
    sensor_id: str,
    location: Optional[str] = None,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Delete a sensor"""
    kwargs = {"id": sensor_id}

    if location:
        location_id = await get_location_id(location, db_session)
        if not current_user.admin and location_id not in current_user.locations:
            raise HTTPException(status_code=403, detail="Not authorized to access this location")
        kwargs["locations"] = [location_id]

    sensors = await SensorsDB.query(db_session, **kwargs)
    if not sensors:
        raise HTTPException(status_code=404, detail="Sensor not found")

    sensor = sensors[0]

    # Check authorization
    if not current_user.admin and sensor.location_id not in current_user.locations:
        raise HTTPException(status_code=403, detail="Not authorized to delete this sensor")

    await SensorsDB.delete(db_session, sensor.id)
    return True
