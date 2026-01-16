"""
Authentication router for FastAPI.
Handles login, logout, and Google OAuth flows.
"""

import json
import logging

import requests
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from oauthlib.oauth2 import WebApplicationClient
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import get_db_session, require_user, AuthUser
from db.users import Users as UsersDB
from lib.config import Config

router = APIRouter(tags=["auth"])
CONFIG = Config()
LOGGER = logging.getLogger(__name__)


class LoginRequest(BaseModel):
    """Request model for password-based login"""

    email: str
    password: str


@router.post("/login")
async def login(
    request: Request, login_data: LoginRequest, db_session: AsyncSession = Depends(get_db_session)
):
    """
    Password-based login endpoint.
    Sets session cookie on successful authentication.
    """
    user = await UsersDB.get_by_email_async(db_session, login_data.email)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user does not have a password set. Please try logging in with google.",
        )

    ph = PasswordHasher()
    try:
        if not ph.verify(user.password_hash, login_data.password):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")
    except VerifyMismatchError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authorized")

    # Set session cookie (replaces Flask-Login's login_user)
    request.session["user_id"] = str(user.id)
    LOGGER.info("User logged in: %s", user.email)

    return True


@router.get("/login/google")
async def google_login(request: Request):
    """
    Initiate Google OAuth flow.
    Redirects user to Google for authentication.
    """
    if not CONFIG.get("auth.oidc.google.enabled"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Google authentication is disabled"
        )

    client_id = CONFIG.get("auth.oidc.google.client_id")
    discovery_url = CONFIG.get("auth.oidc.google.discovery_url")

    # Get Google's OAuth 2.0 configuration
    google_provider_cfg = requests.get(discovery_url).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]

    # Prepare OAuth request
    client = WebApplicationClient(client_id)
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=str(request.base_url) + "callback",
        scope=["openid", "email", "profile"],
    )

    LOGGER.debug("Redirecting to Google SSO: %s", request_uri)
    return RedirectResponse(url=request_uri)


@router.get("/login/google/callback")
async def google_callback(request: Request, code: str, db_session: AsyncSession = Depends(get_db_session)):
    """
    Handle Google OAuth callback.
    Validates user with Google and creates session.
    """
    if not CONFIG.get("auth.oidc.google.enabled"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Google authentication is disabled"
        )

    client_id = CONFIG.get("auth.oidc.google.client_id")
    client_secret = CONFIG.get("auth.oidc.google.client_secret")
    discovery_url = CONFIG.get("auth.oidc.google.discovery_url")

    # Get Google's OAuth 2.0 configuration
    google_provider_cfg = requests.get(discovery_url).json()
    token_endpoint = google_provider_cfg["token_endpoint"]

    # Prepare token request
    client = WebApplicationClient(client_id)
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=str(request.url),
        redirect_url=str(request.base_url).rstrip("/"),
        code=code,
    )

    # Get tokens from Google
    token_response = requests.post(
        token_url, headers=headers, data=body, auth=(client_id, client_secret)
    )

    # Parse the tokens
    client.parse_request_body_response(json.dumps(token_response.json()))

    # Get user info from Google
    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    userinfo = userinfo_response.json()
    LOGGER.debug("User info from Google: %s", userinfo)

    # Verify email
    if not userinfo.get("email_verified"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User email not available or not verified by Google.",
        )

    unique_id = userinfo.get("sub")
    users_email = userinfo.get("email")
    picture = userinfo.get("picture")
    first_name = userinfo.get("given_name")
    last_name = userinfo.get("family_name")

    # Find user in database
    user = await UsersDB.get_by_email_async(db_session, users_email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No user found for the given Google account. User email must match the Google account email.",
        )

    # Update user info from Google if not set
    update_data = {}

    if not user.first_name and first_name:
        LOGGER.debug(
            "User '%s' first name not set in database. Updating from Google: %s",
            users_email,
            first_name,
        )
        update_data["first_name"] = first_name

    if not user.last_name and last_name:
        LOGGER.debug(
            "User '%s' last name not set in database. Updating from Google: %s",
            users_email,
            last_name,
        )
        update_data["last_name"] = last_name

    if not user.google_oidc_id and unique_id:
        LOGGER.debug(
            "User '%s' Google OIDC ID not set in database. Updating from Google: %s",
            users_email,
            unique_id,
        )
        update_data["google_oidc_id"] = unique_id

    if not user.profile_pic and picture:
        LOGGER.debug(
            "User '%s' profile pic URL not set in database. Updating from Google: %s",
            users_email,
            picture,
        )
        update_data["profile_pic"] = picture

    if update_data:
        LOGGER.debug("Updating user account '%s' with missing data: %s", users_email, update_data)
        await UsersDB.update_async(db_session, user.id, **update_data)
        # Refresh user after update
        user = await UsersDB.get_by_pkey(db_session, user.id)

    # Set session cookie (replaces Flask-Login's login_user)
    request.session["user_id"] = str(user.id)
    LOGGER.info("User logged in via Google: %s", user.email)

    # Redirect to management page
    return RedirectResponse(url="/manage")


@router.get("/logout")
async def logout(request: Request):
    """
    Logout endpoint.
    Clears session and redirects to login page.
    """
    request.session.clear()
    return RedirectResponse(url="/login")
