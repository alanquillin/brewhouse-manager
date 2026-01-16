"""Users router for FastAPI"""

import logging
from typing import List
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import AuthUser, get_db_session, require_user, require_admin
from db.users import Users as UsersDB
from services.users import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])
LOGGER = logging.getLogger(__name__)


class UserCreate(BaseModel):
    """Schema for creating a user"""

    email: str
    first_name: str | None = None
    last_name: str | None = None
    admin: bool = False
    password: str | None = None


class UserUpdate(BaseModel):
    """Schema for updating a user"""

    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    admin: bool | None = None
    password: str | None = None


@router.get("/current", response_model=dict)
async def get_current_user(
    current_user: AuthUser = Depends(require_user), db_session: AsyncSession = Depends(get_db_session)
):
    """Get current authenticated user"""
    user = await UsersDB.get_by_pkey(db_session, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return await UserService.transform_response(user, current_user)


@router.get("", response_model=List[dict])
async def list_users(
    current_user: AuthUser = Depends(require_admin), db_session: AsyncSession = Depends(get_db_session)
):
    """List all users (admin only)"""
    users = await UsersDB.query(db_session)
    return [await UserService.transform_response(u, current_user) for u in users]


@router.post("", response_model=dict)
async def create_user(
    user_data: UserCreate,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Create a new user (admin only)"""
    data = user_data.model_dump(exclude_unset=True)
    LOGGER.debug("Creating user with: %s", data)

    user = await UsersDB.create_async(db_session, **data)
    return await UserService.transform_response(user, current_user)


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: str,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get a specific user (admin only)"""
    user = await UsersDB.get_by_pkey(db_session, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return await UserService.transform_response(user, current_user)


@router.patch("/{user_id}", response_model=dict)
async def update_user(
    user_id: str,
    user_data: UserUpdate,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Update a user"""
    # Users can only update themselves unless they're admin
    if user_id != str(current_user.id) and not current_user.admin:
        raise HTTPException(status_code=403, detail="Not authorized to update this user")

    user = await UsersDB.get_by_pkey(db_session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    data = user_data.model_dump(exclude_unset=True)

    # Non-admins cannot change admin status
    if "admin" in data and not current_user.admin:
        del data["admin"]

    LOGGER.debug("Updating user %s with data: %s", user_id, data)

    if data:
        user = await UsersDB.update_async(db_session, user_id, **data)

    return await UserService.transform_response(user, current_user)


@router.delete("/{user_id}")
async def delete_user(
    user_id: str,
    current_user: AuthUser = Depends(require_admin),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Delete a user (admin only)"""
    user = await UsersDB.get_by_pkey(db_session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await UsersDB.delete(db_session, user.id)
    return True


@router.get("/{user_id}/api_key", response_model=dict)
async def get_user_api_key(
    user_id: str,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Get user's API key"""
    # Users can only get their own API key unless they're admin
    if user_id != str(current_user.id) and not current_user.admin:
        raise HTTPException(status_code=403, detail="Not authorized to view this API key")

    user = await UsersDB.get_by_pkey(db_session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {"apiKey": user.api_key}


@router.post("/{user_id}/api_key/generate", response_model=dict)
async def generate_user_api_key(
    user_id: str,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Generate a new API key for user"""
    # Users can only generate their own API key unless they're admin
    if user_id != str(current_user.id) and not current_user.admin:
        raise HTTPException(status_code=403, detail="Not authorized to generate API key for this user")

    user = await UsersDB.get_by_pkey(db_session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Generate new API key
    new_api_key = str(uuid.uuid4())
    user = await UsersDB.update(db_session, user_id, api_key=new_api_key)

    return {"apiKey": user.api_key}


@router.delete("/{user_id}/api_key")
async def delete_user_api_key(
    user_id: str,
    current_user: AuthUser = Depends(require_user),
    db_session: AsyncSession = Depends(get_db_session),
):
    """Delete user's API key"""
    # Users can only delete their own API key unless they're admin
    if user_id != str(current_user.id) and not current_user.admin:
        raise HTTPException(status_code=403, detail="Not authorized to delete API key for this user")

    user = await UsersDB.get_by_pkey(db_session, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await UsersDB.update(db_session, user_id, api_key=None)
    return True
