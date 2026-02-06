"""
Authentication dependencies for FastAPI.
Replaces Flask-Login functionality with FastAPI dependency injection.
"""

import base64
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from db import async_session_scope
from db.users import Users as UsersDB
from lib import logging
from lib.config import Config

CONFIG = Config()
LOGGER = logging.getLogger(__name__)

# Optional bearer token security (doesn't raise 401 if not provided)
security = HTTPBearer(auto_error=False)


class AuthUser:
    """
    FastAPI version of AuthUser (replaces Flask-Login's UserMixin).
    Represents an authenticated user with their permissions.
    """

    def __init__(
        self,
        id_,
        first_name,
        last_name,
        email,
        profile_pic,
        google_oidc_id,
        api_key,
        admin,
        locations,
    ):
        self.id = id_
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.profile_pic = profile_pic
        self.google_oidc_id = google_oidc_id
        self.api_key = api_key
        self.admin = admin
        self.locations = [l.id for l in locations]
        self.is_authenticated = True

    @staticmethod
    async def from_user(user):
        """Create AuthUser from database User model"""
        if not user:
            return None

        await user.awaitable_attrs.locations
        return AuthUser(user.id, user.first_name, user.last_name, user.email, user.profile_pic, user.google_oidc_id, user.api_key, user.admin, user.locations)


async def get_db_session() -> AsyncSession:
    """
    FastAPI dependency that provides an async database session.
    Automatically handles commit/rollback and cleanup.
    """
    async with async_session_scope(CONFIG) as session:
        yield session


async def get_current_user_from_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    request: Request = None,
    db_session: AsyncSession = Depends(get_db_session),
) -> Optional[AuthUser]:
    """
    Check for API key authentication via Bearer token or query parameter.
    Returns AuthUser if valid API key found, None otherwise.
    """
    api_key = None

    # Try query param first (?api_key=...)
    if request:
        api_key = request.query_params.get("api_key")

    LOGGER.debug("api_key: %s", api_key)
    LOGGER.debug("credentials: %s", credentials)
    # Try Bearer token from Authorization header
    if not api_key and credentials:
        api_key = credentials.credentials

        # Try base64 decode (some clients send base64-encoded keys)
        if api_key:
            try:
                LOGGER.debug("API Key (encoded): %s", api_key)
                api_key = base64.b64decode(api_key).decode("ascii")
            except Exception:
                # If decode fails, use the key as-is
                pass

    if api_key:
        user = await UsersDB.get_by_api_key(db_session, api_key)
        if user:
            LOGGER.debug("Authenticated user via API key: %s", user.email)
            return await AuthUser.from_user(user)

    return None


async def get_current_user_from_session(request: Request, db_session: AsyncSession = Depends(get_db_session)) -> Optional[AuthUser]:
    """
    Check for session-based authentication (cookie).
    Returns AuthUser if valid session found, None otherwise.
    """
    user_id = request.session.get("user_id")

    if user_id:
        user = await UsersDB.get_by_pkey(db_session, user_id)
        if user:
            LOGGER.debug("Authenticated user via session: %s", user.email)
            return await AuthUser.from_user(user)

    return None


async def get_optional_user(
    api_key_user: Optional[AuthUser] = Depends(get_current_user_from_api_key),
    session_user: Optional[AuthUser] = Depends(get_current_user_from_session),
) -> Optional[AuthUser]:
    """
    Try API key authentication first, then session authentication.
    Returns AuthUser if authenticated by either method, None otherwise.
    This dependency does NOT raise an error if no authentication is found.
    """
    return api_key_user or session_user


async def require_user(user: Optional[AuthUser] = Depends(get_optional_user)) -> AuthUser:
    """
    Require authentication - raises 401 if not authenticated.
    This is the FastAPI equivalent of Flask-Login's @login_required decorator.

    Usage in router:
        @router.get("/protected")
        async def protected_endpoint(current_user: AuthUser = Depends(require_user)):
            return {"user": current_user.email}
    """
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized. Please login first.",
        )
    return user


async def require_admin(user: AuthUser = Depends(require_user)) -> AuthUser:
    """
    Require admin role - raises 403 if not admin.
    This is the FastAPI equivalent of the @requires_admin decorator.

    Usage in router:
        @router.get("/admin-only")
        async def admin_endpoint(current_user: AuthUser = Depends(require_admin)):
            return {"admin": True}
    """
    if not user.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not authorized to access this resource.",
        )
    return user


def require_location_access(location_id: str):
    """
    Require user has access to a specific location.
    This is a dependency factory that creates a dependency function.

    Usage in router:
        @router.get("/locations/{location_id}/data")
        async def get_location_data(
            location_id: str,
            current_user: AuthUser = Depends(require_location_access(location_id))
        ):
            return {"location_id": location_id}
    """

    async def _check_location_access(user: AuthUser = Depends(require_user)) -> AuthUser:
        if not user.admin and location_id not in user.locations:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You do not have access to location: {location_id}",
            )
        return user

    return _check_location_access
