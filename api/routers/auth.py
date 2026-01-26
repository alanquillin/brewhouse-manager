"""
Authentication router for FastAPI.
Handles login, logout, and Google OAuth flows.
"""

import logging
import os

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies.auth import get_db_session, require_user, AuthUser
from db.users import Users as UsersDB
from lib.config import Config

router = APIRouter(tags=["auth"])
CONFIG = Config()
LOGGER = logging.getLogger(__name__)

GOOGLE_CALLBACK_URI = "/login/google/callback"

def build_google_redir_uri(request: Request):
    return str(request.base_url).rstrip("/") + GOOGLE_CALLBACK_URI

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
    user = await UsersDB.get_by_email(db_session, login_data.email)

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
    client_secret = CONFIG.get("auth.oidc.google.client_secret")

    if not client_id or not client_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured properly"
        )

    redirect_url = build_google_redir_uri(request)

    # Create flow instance to manage the OAuth 2.0 Authorization Grant Flow
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_url]
            }
        },
        scopes=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"],
    )
    
    flow.redirect_uri = redirect_url

    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true'
    )

    # Store state in session to verify callback
    request.session["oauth_state"] = state

    LOGGER.debug("Redirecting to Google SSO: %s", authorization_url)
    return RedirectResponse(url=authorization_url)


@router.get(GOOGLE_CALLBACK_URI)
async def google_callback(
    request: Request,
    code: str,
    state: str,
    db_session: AsyncSession = Depends(get_db_session)
):
    """
    Handle Google OAuth callback.
    Validates user with Google and creates session.
    """
    if not CONFIG.get("auth.oidc.google.enabled"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Google authentication is disabled"
        )

    # Verify state to prevent CSRF
    stored_state = request.session.get("oauth_state")
    if not stored_state or stored_state != state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter"
        )

    client_id = CONFIG.get("auth.oidc.google.client_id")
    client_secret = CONFIG.get("auth.oidc.google.client_secret")

    redirect_url = build_google_redir_uri(request)

    # Create flow instance
    flow = Flow.from_client_config(
        client_config={
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_url]
            }
        },
        scopes=["openid", "https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile"],
        state=state
    )

    flow.redirect_uri = redirect_url

    # Exchange authorization code for tokens
    flow.fetch_token(code=code)

    # Get credentials and verify ID token
    credentials = flow.credentials
    id_token_jwt = credentials.id_token

    # Verify the token
    try:
        idinfo = id_token.verify_oauth2_token(
            id_token_jwt,
            google_requests.Request(),
            client_id
        )
    except ValueError as e:
        LOGGER.error("Token verification failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

    # Extract user info from verified token
    users_email = idinfo.get("email")
    email_verified = idinfo.get("email_verified")
    unique_id = idinfo.get("sub")
    picture = idinfo.get("picture")
    first_name = idinfo.get("given_name")
    last_name = idinfo.get("family_name")

    LOGGER.debug("User info from Google: %s", idinfo)

    # Verify email
    if not email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User email not verified by Google."
        )

    # Find user in database
    user = await UsersDB.get_by_email(db_session, users_email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No user found for the given Google account. User email must match the Google account email."
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
        await UsersDB.update(db_session, user.id, **update_data)
        # Refresh user after update
        user = await UsersDB.get_by_pkey(db_session, user.id)

    # Clear oauth state from session
    request.session.pop("oauth_state", None)

    # Set session cookie
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
