"""Image transitions router for FastAPI"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import AuthUser, get_db_session, require_user
from db.image_transitions import ImageTransitions as ImageTransitionsDB

router = APIRouter(prefix="/api/v1/image_transitions", tags=["image_transitions"])
LOGGER = logging.getLogger(__name__)


@router.delete("/{image_transition_id}")
async def delete_image_transition(
    image_transition_id: str,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Delete an image transition"""
    image_transition = await ImageTransitionsDB.get_by_pkey(db_session, image_transition_id)

    if not image_transition:
        raise HTTPException(status_code=404, detail="Image transition not found")

    await ImageTransitionsDB.delete(db_session, image_transition_id)
    return True
