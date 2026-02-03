"""Sensors router for FastAPI"""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import AuthUser, get_db_session, require_user
from db.sensors import Sensors as SensorsDB
from db.taps import Taps as TapsDB
from lib import logging, util
from lib.sensors import InvalidDataType, get_sensor_lib
from lib.sensors import get_types as get_sensor_types
from services.base import transform_dict_to_camel_case
from services.sensors import SensorService
from schemas.sensors import SensorCreate, SensorUpdate

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
async def list_sensor_types(
    current_user: AuthUser = Depends(require_user),
):
    """List available sensor types"""
    return [str(t) for t in get_sensor_types()]


@router.get("/discover", response_model=dict)
async def discover_sensors(
    current_user: AuthUser = Depends(require_user),
):
    raise HTTPException(status_code=404, detail="Resource not found")


@router.get("/discover/{sensor_type}", response_model=List[dict])
async def discover_sensors(
    sensor_type: str,
    current_user: AuthUser = Depends(require_user),
):
    """Discover sensors of a specific type"""
    if sensor_type not in get_sensor_types():
        raise HTTPException(
            status_code=400, detail=f"Invalid sensor type: {sensor_type}"
        )

    sensor_lib = get_sensor_lib(sensor_type)

    if not sensor_lib.supports_discovery():
        raise HTTPException(
            status_code=400, detail=f"{sensor_type} sensors do not support discovery"
        )

    data = await sensor_lib.discover()
    return transform_dict_to_camel_case(data)


@router.get("", response_model=List[dict])
async def list_sensors(
    request: Request,
    location: Optional[str] = None,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """List sensors accessible to the user"""
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

    sensors = await SensorsDB.query(db_session, **kwargs)
    include_tap_details = request.query_params.get("include_tap_details", "false").lower() in ["true", "yes", "", "1"]
    return [
        await SensorService.transform_response(s, db_session=db_session, include_tap=include_tap_details)
        for s in sensors
    ]


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
            raise HTTPException(
                status_code=403,
                detail="Not authorized to create sensor in this location",
            )
        data["location_id"] = location_id

    # Check authorization for location in body
    if not current_user.admin and data.get("location_id") not in current_user.locations:
        raise HTTPException(
            status_code=403, detail="Not authorized to create sensor in this location"
        )

    LOGGER.debug("Creating sensor with: %s", data)
    sensor = await SensorsDB.create(db_session, **data)

    return await SensorService.transform_response(sensor, db_session=db_session)


@router.get("/{sensor_id}", response_model=dict)
async def get_sensor(
    request: Request,
    sensor_id: str,
    location: Optional[str] = None,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get a specific sensor"""
    if location:
        location_id = await get_location_id(location, db_session)
        if not current_user.admin and location_id not in current_user.locations:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this location"
            )

    sensor = await SensorsDB.get_by_pkey(db_session, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    # Check authorization
    if not current_user.admin and sensor.location_id not in current_user.locations:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this sensor"
        )
    include_tap_details = request.query_params.get("include_tap_details", "false").lower() in ["true", "yes", "", "1"]
    return await SensorService.transform_response(sensor, db_session=db_session, include_tap=include_tap_details)


@router.patch("/{sensor_id}", response_model=dict)
async def update_sensor(
    sensor_id: str,
    sensor_data: SensorUpdate,
    location: Optional[str] = None,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Update a sensor"""

    if location:
        location_id = await get_location_id(location, db_session)
        if not current_user.admin and location_id not in current_user.locations:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this location"
            )
        
    data = sensor_data.model_dump(exclude_unset=True)

    location_id = data.get("location_id")
    if location_id:
        if not current_user.admin and location_id not in current_user.locations:
            raise HTTPException(
                status_code=403, detail="Not authorized to add sensor in this location"
            )

    sensor = await SensorsDB.get_by_pkey(db_session, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    # Check authorization
    if not current_user.admin and sensor.location_id not in current_user.locations:
        raise HTTPException(
            status_code=403, detail="Not authorized to update this sensor"
        )

    LOGGER.debug("Updating sensor %s with data: %s", sensor_id, data)

    if data:
        await SensorsDB.update(db_session, sensor.id, **data)

    sensor = SensorsDB.get_by_pkey(db_session, sensor_id)
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

    # if location was passed as part of the query, first check that user is associated with location
    location_id = None
    if location:
        location_id = await get_location_id(location, db_session)
        if not current_user.admin and location_id not in current_user.locations:
            raise HTTPException(
                status_code=403, detail="Not authorized to access this location"
            )

    sensor = await SensorsDB.get_by_pkey(db_session, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    if location_id and (sensor.location_id != location_id):
        LOGGER.warning("Sensor query succeeded but the user passed in a location that the sensor was not associated with, returning 404")
        raise HTTPException(status_code=404, detail="Sensor not found")
    
    if not current_user.admin and sensor.location_id not in current_user.locations:
        raise HTTPException(
            status_code=403, detail="Not authorized to access this location"
        )

    # update associated 
    taps = await TapsDB.query(db_session, sensor_id=sensor_id)
    if taps:
        for tap in taps:
            await TapsDB.update(db_session, tap.id, sensor_id=None)

    await SensorsDB.delete(db_session, sensor.id)
    return True


@router.get("/{sensor_id}/data")
async def get_sensor_data(
    sensor_id: str,
    location: Optional[str] = None,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get sensor data (no authentication required for public access)"""
    sensor = None
    if location:
        location_id = await get_location_id(location, db_session)
        kwargs = {"location_id": location_id, "id": sensor_id}
        resp = await SensorsDB.query(db_session, **kwargs)
        if resp:
            sensor = resp[0]
    else:
        sensor = await SensorsDB.get_by_pkey(db_session, sensor_id)

    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    sensor_lib = get_sensor_lib(sensor.sensor_type)
    try:
        return await sensor_lib.get_all(sensor=sensor)
    except InvalidDataType as ex:
        raise HTTPException(status_code=400, detail=str(ex))


@router.get("/{sensor_id}/data/{data_type}")
async def get_specific_sensor_data(
    sensor_id: str,
    data_type: str,
    location: Optional[str] = None,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get sensor data (no authentication required for public access)"""
    sensor = None
    if location:
        location_id = await get_location_id(location, db_session)
        kwargs = {"location_id": location_id, "id": sensor_id}
        resp = await SensorsDB.query(db_session, **kwargs)
        if resp:
            sensor = resp[0]
    else:
        sensor = await SensorsDB.get_by_pkey(db_session, sensor_id)

    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    sensor_lib = get_sensor_lib(sensor.sensor_type)
    try:
        try:
            return await sensor_lib.get(data_type, sensor=sensor)
        except InvalidDataType as ex:
            raise HTTPException(
                status_code=400, detail=f"Invalid data type: {data_type}"
            )
    except InvalidDataType as ex:
        raise HTTPException(status_code=400, detail=str(ex))
