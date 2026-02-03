"""Batches router for FastAPI"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from dependencies.auth import AuthUser, get_db_session, require_user
from db.batches import Batches as BatchesDB
from db.batch_locations import BatchLocations as BatchLocationsDB
from lib import logging
from schemas.batches import BatchCreate, BatchUpdate
from services.batches import BatchService

router = APIRouter()
LOGGER = logging.getLogger(__name__)


class BeerOrBeverageOnlyError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=400,
            detail="You can only associate a beer or a beverage to the selected batch, not both",
        )

@router.get("", response_model=List[dict])
async def list_batches(
    request: Request,
    beer_id: Optional[str] = None,
    beverage_id: Optional[str] = None,
    include_archived: bool = Query(False),
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """List batches, optionally filtered by beer or beverage"""
    kwargs = {}
    if beer_id:
        kwargs["beer_id"] = beer_id
    if beverage_id:
        kwargs["beverage_id"] = beverage_id

    if not include_archived:
        kwargs["archived_on"] = None

    LOGGER.debug(f"GET BATCHES KWARGS: {kwargs}")

    batches = await BatchesDB.query(db_session, **kwargs)

    # Filter batches based on user's location access
    batches_filtered = []
    for b in batches:
        if await BatchService.can_user_see_batch(current_user, batch=b):
            batches_filtered.append(b)

    include_tap_details = request.query_params.get("include_tap_details", "false").lower() in ["true", "yes", "", "1"]
    force_refresh = request.query_params.get("force_refresh", "false").lower() in ["true", "yes", "", "1"]

    return [
        await BatchService.transform_response(
            b,
            db_session=db_session,
            include_tap_details=include_tap_details,
            force_refresh=force_refresh,
        )
        for b in batches_filtered
    ]


@router.post("", response_model=dict)
async def create_batch(
    batch_data: BatchCreate,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Create a new batch"""
    data = batch_data.model_dump(exclude_unset=True)

    data = await BatchService.verify_and_update_external_brew_tool_batch(data)

    # Extract location_ids for separate processing
    location_ids = data.pop("location_ids", None)
    if location_ids:
        if not await BatchService.can_user_see_batch(current_user, location_ids=location_ids):
            raise HTTPException(status_code=403, detail="Not authorized to create batch in these locations")

    # Convert timestamps to datetimes
    for k in ["brew_date", "keg_date", "archived_on"]:
        if k in data and data.get(k):
            data[k] = datetime.fromtimestamp(data.get(k))

    # Handle empty strings as None
    beer_id = data.get("beer_id")
    if beer_id == "":
        beer_id = None
        data["beer_id"] = None
    beverage_id = data.get("beverage_id")
    if beverage_id == "":
        beverage_id = None
        data["beverage_id"] = None

    if beer_id and beverage_id:
        raise BeerOrBeverageOnlyError()

    LOGGER.debug("Creating batch with: %s", data)
    batch = await BatchesDB.create(db_session, **data)

    # Create batch-location associations
    if location_ids:
        for loc_id in location_ids:
            await BatchLocationsDB.create(db_session, batch_id=batch.id, location_id=loc_id)
        # Refresh batch to get locations
        batch = await BatchesDB.get_by_pkey(db_session, batch.id)

    return await BatchService.transform_response(batch, db_session=db_session, skip_meta_refresh=True)


