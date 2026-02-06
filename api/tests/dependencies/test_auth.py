"""Tests for dependencies/auth.py module - FastAPI authentication dependencies"""

import asyncio
import base64
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException, status

from dependencies.auth import (
    AuthUser,
    get_current_user_from_api_key,
    get_current_user_from_session,
    get_optional_user,
    require_admin,
    require_location_access,
    require_user,
)


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


def create_mock_db_user(
    id_="user-1",
    first_name="Test",
    last_name="User",
    email="test@test.com",
    profile_pic=None,
    google_oidc_id=None,
    api_key=None,
    admin=False,
    locations=None,
):
    """Helper to create a mock database user with proper awaitable_attrs"""
    if locations is None:
        locations = []

    mock_user = MagicMock()
    mock_user.id = id_
    mock_user.first_name = first_name
    mock_user.last_name = last_name
    mock_user.email = email
    mock_user.profile_pic = profile_pic
    mock_user.google_oidc_id = google_oidc_id
    mock_user.api_key = api_key
    mock_user.admin = admin
    mock_user.locations = locations

    # Create a proper awaitable for awaitable_attrs.locations
    async def _awaitable_locations():
        return locations

    mock_user.awaitable_attrs = MagicMock()
    mock_user.awaitable_attrs.locations = _awaitable_locations()

    return mock_user


class TestAuthUser:
    """Tests for AuthUser class"""

    def test_init_sets_all_attributes(self):
        """Test __init__ sets all user attributes"""
        locations = [MagicMock(id="loc-1"), MagicMock(id="loc-2")]

        user = AuthUser(
            id_="user-123",
            first_name="John",
            last_name="Doe",
            email="john@test.com",
            profile_pic="http://example.com/pic.jpg",
            google_oidc_id="google-123",
            api_key="api-key-456",
            admin=True,
            locations=locations,
        )

        assert user.id == "user-123"
        assert user.first_name == "John"
        assert user.last_name == "Doe"
        assert user.email == "john@test.com"
        assert user.profile_pic == "http://example.com/pic.jpg"
        assert user.google_oidc_id == "google-123"
        assert user.api_key == "api-key-456"
        assert user.admin is True
        assert user.locations == ["loc-1", "loc-2"]
        assert user.is_authenticated is True

    def test_init_extracts_location_ids(self):
        """Test __init__ extracts just the IDs from location objects"""
        loc1 = MagicMock(id="location-abc")
        loc2 = MagicMock(id="location-xyz")

        user = AuthUser(
            id_="user-1",
            first_name="Test",
            last_name="User",
            email="test@test.com",
            profile_pic=None,
            google_oidc_id=None,
            api_key=None,
            admin=False,
            locations=[loc1, loc2],
        )

        assert user.locations == ["location-abc", "location-xyz"]

    def test_init_with_empty_locations(self):
        """Test __init__ handles empty locations list"""
        user = AuthUser(
            id_="user-1",
            first_name="Test",
            last_name="User",
            email="test@test.com",
            profile_pic=None,
            google_oidc_id=None,
            api_key=None,
            admin=False,
            locations=[],
        )

        assert user.locations == []


class TestAuthUserFromUser:
    """Tests for AuthUser.from_user static method"""

    def test_from_user_returns_none_for_none_input(self):
        """Test from_user returns None when user is None"""
        result = run_async(AuthUser.from_user(None))
        assert result is None

    def test_from_user_creates_auth_user(self):
        """Test from_user creates AuthUser from database user"""
        locations = [MagicMock(id="loc-a"), MagicMock(id="loc-b")]
        mock_db_user = create_mock_db_user(
            id_="user-123",
            first_name="Jane",
            last_name="Smith",
            email="jane@test.com",
            profile_pic="http://example.com/jane.jpg",
            google_oidc_id="google-456",
            api_key="api-789",
            admin=True,
            locations=locations,
        )

        result = run_async(AuthUser.from_user(mock_db_user))

        assert result is not None
        assert result.id == "user-123"
        assert result.first_name == "Jane"
        assert result.last_name == "Smith"
        assert result.email == "jane@test.com"
        assert result.admin is True
        assert result.locations == ["loc-a", "loc-b"]

    def test_from_user_extracts_location_ids(self):
        """Test from_user extracts location IDs correctly"""
        locations = [MagicMock(id="loc-x"), MagicMock(id="loc-y"), MagicMock(id="loc-z")]
        mock_db_user = create_mock_db_user(
            id_="user-1",
            email="test@test.com",
            locations=locations,
        )

        result = run_async(AuthUser.from_user(mock_db_user))

        assert result.locations == ["loc-x", "loc-y", "loc-z"]


