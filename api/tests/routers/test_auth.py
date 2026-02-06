"""Tests for routers/auth.py module - Authentication router"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


def create_mock_request(session=None):
    """Helper to create mock request"""
    mock_request = MagicMock()
    mock_request.session = session or {}
    mock_request.base_url = "http://localhost:8000/"
    return mock_request


def create_mock_user(
    id_="user-1",
    email="test@example.com",
    password_hash="$argon2id$v=19$m=65536,t=3,p=4$...",
    first_name="Test",
    last_name="User",
):
    """Helper to create mock user"""
    mock_user = MagicMock()
    mock_user.id = id_
    mock_user.email = email
    mock_user.password_hash = password_hash
    mock_user.first_name = first_name
    mock_user.last_name = last_name
    mock_user.google_oidc_id = None
    mock_user.profile_pic = None
    return mock_user


class TestBuildGoogleRedirUri:
    """Tests for build_google_redir_uri helper"""

    def test_builds_callback_uri(self):
        """Test builds correct callback URI"""
        from routers.auth import build_google_redir_uri

        mock_request = MagicMock()
        mock_request.base_url = "http://localhost:8000/"

        result = build_google_redir_uri(mock_request)

        assert result == "http://localhost:8000/login/google/callback"

    def test_strips_trailing_slash(self):
        """Test strips trailing slash from base_url"""
        from routers.auth import build_google_redir_uri

        mock_request = MagicMock()
        mock_request.base_url = "https://example.com/"

        result = build_google_redir_uri(mock_request)

        assert result == "https://example.com/login/google/callback"


class TestLogin:
    """Tests for login endpoint"""

    def test_successful_login(self):
        """Test successful password login"""
        from routers.auth import LoginRequest, login

        mock_request = create_mock_request()
        mock_user = create_mock_user(password_hash="hashed_password")
        mock_session = AsyncMock()
        login_data = LoginRequest(email="test@example.com", password="password123")

        with patch("routers.auth.UsersDB") as mock_users_db, patch("routers.auth.PasswordHasher") as mock_ph_class:
            mock_users_db.get_by_email = AsyncMock(return_value=mock_user)
            mock_ph = MagicMock()
            mock_ph.verify.return_value = True
            mock_ph_class.return_value = mock_ph

            result = run_async(login(mock_request, login_data, mock_session))

            assert result is True
            assert mock_request.session["user_id"] == "user-1"

    def test_login_user_not_found(self):
        """Test login fails when user not found"""
        from routers.auth import LoginRequest, login

        mock_request = create_mock_request()
        mock_session = AsyncMock()
        login_data = LoginRequest(email="unknown@example.com", password="password123")

        with patch("routers.auth.UsersDB") as mock_users_db:
            mock_users_db.get_by_email = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(login(mock_request, login_data, mock_session))

            assert exc_info.value.status_code == 401

    def test_login_no_password_set(self):
        """Test login fails when user has no password set"""
        from routers.auth import LoginRequest, login

        mock_request = create_mock_request()
        mock_user = create_mock_user(password_hash=None)
        mock_session = AsyncMock()
        login_data = LoginRequest(email="test@example.com", password="password123")

        with patch("routers.auth.UsersDB") as mock_users_db:
            mock_users_db.get_by_email = AsyncMock(return_value=mock_user)

            with pytest.raises(HTTPException) as exc_info:
                run_async(login(mock_request, login_data, mock_session))

            assert exc_info.value.status_code == 400
            assert "password" in exc_info.value.detail.lower()

    def test_login_wrong_password(self):
        """Test login fails with wrong password"""
        from argon2.exceptions import VerifyMismatchError

        from routers.auth import LoginRequest, login

        mock_request = create_mock_request()
        mock_user = create_mock_user(password_hash="hashed_password")
        mock_session = AsyncMock()
        login_data = LoginRequest(email="test@example.com", password="wrong_password")

        with patch("routers.auth.UsersDB") as mock_users_db, patch("routers.auth.PasswordHasher") as mock_ph_class:
            mock_users_db.get_by_email = AsyncMock(return_value=mock_user)
            mock_ph = MagicMock()
            mock_ph.verify.side_effect = VerifyMismatchError()
            mock_ph_class.return_value = mock_ph

            with pytest.raises(HTTPException) as exc_info:
                run_async(login(mock_request, login_data, mock_session))

            assert exc_info.value.status_code == 401


class TestGoogleLogin:
    """Tests for google_login endpoint"""

    def test_google_login_disabled(self):
        """Test google login raises 403 when disabled"""
        from routers.auth import google_login

        mock_request = create_mock_request()

        with patch("routers.auth.CONFIG") as mock_config:
            mock_config.get.return_value = False

            with pytest.raises(HTTPException) as exc_info:
                run_async(google_login(mock_request))

            assert exc_info.value.status_code == 403

    def test_google_login_not_configured(self):
        """Test google login raises 500 when not configured"""
        from routers.auth import google_login

        mock_request = create_mock_request()

        with patch("routers.auth.CONFIG") as mock_config:
            mock_config.get.side_effect = lambda key: {
                "auth.oidc.google.enabled": True,
                "auth.oidc.google.client_id": None,
                "auth.oidc.google.client_secret": None,
            }.get(key)

            with pytest.raises(HTTPException) as exc_info:
                run_async(google_login(mock_request))

            assert exc_info.value.status_code == 500

    def test_google_login_redirects(self):
        """Test google login returns redirect response"""
        from fastapi.responses import RedirectResponse

        from routers.auth import google_login

        mock_request = create_mock_request()

        with patch("routers.auth.CONFIG") as mock_config, patch("routers.auth.Flow") as mock_flow_class:
            mock_config.get.side_effect = lambda key: {
                "auth.oidc.google.enabled": True,
                "auth.oidc.google.client_id": "client_id",
                "auth.oidc.google.client_secret": "client_secret",
            }.get(key)

            mock_flow = MagicMock()
            mock_flow.authorization_url.return_value = ("https://accounts.google.com/auth", "state123")
            mock_flow_class.from_client_config.return_value = mock_flow

            result = run_async(google_login(mock_request))

            assert isinstance(result, RedirectResponse)
            assert mock_request.session["oauth_state"] == "state123"


class TestGoogleCallback:
    """Tests for google_callback endpoint"""

    def test_google_callback_disabled(self):
        """Test google callback raises 403 when disabled"""
        from routers.auth import google_callback

        mock_request = create_mock_request(session={"oauth_state": "state123"})
        mock_session = AsyncMock()

        with patch("routers.auth.CONFIG") as mock_config:
            mock_config.get.return_value = False

            with pytest.raises(HTTPException) as exc_info:
                run_async(google_callback(mock_request, "code", "state123", mock_session))

            assert exc_info.value.status_code == 403

    def test_google_callback_invalid_state(self):
        """Test google callback raises 400 for invalid state"""
        from routers.auth import google_callback

        mock_request = create_mock_request(session={"oauth_state": "different_state"})
        mock_session = AsyncMock()

        with patch("routers.auth.CONFIG") as mock_config:
            mock_config.get.return_value = True

            with pytest.raises(HTTPException) as exc_info:
                run_async(google_callback(mock_request, "code", "state123", mock_session))

            assert exc_info.value.status_code == 400
            assert "state" in exc_info.value.detail.lower()

    def test_google_callback_no_state_stored(self):
        """Test google callback raises 400 when no state stored"""
        from routers.auth import google_callback

        mock_request = create_mock_request(session={})
        mock_session = AsyncMock()

        with patch("routers.auth.CONFIG") as mock_config:
            mock_config.get.return_value = True

            with pytest.raises(HTTPException) as exc_info:
                run_async(google_callback(mock_request, "code", "state123", mock_session))

            assert exc_info.value.status_code == 400


class TestLogout:
    """Tests for logout endpoint"""

    def test_logout_clears_session(self):
        """Test logout clears session"""
        from fastapi.responses import RedirectResponse

        from routers.auth import logout

        session = {"user_id": "user-1", "other_data": "value"}
        mock_request = create_mock_request(session=session)

        result = run_async(logout(mock_request))

        assert isinstance(result, RedirectResponse)
        # Session should be cleared
        assert len(mock_request.session) == 0

    def test_logout_redirects_to_login(self):
        """Test logout redirects to login page"""
        from routers.auth import logout

        mock_request = create_mock_request()

        result = run_async(logout(mock_request))

        assert result.status_code == 307
        assert result.headers["location"] == "/login"
