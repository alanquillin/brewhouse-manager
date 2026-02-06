"""Tests for routers/users.py module - Users router"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


def create_mock_auth_user(id_="user-1", admin=False, locations=None):
    """Helper to create mock AuthUser"""
    mock = MagicMock()
    mock.id = id_
    mock.admin = admin
    mock.locations = locations or []
    return mock


def create_mock_user(
    id_="user-1",
    email="test@example.com",
    first_name="Test",
    last_name="User",
    admin=False,
    api_key="api-key-123",
    locations=None,
):
    """Helper to create mock user"""
    mock = MagicMock()
    mock.id = id_
    mock.email = email
    mock.first_name = first_name
    mock.last_name = last_name
    mock.admin = admin
    mock.api_key = api_key
    mock.locations = locations or []
    return mock


class TestGetCurrentUser:
    """Tests for get_current_user endpoint"""

    def test_returns_current_user(self):
        """Test returns current authenticated user"""
        from routers.users import get_current_user

        mock_auth_user = create_mock_auth_user(id_="user-1")
        mock_user = create_mock_user(id_="user-1")
        mock_session = AsyncMock()

        with patch("routers.users.UsersDB") as mock_db, patch("routers.users.UserService") as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_user)
            mock_service.transform_response = AsyncMock(return_value={"id": "user-1", "email": "test@example.com"})

            result = run_async(get_current_user(mock_auth_user, mock_session))

            assert result["id"] == "user-1"
            assert result["email"] == "test@example.com"

    def test_raises_404_when_user_not_found(self):
        """Test raises 404 when user not found in database"""
        from routers.users import get_current_user

        mock_auth_user = create_mock_auth_user(id_="user-1")
        mock_session = AsyncMock()

        with patch("routers.users.UsersDB") as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_current_user(mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404


class TestListUsers:
    """Tests for list_users endpoint"""

    def test_admin_lists_all_users(self):
        """Test admin can list all users"""
        from routers.users import list_users

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_user1 = create_mock_user(id_="user-1")
        mock_user2 = create_mock_user(id_="user-2")
        mock_session = AsyncMock()

        with patch("routers.users.UsersDB") as mock_db, patch("routers.users.UserService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_user1, mock_user2])
            mock_service.transform_response = AsyncMock(
                side_effect=[
                    {"id": "user-1"},
                    {"id": "user-2"},
                ]
            )

            result = run_async(list_users(mock_auth_user, mock_session))

            assert len(result) == 2


class TestCreateUser:
    """Tests for create_user endpoint"""

    def test_creates_user(self):
        """Test creates user successfully"""
        from routers.users import create_user
        from schemas.users import UserCreate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_user = create_mock_user(id_="new-user")
        mock_session = AsyncMock()
        user_data = UserCreate(email="new@example.com", first_name="New", last_name="User")

        with patch("routers.users.UsersDB") as mock_db, patch("routers.users.UserService") as mock_service:
            mock_db.create = AsyncMock(return_value=mock_user)
            mock_service.transform_response = AsyncMock(return_value={"id": "new-user", "email": "new@example.com"})

            result = run_async(create_user(user_data, mock_auth_user, mock_session))

            mock_db.create.assert_called_once()
            assert result["email"] == "new@example.com"


class TestGetUser:
    """Tests for get_user endpoint"""

    def test_admin_gets_user(self):
        """Test admin can get any user"""
        from routers.users import get_user

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_user = create_mock_user(id_="user-2")
        mock_session = AsyncMock()

        with patch("routers.users.UsersDB") as mock_db, patch("routers.users.UserService") as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_user)
            mock_service.transform_response = AsyncMock(return_value={"id": "user-2"})

            result = run_async(get_user("user-2", mock_auth_user, mock_session))

            assert result["id"] == "user-2"

    def test_raises_404_when_not_found(self):
        """Test raises 404 when user not found"""
        from routers.users import get_user

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()

        with patch("routers.users.UsersDB") as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_user("unknown", mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404


class TestUpdateUser:
    """Tests for update_user endpoint"""

    def test_user_can_update_self(self):
        """Test user can update themselves"""
        from routers.users import update_user
        from schemas.users import UserUpdate

        mock_auth_user = create_mock_auth_user(id_="user-1", admin=False)
        mock_user = create_mock_user(id_="user-1")
        mock_session = AsyncMock()
        update_data = UserUpdate(first_name="Updated")

        with patch("routers.users.UsersDB") as mock_db, patch("routers.users.UserService") as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_user)
            mock_db.update = AsyncMock()
            mock_service.transform_response = AsyncMock(return_value={"id": "user-1", "firstName": "Updated"})

            result = run_async(update_user("user-1", update_data, mock_auth_user, mock_session))

            mock_db.update.assert_called_once()

    def test_non_admin_cannot_update_other_users(self):
        """Test non-admin cannot update other users"""
        from routers.users import update_user
        from schemas.users import UserUpdate

        mock_auth_user = create_mock_auth_user(id_="user-1", admin=False)
        mock_session = AsyncMock()
        update_data = UserUpdate(first_name="Updated")

        with pytest.raises(HTTPException) as exc_info:
            run_async(update_user("user-2", update_data, mock_auth_user, mock_session))

        assert exc_info.value.status_code == 403

    def test_admin_can_update_any_user(self):
        """Test admin can update any user"""
        from routers.users import update_user
        from schemas.users import UserUpdate

        mock_auth_user = create_mock_auth_user(id_="admin-1", admin=True)
        mock_user = create_mock_user(id_="user-2")
        mock_session = AsyncMock()
        update_data = UserUpdate(first_name="Updated")

        with patch("routers.users.UsersDB") as mock_db, patch("routers.users.UserService") as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_user)
            mock_db.update = AsyncMock()
            mock_service.transform_response = AsyncMock(return_value={"id": "user-2"})

            result = run_async(update_user("user-2", update_data, mock_auth_user, mock_session))

            mock_db.update.assert_called_once()

    def test_non_admin_cannot_set_admin(self):
        """Test non-admin cannot change admin status"""
        from routers.users import update_user
        from schemas.users import UserUpdate

        mock_auth_user = create_mock_auth_user(id_="user-1", admin=False)
        mock_user = create_mock_user(id_="user-1", admin=False)
        mock_session = AsyncMock()
        update_data = UserUpdate(admin=True)

        with patch("routers.users.UsersDB") as mock_db, patch("routers.users.UserService") as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_user)
            mock_db.update = AsyncMock()
            mock_service.transform_response = AsyncMock(return_value={"id": "user-1"})

            run_async(update_user("user-1", update_data, mock_auth_user, mock_session))

            # Should NOT include admin in update call
            call_kwargs = mock_db.update.call_args[1] if mock_db.update.call_args else {}
            assert "admin" not in call_kwargs


class TestDeleteUser:
    """Tests for delete_user endpoint"""

    def test_admin_deletes_user(self):
        """Test admin can delete user"""
        from routers.users import delete_user

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_user = create_mock_user(id_="user-2")
        mock_session = AsyncMock()

        with patch("routers.users.UsersDB") as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_user)
            mock_db.delete = AsyncMock()

            result = run_async(delete_user("user-2", mock_auth_user, mock_session))

            assert result is True
            mock_db.delete.assert_called_once()

    def test_raises_404_when_not_found(self):
        """Test raises 404 when user not found"""
        from routers.users import delete_user

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()

        with patch("routers.users.UsersDB") as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(delete_user("unknown", mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404


class TestGetUserApiKey:
    """Tests for get_user_api_key endpoint"""

    def test_user_gets_own_api_key(self):
        """Test user can get their own API key"""
        from routers.users import get_user_api_key

        mock_auth_user = create_mock_auth_user(id_="user-1", admin=False)
        mock_user = create_mock_user(id_="user-1", api_key="my-api-key")
        mock_session = AsyncMock()

        with patch("routers.users.UsersDB") as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_user)

            result = run_async(get_user_api_key("user-1", mock_auth_user, mock_session))

            assert result["apiKey"] == "my-api-key"

    def test_non_admin_cannot_get_other_api_key(self):
        """Test non-admin cannot get another user's API key"""
        from routers.users import get_user_api_key

        mock_auth_user = create_mock_auth_user(id_="user-1", admin=False)
        mock_session = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            run_async(get_user_api_key("user-2", mock_auth_user, mock_session))

        assert exc_info.value.status_code == 403

    def test_admin_gets_any_api_key(self):
        """Test admin can get any user's API key"""
        from routers.users import get_user_api_key

        mock_auth_user = create_mock_auth_user(id_="admin-1", admin=True)
        mock_user = create_mock_user(id_="user-2", api_key="other-api-key")
        mock_session = AsyncMock()

        with patch("routers.users.UsersDB") as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_user)

            result = run_async(get_user_api_key("user-2", mock_auth_user, mock_session))

            assert result["apiKey"] == "other-api-key"


