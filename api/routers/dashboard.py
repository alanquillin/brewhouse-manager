"""Dashboard router for FastAPI"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import get_db_session
from db.locations import Locations as LocationsDB
from db.taps import Taps as TapsDB
from db.beers import Beers as BeersDB
from db.beverages import Beverages as BeveragesDB
from db.sensors import Sensors as SensorsDB
from services.locations import LocationService
from services.taps import TapService
from services.beers import BeerService
from services.beverages import BeverageService
from services.sensors import SensorService
from lib import util

router = APIRouter(prefix="/api/v1/dashboard", tags=["dashboard"])
LOGGER = logging.getLogger(__name__)


async def get_location_id(location_identifier: str, db_session: AsyncSession) -> str:
    """Get location ID from name or UUID"""
    if util.is_valid_uuid(location_identifier):
        return location_identifier

    locations = await LocationsDB.query(db_session, name=location_identifier)
    if locations:
        return locations[0].id

    return None


@router.get("/locations", response_model=List[dict])
async def list_dashboard_locations(
    db_session: AsyncSession = Depends(get_db_session),
):
    """List all locations for dashboard"""
    locations = await LocationsDB.query(db_session)
    return [await LocationService.transform_response(l, db_session=db_session) for l in locations]


@router.get("/taps/{tap_id}", response_model=dict)
async def get_dashboard_tap(
    tap_id: str,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get a specific tap for dashboard"""
    tap = await TapsDB.get_by_pkey(db_session, tap_id)
    if not tap:
        raise HTTPException(status_code=404, detail="Tap not found")

    return await TapService.transform_response(tap, db_session=db_session)


@router.get("/beers/{beer_id}", response_model=dict)
async def get_dashboard_beer(
    beer_id: str,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get a specific beer for dashboard"""
    beer = await BeersDB.get_by_pkey(db_session, beer_id)
    if not beer:
        raise HTTPException(status_code=404, detail="Beer not found")

    return await BeerService.transform_response(beer, db_session=db_session, skip_meta_refresh=True)


@router.get("/beverages/{beverage_id}", response_model=dict)
async def get_dashboard_beverage(
    beverage_id: str,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get a specific beverage for dashboard"""
    beverage = await BeveragesDB.get_by_pkey(db_session, beverage_id)
    if not beverage:
        raise HTTPException(status_code=404, detail="Beverage not found")

    return await BeverageService.transform_response(beverage, db_session=db_session)


@router.get("/sensors/{sensor_id}", response_model=dict)
async def get_dashboard_sensor(
    sensor_id: str,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get a specific sensor for dashboard"""
    sensor = await SensorsDB.get_by_pkey(db_session, sensor_id)
    if not sensor:
        raise HTTPException(status_code=404, detail="Sensor not found")

    return await SensorService.transform_response(sensor, db_session=db_session)


@router.get("/locations/{location}", response_model=dict)
async def get_dashboard(
    location: str,
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get dashboard data for a specific location"""
    location_id = await get_location_id(location, db_session)
    if not location_id:
        raise HTTPException(status_code=404, detail="Location not found")

    locations = await LocationsDB.query(db_session)
    taps = await TapsDB.query(db_session, locations=[location_id])

    # Find the current location
    current_location = None
    for l in locations:
        if l.id == location_id:
            current_location = l
            break

    if not current_location:
        current_location = await LocationsDB.get_by_pkey(db_session, location_id)

    return {
        "taps": [await TapService.transform_response(t, db_session=db_session, include_location=False) for t in taps],
        "locations": [await LocationService.transform_response(l, db_session=db_session) for l in locations],
        "location": await LocationService.transform_response(current_location, db_session=db_session) if current_location else None
    }