class TestGetCurrentUserFromApiKey:
    """Tests for get_current_user_from_api_key dependency"""

    def test_returns_none_when_no_credentials(self):
        """Test returns None when no API key provided"""
        mock_request = MagicMock()
        mock_request.query_params = {}
        mock_session = AsyncMock()

        with patch("dependencies.auth.UsersDB") as mock_users_db:
            result = run_async(get_current_user_from_api_key(credentials=None, request=mock_request, db_session=mock_session))

        assert result is None

    def test_uses_query_param_api_key(self):
        """Test extracts API key from query parameter"""
        mock_request = MagicMock()
        mock_request.query_params = {"api_key": "my-api-key"}
        mock_session = AsyncMock()

        mock_user = create_mock_db_user(
            email="test@test.com",
            api_key="my-api-key",
        )

        with patch("dependencies.auth.UsersDB") as mock_users_db:
            mock_users_db.get_by_api_key = AsyncMock(return_value=mock_user)
            result = run_async(get_current_user_from_api_key(credentials=None, request=mock_request, db_session=mock_session))

        assert result is not None
        assert result.email == "test@test.com"
        mock_users_db.get_by_api_key.assert_called_once_with(mock_session, "my-api-key")

    def test_uses_bearer_token(self):
        """Test extracts API key from Bearer token"""
        mock_request = MagicMock()
        mock_request.query_params = {}
        mock_session = AsyncMock()

        mock_credentials = MagicMock()
        mock_credentials.credentials = "bearer-api-key"

        mock_user = create_mock_db_user(
            email="bearer@test.com",
            api_key="bearer-api-key",
        )

        with patch("dependencies.auth.UsersDB") as mock_users_db:
            mock_users_db.get_by_api_key = AsyncMock(return_value=mock_user)
            result = run_async(get_current_user_from_api_key(credentials=mock_credentials, request=mock_request, db_session=mock_session))

        assert result is not None
        assert result.email == "bearer@test.com"

    def test_decodes_base64_bearer_token(self):
        """Test decodes base64-encoded Bearer token"""
        mock_request = MagicMock()
        mock_request.query_params = {}
        mock_session = AsyncMock()

        # Create base64-encoded API key
        original_key = "my-secret-key"
        encoded_key = base64.b64encode(original_key.encode()).decode()

        mock_credentials = MagicMock()
        mock_credentials.credentials = encoded_key

        mock_user = create_mock_db_user(
            email="base64@test.com",
            api_key=original_key,
        )

        with patch("dependencies.auth.UsersDB") as mock_users_db:
            mock_users_db.get_by_api_key = AsyncMock(return_value=mock_user)
            result = run_async(get_current_user_from_api_key(credentials=mock_credentials, request=mock_request, db_session=mock_session))

        assert result is not None
        mock_users_db.get_by_api_key.assert_called_once_with(mock_session, original_key)

    def test_falls_back_to_raw_key_if_base64_decode_fails(self):
        """Test uses raw key if base64 decode fails"""
        mock_request = MagicMock()
        mock_request.query_params = {}
        mock_session = AsyncMock()

        # Not valid base64
        raw_key = "not-base64-encoded!!!"

        mock_credentials = MagicMock()
        mock_credentials.credentials = raw_key

        mock_user = create_mock_db_user(
            email="raw@test.com",
            api_key=raw_key,
        )

        with patch("dependencies.auth.UsersDB") as mock_users_db:
            mock_users_db.get_by_api_key = AsyncMock(return_value=mock_user)
            result = run_async(get_current_user_from_api_key(credentials=mock_credentials, request=mock_request, db_session=mock_session))

        assert result is not None

    def test_returns_none_for_invalid_api_key(self):
        """Test returns None when API key is not found in database"""
        mock_request = MagicMock()
        mock_request.query_params = {"api_key": "invalid-key"}
        mock_session = AsyncMock()

        with patch("dependencies.auth.UsersDB") as mock_users_db:
            mock_users_db.get_by_api_key = AsyncMock(return_value=None)
            result = run_async(get_current_user_from_api_key(credentials=None, request=mock_request, db_session=mock_session))

        assert result is None

    def test_query_param_takes_precedence(self):
        """Test query param API key is used over Bearer token"""
        mock_request = MagicMock()
        mock_request.query_params = {"api_key": "query-key"}
        mock_session = AsyncMock()

        mock_credentials = MagicMock()
        mock_credentials.credentials = "bearer-key"

        mock_user = create_mock_db_user(
            email="query@test.com",
            api_key="query-key",
        )

        with patch("dependencies.auth.UsersDB") as mock_users_db:
            mock_users_db.get_by_api_key = AsyncMock(return_value=mock_user)
            result = run_async(get_current_user_from_api_key(credentials=mock_credentials, request=mock_request, db_session=mock_session))

        mock_users_db.get_by_api_key.assert_called_once_with(mock_session, "query-key")