class TestGenerateUserApiKey:
    """Tests for generate_user_api_key endpoint"""

    def test_generates_new_api_key(self):
        """Test generates new API key for user"""
        from routers.users import generate_user_api_key

        mock_auth_user = create_mock_auth_user(id_="user-1", admin=False)
        mock_user = create_mock_user(id_="user-1")
        mock_session = AsyncMock()

        with patch("routers.users.UsersDB") as mock_db, patch("routers.users.uuid") as mock_uuid:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_user)
            mock_db.update = AsyncMock()
            mock_uuid.uuid4.return_value = "new-uuid-key"

            result = run_async(generate_user_api_key("user-1", mock_auth_user, mock_session))

            assert result["apiKey"] == "new-uuid-key"
            mock_db.update.assert_called_once()

    def test_non_admin_cannot_generate_other_api_key(self):
        """Test non-admin cannot generate API key for another user"""
        from routers.users import generate_user_api_key

        mock_auth_user = create_mock_auth_user(id_="user-1", admin=False)
        mock_session = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            run_async(generate_user_api_key("user-2", mock_auth_user, mock_session))

        assert exc_info.value.status_code == 403


class TestDeleteUserApiKey:
    """Tests for delete_user_api_key endpoint"""

    def test_deletes_api_key(self):
        """Test deletes user's API key"""
        from routers.users import delete_user_api_key

        mock_auth_user = create_mock_auth_user(id_="user-1", admin=False)
        mock_user = create_mock_user(id_="user-1", api_key="old-key")
        mock_session = AsyncMock()

        with patch("routers.users.UsersDB") as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_user)
            mock_db.update = AsyncMock()

            result = run_async(delete_user_api_key("user-1", mock_auth_user, mock_session))

            assert result is True
            mock_db.update.assert_called_once_with(mock_session, "user-1", api_key=None)

    def test_non_admin_cannot_delete_other_api_key(self):
        """Test non-admin cannot delete another user's API key"""
        from routers.users import delete_user_api_key

        mock_auth_user = create_mock_auth_user(id_="user-1", admin=False)
        mock_session = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            run_async(delete_user_api_key("user-2", mock_auth_user, mock_session))

        assert exc_info.value.status_code == 403


