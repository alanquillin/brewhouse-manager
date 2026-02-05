"""Beer router for FastAPI"""

from typing import List, Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import AuthUser, get_db_session, require_admin
from db.plaato_data import PlaatoData as PlaatoDataDB
from lib import logging, util
from lib.devices.plaato_keg import service_handler
from lib.devices.plaato_keg.command_writer import COMMAND_MAPP, sanitize_command, Commands
from services.plaato_keg import PlaatoKegService
from schemas.plaato_keg import PlaatoKegBase, PlaatoKegCreate, PlaatoKegUpdate
from routers import StringValueRequest

router = APIRouter(prefix="/api/v1/devices/plaato_keg", tags=["plaato_keg_device_management"])
LOGGER = logging.getLogger(__name__)


@router.get("", response_model=List[PlaatoKegBase])
async def list(
    request: Request,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):
    """List all beers"""
    devices = await PlaatoDataDB.query(db_session)

    if not devices:
        return []

    return [await PlaatoKegService.transform_response(dev, db_session) for dev in devices]

@router.post("", response_model=PlaatoKegBase)
async def create_device(
    device_data: PlaatoKegCreate,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):    
    data = device_data.model_dump()
    data["id"] = util.random_string(32, include_uppercase=False)

    LOGGER.debug(f"Creating plaato keg device with: {data}")
    dev = await PlaatoDataDB.create(db_session, **data)

    return await PlaatoKegService.transform_response(dev, db_session=db_session)


@router.get("/connected", response_model=Dict[str, Any])
async def list(
    current_user: AuthUser = Depends(require_admin),
):
    """List all beers"""

    return {
        "registered": service_handler.command_writer.connection_handler.get_registered_device_ids(),
        "connections": service_handler.command_writer.connection_handler.get_connection_ids()
    }


@router.get("/{device_id}", response_model=PlaatoKegBase)
async def get(
    device_id: str,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):
    """List all beers"""
    dev = await PlaatoDataDB.get_by_pkey(db_session, device_id)
    if not dev:
        raise HTTPException(status_code=404, detail="Plaato keg device not found")

    return await PlaatoKegService.transform_response(dev, db_session)


@router.patch("/{device_id}", response_model=PlaatoKegBase)
async def update_device(
    device_id: str,
    device_data: PlaatoKegUpdate,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):    
    data = device_data.model_dump()

    LOGGER.debug(f"Updating plaato keg device {device_id} with: {data}")
    await PlaatoDataDB.update(db_session, device_id, **data)

    dev = await PlaatoDataDB.get_by_pkey(db_session, device_id)

    return await PlaatoKegService.transform_response(dev, db_session=db_session)


@router.delete("/{device_id}", response_model=bool)
async def get(
    device_id: str,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):
    """List all beers"""
    dev = await PlaatoDataDB.get_by_pkey(db_session, device_id)
    if not dev:
        raise HTTPException(status_code=404, detail="Plaato keg device not found")

    cnt = await PlaatoDataDB.delete(db_session, device_id)
    
    return True if cnt else False


@router.post("/{device_id}/set/mode", response_model=bool)
async def set_mode(
    device_id: str,
    request: StringValueRequest,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):
    if device_id not in service_handler.command_writer.connection_handler.get_registered_device_ids():
        raise HTTPException(status_code=400, detail=f"Plaato keg '{device_id}' not connected.  Cannot send commands to disconnected devices.")
    
    dev = await PlaatoDataDB.get_by_pkey(db_session, device_id)
    if not dev:
        raise HTTPException(status_code=404, detail="Plaato keg device not found")
    
    val = request.value.lower()
    if val not in ["beer", "co2"]:
        raise HTTPException(status_code=400, detail=f"Invalid mode '{val}'.  Must be either 'beer' or 'co2'.")
    
    dev_data = await PlaatoKegService.transform_response(dev, db_session)

    if dev_data.get("mode") == val:
        LOGGER.info(f"Request for setting plaato keg device {device_id} mode to {val} is being ignored.... mode is already {val}")
        return True
    
    command_writer = service_handler.command_writer
    if val == "co2":
        return await command_writer.send_command(device_id, Commands.SET_MODE, "02")
    
    return await command_writer.send_command(device_id, Commands.SET_MODE, "01")
    