@router.get("/{batch_id}", response_model=dict)
async def get_batch(
    batch_id: str,
    request: Request,
    beer_id: Optional[str] = None,
    beverage_id: Optional[str] = None,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get a specific batch"""
    kwargs = {"id": batch_id}
    if beer_id:
        kwargs["beer_id"] = beer_id
    if beverage_id:
        kwargs["beverage_id"] = beverage_id

    batches = await BatchesDB.query(db_session, **kwargs)
    if not batches:
        raise HTTPException(status_code=404, detail="Batch not found")

    batch = batches[0]

    # Check authorization
    if not await BatchService.can_user_see_batch(current_user, batch=batch):
        raise HTTPException(status_code=403, detail="Not authorized to view this batch")

    include_tap_details = request.query_params.get("include_tap_details", "false").lower() in ["true", "yes", "", "1"]
    force_refresh = request.query_params.get("force_refresh", "false").lower() in ["true", "yes", "", "1"]

    return await BatchService.transform_response(
        batch,
        db_session=db_session,
        include_tap_details=include_tap_details,
        force_refresh=force_refresh,
    )


@router.patch("/{batch_id}", response_model=dict)
async def update_batch(
    batch_id: str,
    batch_data: BatchUpdate,
    beer_id: Optional[str] = None,
    beverage_id: Optional[str] = None,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Update a batch"""
    kwargs = {"id": batch_id}
    if beer_id:
        kwargs["beer_id"] = beer_id
    if beverage_id:
        kwargs["beverage_id"] = beverage_id

    batches = await BatchesDB.query(db_session, **kwargs)
    if not batches:
        raise HTTPException(status_code=404, detail="Batch not found")

    batch = batches[0]

    # Check authorization
    if not await BatchService.can_user_see_batch(current_user, batch=batch):
        raise HTTPException(status_code=403, detail="Not authorized to update this batch")

    data = batch_data.model_dump(exclude_unset=True)

    # Extract location_ids for separate processing
    location_ids = data.pop("location_ids", None)
    if location_ids:
        if not await BatchService.can_user_see_batch(current_user, location_ids=location_ids):
            raise HTTPException(status_code=403, detail="Not authorized to assign batch to these locations")

    # Convert timestamps to datetimes
    for k in ["brew_date", "keg_date", "archived_on"]:
        if k in data and data.get(k):
            data[k] = datetime.fromtimestamp(data.get(k))

    # Handle empty strings as None
    for k, v in data.items():
        if v == "":
            data[k] = None

    # Merge external_brewing_tool_meta if both exist
    external_brewing_tool_meta = data.get("external_brewing_tool_meta", {})
    if external_brewing_tool_meta and batch.external_brewing_tool_meta:
        data["external_brewing_tool_meta"] = {**batch.external_brewing_tool_meta, **external_brewing_tool_meta}

    skip_meta_refresh=False
    # Merge external_brewing_tool_meta if both exist
    external_brewing_tool_meta = data.get("external_brewing_tool_meta", {})
    if external_brewing_tool_meta:
        if batch.external_brewing_tool_meta:
            data["external_brewing_tool_meta"] = {**batch.external_brewing_tool_meta, **external_brewing_tool_meta}
            old_ext_batch_id = batch.external_brewing_tool_meta.get("batch_id")
            new_ext_batch_id = external_brewing_tool_meta.get("batch_id")
            if new_ext_batch_id != old_ext_batch_id:
                LOGGER.info(f"external brew tool batch id for batch ({batch_id}) has changed.  Verifying new id.")
                LOGGER.debug(f"batch ({batch_id}) external brew tool batch id change details: old = {old_ext_batch_id}, new = {new_ext_batch_id}")
                data = await BatchService.verify_and_update_external_brew_tool_batch(data)
                skip_meta_refresh = True

    # Update batch-location associations if provided
    if location_ids:
        await BatchLocationsDB.delete_by(db_session, batch_id=batch_id)
        for loc_id in location_ids:
            await BatchLocationsDB.create(db_session, batch_id=batch.id, location_id=loc_id)

    LOGGER.debug("Updating batch %s with data: %s", batch_id, data)

    if data:
        await BatchesDB.update(db_session, batch.id, **data)

    # Refresh batch to get updated data
    batch = await BatchesDB.get_by_pkey(db_session, batch_id)

    return await BatchService.transform_response(batch, db_session=db_session, skip_meta_refresh=skip_meta_refresh)


@router.delete("/{batch_id}")
async def delete_batch(
    batch_id: str,
    beer_id: Optional[str] = None,
    beverage_id: Optional[str] = None,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Delete a batch"""
    kwargs = {"id": batch_id}
    if beer_id:
        kwargs["beer_id"] = beer_id
    if beverage_id:
        kwargs["beverage_id"] = beverage_id

    batches = await BatchesDB.query(db_session, **kwargs)
    if not batches:
        raise HTTPException(status_code=404, detail="Batch not found")

    batch = batches[0]

    # Check authorization
    if not await BatchService.can_user_see_batch(current_user, batch=batch):
        raise HTTPException(status_code=403, detail="Not authorized to delete this batch")

    await BatchesDB.delete(db_session, batch.id)
    return True
