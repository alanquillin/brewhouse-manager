"""Kegtron Device Management Router for FastAPI"""

import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import Integer
from sqlalchemy.ext.asyncio import AsyncSession

from db.batches import Batches as BatchesDB
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
    batch_id: Optional[str] = None


def get_beer_data(batch_d, beer_d, key):
    batch_ext_data = batch_d.get("external_brewing_tool_meta") or {}
    batch_ext_details = batch_ext_data.get("details") or {}
    v = batch_ext_details.get(key)
    if not v:
        v = batch_d.get(key)
    if not v:
        beer_ext_data = beer_d.get("external_brewing_tool_meta") or {}
        beer_ext_details = beer_ext_data.get("details") or {}
        v = beer_ext_details.get(key)
    if not v:
        v = beer_d.get(key)
    return v


async def get_monitor_from_device_and_port(device_id: str, port_num: int, db_session) -> TapMonitorsDB:
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

    return monitor


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

    monitor = await get_monitor_from_device_and_port(device_id, port_num, db_session)

    vol_ml = to_ml(request_data.volume_size, request_data.volume_unit)

    LOGGER.debug("Updating start volume for kegtron device %s on port %d.  Volume: %s ml.", device_id, port_num, vol_ml)
    data = {"volStart": int(vol_ml)}
    if update_date_tapped:
        now = datetime.now()
        data["dateTapped"] = now.strftime("%Y/%m/%d")
        LOGGER.debug("Including the dateTapped value with the user overrides data: val = %s", data["dateTapped"])

    tasks = [
        kegtron_lib.update_user_overrides(data, meta=monitor.meta),
        kegtron_lib.reset_volume(meta=monitor.meta),
        kegtron_lib.reset_kegs_served(meta=monitor.meta),
    ]

    port_data = {}
    if request_data.batch_id:
        batch = await BatchesDB.get_by_pkey(db_session, request_data.batch_id)
        if not batch:
            raise HTTPException(status_code=400, detail=f"Batch with id '{request_data.batch_id}' not found.")

        LOGGER.debug("Batch id set for kegtron rest, attempting to update the kegtron device.")
        if batch.beer_id:
            await batch.awaitable_attrs.beer
            batch_d = batch.to_dict()
            beer_d = batch.beer.to_dict()
            LOGGER.debug("Batch data: %s", batch_d)
            LOGGER.debug("Beer data: %s", beer_d)

            abv = get_beer_data(batch_d, beer_d, "abv")
            if abv:
                port_data["abv"] = abv
            ibu = get_beer_data(batch_d, beer_d, "ibu")
            if ibu:
                port_data["ibu"] = ibu
            srm = get_beer_data(batch_d, beer_d, "srm")
            if srm:
                port_data["srm"] = srm
            style = get_beer_data(batch_d, beer_d, "style")
            if style:
                port_data["style"] = style
            desc = get_beer_data(batch_d, beer_d, "description")
            if desc:
                port_data["userDesc"] = desc
            name = get_beer_data(batch_d, beer_d, "name")
            if name:
                port_data["userName"] = name
            labelUrl = get_beer_data(batch_d, beer_d, "img_url")
            if labelUrl:
                port_data["labelUrl"] = labelUrl
        elif batch.beverage_id:
            await batch.awaitable_attrs.beverage
            port_data["abv"] = 0.0
            port_data["ibu"] = 0
            port_data["srm"] = 40
            port_data["style"] = batch.beverage.type
            port_data["userDesc"] = batch.beverage.description
            port_data["userName"] = batch.beverage.name
            labelUrl = port_data["labelUrl"] = batch.img_url if batch.img_url else batch.beverage.img_url
            if labelUrl:
                port_data["labelUrl"] = labelUrl

    if port_data:
        tasks.append(kegtron_lib.update_port(port_data, meta=monitor.meta))

    results = await asyncio.gather(*tasks)
    for res in results:
        if not res:
            raise HTTPException(status_code=502, detail="Failed to update kegtron device")

    return True


@router.post("/{device_id}/{port_num}/clear", response_model=bool)
async def clear_port(
    device_id: str,
    port_num: int,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):
    kegtron_lib = get_tap_monitor_lib("kegtron-pro")
    if not kegtron_lib:
        raise HTTPException(status_code=400, detail="Kegtron Pro tap monitor support is not enabled")

    monitor = await get_monitor_from_device_and_port(device_id, port_num, db_session)

    port_data = {"abv": 0.0, "ibu": 0, "srm": 0, "style": "", "userDesc": "", "userName": f"Port {port_num + 1}", "labelUrl": ""}

    res = await kegtron_lib.update_port(port_data, meta=monitor.meta)

    if not res:
        raise HTTPException(status_code=502, detail="Failed to update kegtron device")

    return True
