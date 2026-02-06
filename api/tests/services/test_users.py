"""Tests for services/users.py module - User service"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from services.users import UserService


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


def create_mock_user(
    id_="user-1",
    first_name="Test",
    last_name="User",
    email="test@test.com",
    profile_pic=None,
    google_oidc_id="google-123",
    api_key="api-key-123",
    password_hash="hashed_password",
    admin=False,
    locations=None,
):
    """Helper to create mock user"""
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
    mock_user.password_hash = password_hash
    mock_user.admin = admin
    mock_user.locations = locations

    mock_user.to_dict.return_value = {
        "id": id_,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "profile_pic": profile_pic,
        "google_oidc_id": google_oidc_id,
        "api_key": api_key,
        "password_hash": password_hash,
        "admin": admin,
    }

    # Make awaitable_attrs.locations awaitable
    async def _awaitable_locations():
        return locations

    mock_user.awaitable_attrs = MagicMock()
    mock_user.awaitable_attrs.locations = _awaitable_locations()

    return mock_user


def create_mock_current_user(id_="current-1", admin=False):
    """Helper to create mock current user"""
    mock = MagicMock()
    mock.id = id_
    mock.admin = admin
    return mock


class TestUserServiceTransformResponse:
    """Tests for UserService.transform_response method"""

    def test_filters_password_hash(self):
        """Test password_hash is filtered from response"""
        mock_user = create_mock_user(password_hash="secret_hash")
        mock_current = create_mock_current_user(admin=True)

        with patch('services.users.transform_dict_to_camel_case', side_effect=lambda x: x):
            result = run_async(UserService.transform_response(mock_user, mock_current))

        assert "password_hash" not in result

    def test_filters_google_oidc_id(self):
        """Test google_oidc_id is filtered from response"""
        mock_user = create_mock_user(google_oidc_id="google-secret")
        mock_current = create_mock_current_user(admin=True)

        with patch('services.users.transform_dict_to_camel_case', side_effect=lambda x: x):
            result = run_async(UserService.transform_response(mock_user, mock_current))

        assert "google_oidc_id" not in result

    def test_adds_password_enabled_true(self):
        """Test password_enabled is True when password_hash exists"""
        mock_user = create_mock_user(password_hash="hashed")
        mock_current = create_mock_current_user(admin=True)

        with patch('services.users.transform_dict_to_camel_case', side_effect=lambda x: x):
            result = run_async(UserService.transform_response(mock_user, mock_current))

        assert result["password_enabled"] is True

    def test_adds_password_enabled_false(self):
        """Test password_enabled is False when no password_hash"""
        mock_user = create_mock_user(password_hash=None)
        mock_user.to_dict.return_value["password_hash"] = None
        mock_current = create_mock_current_user(admin=True)

        with patch('services.users.transform_dict_to_camel_case', side_effect=lambda x: x):
            result = run_async(UserService.transform_response(mock_user, mock_current))

        assert result["password_enabled"] is False

    def test_admin_can_see_other_user_api_key(self):
        """Test admin can see other user's api_key"""
        mock_user = create_mock_user(id_="other-user", api_key="secret-key")
        mock_current = create_mock_current_user(id_="admin-user", admin=True)

        with patch('services.users.transform_dict_to_camel_case', side_effect=lambda x: x):
            result = run_async(UserService.transform_response(mock_user, mock_current))

        assert "api_key" in result
        assert result["api_key"] == "secret-key"

    def test_non_admin_cannot_see_other_user_api_key(self):
        """Test non-admin cannot see other user's api_key"""
        mock_user = create_mock_user(id_="other-user", api_key="secret-key")
        mock_current = create_mock_current_user(id_="regular-user", admin=False)

        with patch('services.users.transform_dict_to_camel_case', side_effect=lambda x: x):
            result = run_async(UserService.transform_response(mock_user, mock_current))

        assert "api_key" not in result

    def test_user_can_see_own_api_key(self):
        """Test user can see their own api_key"""
        mock_user = create_mock_user(id_="user-123", api_key="my-key")
        mock_current = create_mock_current_user(id_="user-123", admin=False)

        with patch('services.users.transform_dict_to_camel_case', side_effect=lambda x: x):
            result = run_async(UserService.transform_response(mock_user, mock_current))

        assert "api_key" in result
        assert result["api_key"] == "my-key"

    def test_includes_locations(self):
        """Test response includes transformed locations"""
        mock_location = MagicMock()
        mock_user = create_mock_user(locations=[mock_location])
        mock_current = create_mock_current_user(admin=True)

        with patch('services.users.transform_dict_to_camel_case', side_effect=lambda x: x), \
             patch('services.locations.LocationService.transform_response', new_callable=AsyncMock) as mock_loc_transform:
            mock_loc_transform.return_value = {"id": "loc-1", "name": "test-loc"}
            result = run_async(UserService.transform_response(mock_user, mock_current))

        assert "locations" in result
        assert len(result["locations"]) == 1
        assert result["locations"][0]["name"] == "test-loc"

    def test_empty_locations(self):
        """Test response with no locations"""
        mock_user = create_mock_user(locations=[])
        mock_current = create_mock_current_user(admin=True)

        with patch('services.users.transform_dict_to_camel_case', side_effect=lambda x: x):
            result = run_async(UserService.transform_response(mock_user, mock_current))

        assert "locations" in result
        assert result["locations"] == []

    def test_transforms_to_camel_case(self):
        """Test response is transformed to camelCase"""
        mock_user = create_mock_user()
        mock_current = create_mock_current_user(admin=True)

        result = run_async(UserService.transform_response(mock_user, mock_current))

        # Should have camelCase keys
        assert "firstName" in result
        assert "lastName" in result
        assert "first_name" not in result
        assert "last_name" not in result