class TestGetCurrentUserFromSession:
    """Tests for get_current_user_from_session dependency"""

    def test_returns_none_when_no_session(self):
        """Test returns None when no user_id in session"""
        mock_request = MagicMock()
        mock_request.session = {}
        mock_session = AsyncMock()

        result = run_async(get_current_user_from_session(request=mock_request, db_session=mock_session))

        assert result is None

    def test_returns_user_from_session(self):
        """Test returns user when valid session exists"""
        mock_request = MagicMock()
        mock_request.session = {"user_id": "user-123"}
        mock_session = AsyncMock()

        mock_user = create_mock_db_user(
            id_="user-123",
            first_name="Session",
            last_name="User",
            email="session@test.com",
        )

        with patch("dependencies.auth.UsersDB") as mock_users_db:
            mock_users_db.get_by_pkey = AsyncMock(return_value=mock_user)
            result = run_async(get_current_user_from_session(request=mock_request, db_session=mock_session))

        assert result is not None
        assert result.email == "session@test.com"
        mock_users_db.get_by_pkey.assert_called_once_with(mock_session, "user-123")

    def test_returns_none_when_user_not_found(self):
        """Test returns None when user_id in session but user not in database"""
        mock_request = MagicMock()
        mock_request.session = {"user_id": "deleted-user"}
        mock_session = AsyncMock()

        with patch("dependencies.auth.UsersDB") as mock_users_db:
            mock_users_db.get_by_pkey = AsyncMock(return_value=None)
            result = run_async(get_current_user_from_session(request=mock_request, db_session=mock_session))

        assert result is None


class TestGetOptionalUser:
    """Tests for get_optional_user dependency"""

    def test_returns_api_key_user_if_present(self):
        """Test prefers API key user over session user"""
        api_user = MagicMock()
        api_user.email = "api@test.com"
        session_user = MagicMock()
        session_user.email = "session@test.com"

        result = run_async(get_optional_user(api_key_user=api_user, session_user=session_user))

        assert result == api_user

    def test_returns_session_user_if_no_api_key_user(self):
        """Test falls back to session user when no API key user"""
        session_user = MagicMock()
        session_user.email = "session@test.com"

        result = run_async(get_optional_user(api_key_user=None, session_user=session_user))

        assert result == session_user

    def test_returns_none_when_no_user(self):
        """Test returns None when neither auth method provides user"""
        result = run_async(get_optional_user(api_key_user=None, session_user=None))

        assert result is None


