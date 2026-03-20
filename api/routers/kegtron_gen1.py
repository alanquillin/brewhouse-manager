"""Kegtron Gen1 Device Management Router for FastAPI"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import Integer
from sqlalchemy.ext.asyncio import AsyncSession

from db.tap_monitors import TapMonitors as TapMonitorsDB
from dependencies.auth import AuthUser, get_db_session, require_admin
from lib import logging
from lib.tap_monitors import get_tap_monitor_lib
from schemas.base import CamelCaseModel

router = APIRouter(prefix="/api/v1/devices/kegtron_gen1", tags=["kegtron_gen1_device_management"])
LOGGER = logging.getLogger(__name__)

VALID_VOLUME_UNITS = ["gal", "l", "ml"]


class ResetVolumeRequest(CamelCaseModel):
    keg_size: float
    start_volume: float
    volume_unit: str
    batch_id: Optional[str] = None


async def get_monitor_from_device_and_port(device_id: str, port_index: int, db_session) -> TapMonitorsDB:
    monitors = await TapMonitorsDB.query(
        db_session,
        q_fn=lambda q: q.where(
            TapMonitorsDB.meta["device_id"].astext == device_id,
            TapMonitorsDB.meta["port_index"].astext.cast(Integer) == port_index,
            TapMonitorsDB.monitor_type == "kegtron-gen1",
        ),
    )

    monitor = None
    for m in monitors:
        if m.meta.get("port_index") == port_index:
            monitor = m
            break

    if not monitor:
        raise HTTPException(status_code=404, detail=f"Kegtron Gen1 tap monitor not found for device '{device_id}' port {port_index}")

    return monitor


@router.post("/{device_id}/{port_index}/reset", response_model=bool)
async def reset_volume(
    device_id: str,
    port_index: int,
    request_data: ResetVolumeRequest,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Reset a kegtron gen1 port with a new keg size and starting volume"""
    if request_data.volume_unit not in VALID_VOLUME_UNITS:
        raise HTTPException(status_code=400, detail=f"Invalid volume unit '{request_data.volume_unit}'. Must be one of {VALID_VOLUME_UNITS}")

    kegtron_gen1_lib = get_tap_monitor_lib("kegtron-gen1")
    if not kegtron_gen1_lib:
        raise HTTPException(status_code=400, detail="Kegtron Gen1 tap monitor support is not enabled")

    monitor = await get_monitor_from_device_and_port(device_id, port_index, db_session)

    LOGGER.debug("Resetting volume for kegtron gen1 device %s on port %d. Keg size: %s, start volume: %s %s", device_id, port_index, request_data.keg_size, request_data.start_volume, request_data.volume_unit)

    result = await kegtron_gen1_lib.reset_volume(
        keg_size=request_data.keg_size,
        start_volume=request_data.start_volume,
        unit=request_data.volume_unit,
        meta=monitor.meta,
    )

    if not result:
        raise HTTPException(status_code=502, detail="Failed to reset volume on kegtron gen1 device")

    return True
