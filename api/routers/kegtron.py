"""Kegtron Device Management Router for FastAPI"""
import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import Integer
from sqlalchemy.ext.asyncio import AsyncSession

from db.tap_monitors import TapMonitors as TapMonitorsDB
from dependencies.auth import AuthUser, get_db_session, require_admin
from lib import logging
from lib.tap_monitors import get_tap_monitor_lib
from lib.units import to_ml
from schemas.base import CamelCaseModel

router = APIRouter(prefix="/api/v1/devices/kegtron", tags=["kegtron_device_management"])
LOGGER = logging.getLogger(__name__)

VALID_VOLUME_UNITS = ["gal", "l", "ml"]


class ResetPortRequest(CamelCaseModel):
    volume_size: float
    volume_unit: str
    beer_id: Optional[str] = None
    beverage_id: Optional[str] = None


@router.post("/{device_id}/{port_num}", response_model=bool)
async def reset_port(
    device_id: str,
    port_num: int,
    request_data: ResetPortRequest,
    request: Request,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Reset a kegtron port with a new keg volume size"""
    if request_data.volume_unit not in VALID_VOLUME_UNITS:
        raise HTTPException(status_code=400, detail=f"Invalid volume unit '{request_data.volume_unit}'. Must be one of {VALID_VOLUME_UNITS}")

    update_date_tapped = request.query_params.get("update_date_tapped", "false").lower() in ["true", "yes", "", "1"]

    kegtron_lib = get_tap_monitor_lib("kegtron-pro")
    if not kegtron_lib:
        raise HTTPException(status_code=400, detail="Kegtron Pro tap monitor support is not enabled")

    monitors = await TapMonitorsDB.query(
        db_session,
        q_fn=lambda q: q.where(
            TapMonitorsDB.meta["device_id"].astext == device_id,
            TapMonitorsDB.meta["port_num"].astext.cast(Integer) == port_num,
            TapMonitorsDB.monitor_type == "kegtron-pro",
        ),
    )

    monitor = None
    for m in monitors:
        if m.meta.get("port_num") == port_num:
            monitor = m
            break

    if not monitor:
        raise HTTPException(status_code=404, detail=f"Kegtron tap monitor not found for device '{device_id}' port {port_num}")

    vol_ml = to_ml(request_data.volume_size, request_data.volume_unit)

    LOGGER.debug("Updating start volume for kegtron device %s on port %d.  Volume: %s ml.", device_id, port_num, vol_ml)
    data = {"volStart": int(vol_ml)}
    if update_date_tapped:
        now = datetime.now()
        data["dateTapped"] = now.strftime("%Y/%m/%d")
        LOGGER.debug("Including the dateTapped value with the user overrides data: val = %s", data["dateTapped"])

    results = await asyncio.gather(
        kegtron_lib.update_user_overrides(data, meta=monitor.meta),
        kegtron_lib.reset_volume(meta=monitor.meta),
        kegtron_lib.reset_kegs_served(meta=monitor.meta)
    )
    for res in results:
        if not res:
            raise HTTPException(status_code=502, detail="Failed to update kegtron device")

    return True