class TestRequireUser:
    """Tests for require_user dependency"""

    def test_returns_user_when_authenticated(self):
        """Test returns user when provided"""
        mock_user = MagicMock()
        mock_user.email = "test@test.com"

        result = run_async(require_user(user=mock_user))

        assert result == mock_user

    def test_raises_401_when_not_authenticated(self):
        """Test raises HTTPException 401 when no user"""
        with pytest.raises(HTTPException) as exc_info:
            run_async(require_user(user=None))

        assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
        assert "not authorized" in exc_info.value.detail.lower()


class TestRequireAdmin:
    """Tests for require_admin dependency"""

    def test_returns_user_when_admin(self):
        """Test returns user when user is admin"""
        mock_user = MagicMock()
        mock_user.admin = True
        mock_user.email = "admin@test.com"

        result = run_async(require_admin(user=mock_user))

        assert result == mock_user

    def test_raises_403_when_not_admin(self):
        """Test raises HTTPException 403 when user is not admin"""
        mock_user = MagicMock()
        mock_user.admin = False

        with pytest.raises(HTTPException) as exc_info:
            run_async(require_admin(user=mock_user))

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "not authorized" in exc_info.value.detail.lower()


class TestRequireLocationAccess:
    """Tests for require_location_access dependency factory"""

    def test_returns_dependency_function(self):
        """Test returns a callable dependency function"""
        dependency = require_location_access("location-123")
        assert callable(dependency)

    def test_allows_admin_any_location(self):
        """Test admin user can access any location"""
        mock_user = MagicMock()
        mock_user.admin = True
        mock_user.locations = []

        dependency = require_location_access("any-location")
        result = run_async(dependency(user=mock_user))

        assert result == mock_user

    def test_allows_user_with_location_access(self):
        """Test user can access location they have permission for"""
        mock_user = MagicMock()
        mock_user.admin = False
        mock_user.locations = ["loc-1", "loc-2", "loc-3"]

        dependency = require_location_access("loc-2")
        result = run_async(dependency(user=mock_user))

        assert result == mock_user

    def test_raises_403_when_no_location_access(self):
        """Test raises 403 when user doesn't have location access"""
        mock_user = MagicMock()
        mock_user.admin = False
        mock_user.locations = ["loc-1", "loc-2"]

        dependency = require_location_access("restricted-loc")

        with pytest.raises(HTTPException) as exc_info:
            run_async(dependency(user=mock_user))

        assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
        assert "restricted-loc" in exc_info.value.detail

    def test_different_locations_create_different_dependencies(self):
        """Test factory creates unique dependencies per location"""
        dep1 = require_location_access("loc-1")
        dep2 = require_location_access("loc-2")

        # They should be different function instances
        assert dep1 is not dep2


class TestModuleExports:
    """Tests for module exports"""

    def test_init_exports_all_dependencies(self):
        """Test __init__.py exports all required dependencies"""
        from dependencies import (
            AuthUser,
            get_current_user_from_api_key,
            get_current_user_from_session,
            get_db_session,
            get_optional_user,
            require_admin,
            require_location_access,
            require_user,
        )

        assert AuthUser is not None
        assert callable(get_db_session)
        assert callable(get_current_user_from_api_key)
        assert callable(get_current_user_from_session)
        assert callable(get_optional_user)
        assert callable(require_user)
        assert callable(require_admin)
        assert callable(require_location_access)

    def test_all_list_contains_exports(self):
        """Test __all__ list contains expected exports"""
        from dependencies import __all__

        expected = [
            "AuthUser",
            "get_db_session",
            "get_current_user_from_api_key",
            "get_current_user_from_session",
            "get_optional_user",
            "require_user",
            "require_admin",
            "require_location_access",
        ]

        for item in expected:
            assert item in __all__
