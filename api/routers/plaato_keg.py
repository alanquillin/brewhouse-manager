"""Plaato Keg Device Management Router for FastAPI"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from db.plaato_data import PlaatoData as PlaatoDataDB
from db.tap_monitors import TapMonitors as TapMonitorsDB
from dependencies.auth import AuthUser, get_db_session, require_admin
from lib import logging, util
from lib.devices.plaato_keg import service_handler
from lib.devices.plaato_keg.command_writer import COMMAND_MAPP, Commands, sanitize_command
from routers import StringValueRequest
from schemas.plaato_keg import PlaatoKegBase, PlaatoKegCreate, PlaatoKegUpdate
from services.plaato_keg import PlaatoKegService

router = APIRouter(prefix="/api/v1/devices/plaato_keg", tags=["plaato_keg_device_management"])
LOGGER = logging.getLogger(__name__)


@router.get("", response_model=List[PlaatoKegBase])
async def get_all(
    request: Request,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):
    """List all devices"""
    devices = await PlaatoDataDB.query(db_session)

    if not devices:
        return []

    return [await PlaatoKegService.transform_response(dev, db_session) for dev in devices]


@router.post("", response_model=PlaatoKegBase, status_code=201)
async def create_device(
    device_data: PlaatoKegCreate,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):
    data = device_data.model_dump()
    data["id"] = util.random_string(32, include_uppercase=False)

    LOGGER.debug("Creating plaato keg device with: %s", data)
    dev = await PlaatoDataDB.create(db_session, **data)

    return await PlaatoKegService.transform_response(dev, db_session=db_session)


@router.get("/connected", response_model=Dict[str, Any])
async def get_all_connected(
    current_user: AuthUser = Depends(require_admin),
):
    """Get all connected to devices"""

    return {
        "registered": service_handler.command_writer.connection_handler.get_registered_device_ids(),
        "connections": service_handler.command_writer.connection_handler.get_connection_ids(),
    }


@router.get("/{device_id}", response_model=PlaatoKegBase)
async def get(
    device_id: str,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get device by id"""
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

    LOGGER.debug("Updating plaato keg device %s with: %s", device_id, data)
    await PlaatoDataDB.update(db_session, device_id, **data)

    dev = await PlaatoDataDB.get_by_pkey(db_session, device_id)
    await db_session.refresh(dev)

    return await PlaatoKegService.transform_response(dev, db_session=db_session)


@router.delete("/{device_id}", status_code=204)
async def delete(
    device_id: str,
    request: Request,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Delete device"""
    dev = await PlaatoDataDB.get_by_pkey(db_session, device_id)
    if not dev:
        raise HTTPException(status_code=404, detail="Plaato keg device not found")

    force_delete_tap_monitor = request.query_params.get("force_delete_tap_monitor", "false").lower() in ["true", "yes", "", "1"]
    referencing_monitors = await TapMonitorsDB.query(
        db_session,
        q_fn=lambda q: q.where(TapMonitorsDB.meta["device_id"].astext == device_id, TapMonitorsDB.monitor_type == "plaato-keg"),
    )
    if referencing_monitors:
        if force_delete_tap_monitor:
            for monitor in referencing_monitors:
                await TapMonitorsDB.delete(db_session, monitor.id)
        else:
            monitor_names = ", ".join(m.name for m in referencing_monitors)
            raise HTTPException(
                status_code=409,
                detail=f"Cannot delete device: it is referenced by tap monitor(s): {monitor_names}",
            )

    cnt = await PlaatoDataDB.delete(db_session, device_id)

    if cnt == 0:
        raise HTTPException(status_code=500, detail="Plaato keg device not deleted")

    return


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
        LOGGER.info("Request for setting plaato keg device %s mode to %s is being ignored.... mode is already %s", device_id, val, val)
        return True

    command_writer = service_handler.command_writer
    cmd_val = "1"
    if val == "co2":
        cmd_val = "2"

    await PlaatoDataDB.update(db_session, device_id, user_keg_mode_c02_beer=cmd_val)
    return await command_writer.send_command(device_id, Commands.SET_MODE, cmd_val)


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
        LOGGER.info("Request for setting plaato keg device %s unit type to %s is being ignored.... unit type is already %s", device_id, val, val)
        return True

    command_writer = service_handler.command_writer
    unit_mode = dev_data.get("unitMode")

    LOGGER.debug("Updating unit type to %s.  Exiting unit type: %s, unit mode: %s", val, dev_data.get("unitType"), unit_mode)
    unit_val = "1"
    measure_unit_val = "1"
    if val == "us":
        if unit_mode == "volume":
            unit_val = "2"
            measure_unit_val = "2"
        else:
            unit_val = "2"
            measure_unit_val = "1"
    elif unit_mode == "volume":
        unit_val = "1"
        measure_unit_val = "2"

    LOGGER.debug("Setting: Unit = 01, measure_unit = 01")
    await PlaatoDataDB.update(db_session, device_id, user_unit=unit_val, user_measure_unit=measure_unit_val)
    await command_writer.send_command(device_id, Commands.SET_UNIT, unit_val)
    await command_writer.send_command(device_id, Commands.SET_MEASURE_UNIT, measure_unit_val)
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
        LOGGER.info("Request for setting plaato keg device %s unit mode to %s is being ignored.... unit mode is already %s", device_id, val, val)
        return True

    command_writer = service_handler.command_writer
    unit_type = dev_data.get("unitType")
    unit_val = "1"
    measure_unit_val = "1"
    if val == "volume":
        if unit_type == "us":
            unit_val = "2"
            measure_unit_val = "2"
        else:
            unit_val = "1"
            measure_unit_val = "2"

    elif unit_type == "us":
        unit_val = "2"
        measure_unit_val = "1"

    await PlaatoDataDB.update(db_session, device_id, user_unit=unit_val, user_measure_unit=measure_unit_val)
    await command_writer.send_command(device_id, Commands.SET_UNIT, unit_val)
    await command_writer.send_command(device_id, Commands.SET_MEASURE_UNIT, measure_unit_val)
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
    if command not in COMMAND_MAPP:
        raise HTTPException(status_code=400, detail=f"Invalid keg command '{command}'")

    command_writer = service_handler.command_writer
    val = None
    if request:
        val = request.value

    LOGGER.debug("Attempting to send device command: %s, data: %s", command, val)
    try:
        return await command_writer.send_command(device_id, command, val)
    except Exception:
        LOGGER.error("An unhandled exception when writing command %s to keg %s", command, device_id, stack_info=True, exc_info=True)

    return False