class TestGetUserLocations:
    """Tests for get_user_locations endpoint"""

    def test_admin_gets_user_locations(self):
        """Test admin can get user locations"""
        from routers.users import get_user_locations

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_location = MagicMock(id="loc-1")
        mock_user = create_mock_user(id_="user-2", locations=[mock_location])
        mock_session = AsyncMock()

        with patch("routers.users.UsersDB") as mock_db, patch("routers.users.LocationService") as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_user)
            mock_service.transform_response = AsyncMock(return_value={"id": "loc-1"})

            result = run_async(get_user_locations("user-2", mock_auth_user, mock_session))

            assert len(result) == 1

    def test_raises_404_when_user_not_found(self):
        """Test raises 404 when user not found"""
        from routers.users import get_user_locations

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()

        with patch("routers.users.UsersDB") as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_user_locations("unknown", mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404


class TestUpdateUserLocations:
    """Tests for update_user_locations endpoint"""

    def test_updates_user_locations(self):
        """Test updates user locations"""
        from routers.users import update_user_locations
        from schemas.users import UserLocationsUpdate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_user = create_mock_user(id_="user-2")
        mock_session = AsyncMock()
        location_data = UserLocationsUpdate(location_ids=["loc-1", "loc-2"])

        with patch("routers.users.UsersDB") as mock_db, patch("routers.users.UserLocationsDB") as mock_user_loc_db:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_user)
            mock_user_loc_db.delete_by = AsyncMock()
            mock_user_loc_db.create = AsyncMock()

            result = run_async(update_user_locations("user-2", location_data, mock_auth_user, mock_session))

            assert result is True
            mock_user_loc_db.delete_by.assert_called_once()
            assert mock_user_loc_db.create.call_count == 2

    def test_raises_404_when_user_not_found(self):
        """Test raises 404 when user not found"""
        from routers.users import update_user_locations
        from schemas.users import UserLocationsUpdate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        location_data = UserLocationsUpdate(location_ids=["loc-1"])

        with patch("routers.users.UsersDB") as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(update_user_locations("unknown", location_data, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404