@router.post("/{device_id}/set/unit_type", response_model=bool)
async def set_unit_type(
    device_id: str,
    request: StringValueRequest,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):
    if device_id not in service_handler.command_writer.connection_handler.get_registered_device_ids():
        raise HTTPException(status_code=400, detail=f"Plaato keg '{device_id}' not connected.  Cannot send commands to disconnected devices.")
    
    dev = await PlaatoDataDB.get_by_pkey(db_session, device_id)
    if not dev:
        raise HTTPException(status_code=404, detail="Plaato keg device not found")
    
    val = request.value.lower()
    if val not in ["us", "metric"]:
        raise HTTPException(status_code=400, detail=f"Invalid unit type/system '{val}'.  Must be either 'us' or 'metric'.")
    
    dev_data = await PlaatoKegService.transform_response(dev, db_session)

    if dev_data.get("unitType") == val:
        LOGGER.info(f"Request for setting plaato keg device {device_id} unit type to {val} is being ignored.... unit type is already {val}")
        return True
    
    command_writer = service_handler.command_writer
    unit_mode = dev_data.get("unitMode")
    LOGGER.debug(f"Updating unit type to {val}.  Exiting unit type: {dev_data.get("unitType")}, unit mode: {unit_mode}")
    if val == "us":
        if unit_mode == "volume":
            LOGGER.debug("Setting (us/volume): Unit = 02, measure_unit = 02")
            await command_writer.send_command(device_id, Commands.SET_UNIT, "02")
            await command_writer.send_command(device_id, Commands.SET_MEASURE_UNIT, "02")
            return True
        
        LOGGER.debug("Setting (us/weight): Unit = 02, measure_unit = 01")
        await command_writer.send_command(device_id, Commands.SET_UNIT, "02")
        await command_writer.send_command(device_id, Commands.SET_MEASURE_UNIT, "01")
        return True
    
    if unit_mode == "volume":
        LOGGER.debug("Setting (metric/volume): Unit = 01, measure_unit = 02")
        await command_writer.send_command(device_id, Commands.SET_UNIT, "01")
        await command_writer.send_command(device_id, Commands.SET_MEASURE_UNIT, "02")
        return True
    
    LOGGER.debug("Setting: Unit = 01, measure_unit = 01")
    await command_writer.send_command(device_id, Commands.SET_UNIT, "01")
    await command_writer.send_command(device_id, Commands.SET_MEASURE_UNIT, "01")
    return True
    
@router.post("/{device_id}/set/unit_mode", response_model=bool)
async def set_unit_mode(
    device_id: str,
    request: StringValueRequest,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):
    if device_id not in service_handler.command_writer.connection_handler.get_registered_device_ids():
        raise HTTPException(status_code=400, detail=f"Plaato keg '{device_id}' not connected.  Cannot send commands to disconnected devices.")
    
    dev = await PlaatoDataDB.get_by_pkey(db_session, device_id)
    if not dev:
        raise HTTPException(status_code=404, detail="Plaato keg device not found")
    
    val = request.value.lower()
    if val not in ["weight", "volume"]:
        raise HTTPException(status_code=400, detail=f"Invalid unit mode '{val}'.  Must be either 'weight' or 'volume'.")
    
    dev_data = await PlaatoKegService.transform_response(dev, db_session)

    if dev_data.get("unitMode") == val:
        LOGGER.info(f"Request for setting plaato keg device {device_id} unit mode to {val} is being ignored.... unit mode is already {val}")
        return True
    
    command_writer = service_handler.command_writer
    unit_type = dev_data.get("unitType")
    LOGGER.debug(f"Updating unit mode to {val}.  Exiting unit mode: {dev_data.get("unitMode")}, unit type: {unit_type}")
    if val == "volume":
        if unit_type == "us":
            LOGGER.debug("Setting: Unit = 02, measure_unit = 02")
            await command_writer.send_command(device_id, Commands.SET_UNIT, "02")
            await command_writer.send_command(device_id, Commands.SET_MEASURE_UNIT, "02")
            return True
        
        LOGGER.debug("Setting: Unit = 01, measure_unit = 02")
        await command_writer.send_command(device_id, Commands.SET_UNIT, "01")
        await command_writer.send_command(device_id, Commands.SET_MEASURE_UNIT, "02")
        return True
    
    if unit_type == "us":
        LOGGER.debug("Setting: Unit = 02, measure_unit = 01")
        await command_writer.send_command(device_id, Commands.SET_UNIT, "02")
        await command_writer.send_command(device_id, Commands.SET_MEASURE_UNIT, "01")
        return True
    
    LOGGER.debug("Setting: Unit = 01, measure_unit = 01")
    await command_writer.send_command(device_id, Commands.SET_UNIT, "01")
    await command_writer.send_command(device_id, Commands.SET_MEASURE_UNIT, "01")
    return True

@router.post("/{device_id}/set/{key}", response_model=bool)
async def set_value(
    device_id: str,
    key: str,
    request: Optional[StringValueRequest] = None,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):
    if device_id not in service_handler.command_writer.connection_handler.get_registered_device_ids():
        raise HTTPException(status_code=400, detail=f"Plaato keg '{device_id}' not connected.  Cannot send commands to disconnected devices.")
    
    dev = await PlaatoDataDB.get_by_pkey(db_session, device_id)
    if not dev:
        raise HTTPException(status_code=404, detail="Plaato keg device not found")
    
    key = key.lower()
    if key not in ["empty_keg_weight", "max_keg_volume"]:
        raise HTTPException(status_code=400, detail=f"Invalid keg data data key '{key}'")
    
    command = sanitize_command(f"set_{key}")
    if command not in COMMAND_MAPP.keys():
        raise HTTPException(status_code=400, detail=f"Invalid keg command '{command}'")

    command_writer = service_handler.command_writer
    val = None
    if request:
        val = request.value
    
    LOGGER.debug(f"Attempting to send device command: {command}, data: {val}")
    try:
        return await command_writer.send_command(device_id, command, val)
    except Exception:
        LOGGER.error(f"An unhandled exception when writing command {command} to keg {device_id}", stack_info=True, exc_info=True)
    
    return False
