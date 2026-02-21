"""Tests for db/users.py module - User model with password handling"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from db.users import Users


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestUsersModel:
    """Tests for Users model class attributes"""

    def test_table_name(self):
        """Test table name is correct"""
        assert Users.__tablename__ == "users"

    def test_has_required_columns(self):
        """Test model has required columns"""
        column_names = [col.name for col in Users.__table__.columns]
        assert "id" in column_names
        assert "email" in column_names
        assert "first_name" in column_names
        assert "last_name" in column_names
        assert "password_hash" in column_names
        assert "admin" in column_names
        assert "api_key" in column_names

    def test_inherits_mixins(self):
        """Test Users inherits required mixins"""
        from db import AsyncQueryMethodsMixin, AuditedMixin, DictifiableMixin

        assert issubclass(Users, DictifiableMixin)
        assert issubclass(Users, AuditedMixin)
        assert issubclass(Users, AsyncQueryMethodsMixin)


class TestUsersCreate:
    """Tests for Users.create method"""

    def test_create_hashes_password(self):
        """Test that create hashes password when provided"""
        mock_session = AsyncMock()

        with patch.object(Users, "__init__", return_value=None), patch("db.users.PasswordHasher") as mock_hasher_class:
            mock_hasher = MagicMock()
            mock_hasher.hash.return_value = "hashed_password"
            mock_hasher_class.return_value = mock_hasher

            # Mock the parent create method
            with patch("db.AsyncQueryMethodsMixin.create", new_callable=AsyncMock) as mock_create:
                mock_create.return_value = MagicMock()
                run_async(Users.create(mock_session, email="test@test.com", password="mypassword"))

                # Verify password was hashed
                mock_hasher.hash.assert_called_once_with("mypassword")
                # Verify parent was called with password_hash
                mock_create.assert_called_once()
                call_kwargs = mock_create.call_args[1]
                assert call_kwargs["password_hash"] == "hashed_password"
                assert "password" not in call_kwargs

    def test_create_skips_hash_if_password_hash_provided(self):
        """Test that create uses provided password_hash directly"""
        mock_session = AsyncMock()

        with patch("db.users.PasswordHasher") as mock_hasher_class, patch("db.AsyncQueryMethodsMixin.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = MagicMock()
            run_async(Users.create(mock_session, email="test@test.com", password="mypassword", password_hash="existing_hash"))

            # Verify PasswordHasher was never instantiated
            mock_hasher_class.assert_not_called()

    def test_create_without_password(self):
        """Test that create works without password"""
        mock_session = AsyncMock()

        with patch("db.users.PasswordHasher") as mock_hasher_class, patch("db.AsyncQueryMethodsMixin.create", new_callable=AsyncMock) as mock_create:
            mock_create.return_value = MagicMock()
            run_async(Users.create(mock_session, email="test@test.com"))

            # Verify PasswordHasher was never instantiated
            mock_hasher_class.assert_not_called()


class TestUsersUpdate:
    """Tests for Users.update method"""

    def test_update_hashes_password(self):
        """Test that update hashes password when provided"""
        mock_session = AsyncMock()

        with patch("db.users.PasswordHasher") as mock_hasher_class:
            mock_hasher = MagicMock()
            mock_hasher.hash.return_value = "new_hashed_password"
            mock_hasher_class.return_value = mock_hasher

            with patch("db.AsyncQueryMethodsMixin.update", new_callable=AsyncMock) as mock_update:
                mock_update.return_value = 1
                run_async(Users.update(mock_session, "user-id", password="newpassword"))

                mock_hasher.hash.assert_called_once_with("newpassword")
                call_kwargs = mock_update.call_args[1]
                assert call_kwargs["password_hash"] == "new_hashed_password"

    def test_update_without_password(self):
        """Test that update works without password"""
        mock_session = AsyncMock()

        with patch("db.users.PasswordHasher") as mock_hasher_class, patch("db.AsyncQueryMethodsMixin.update", new_callable=AsyncMock) as mock_update:
            mock_update.return_value = 1
            run_async(Users.update(mock_session, "user-id", first_name="John"))

            mock_hasher_class.assert_not_called()


class TestUsersDisablePassword:
    """Tests for Users.disable_password method"""

    def test_disable_password_sets_hash_to_none(self):
        """Test that disable_password clears the password hash"""
        mock_session = AsyncMock()

        with patch("db.AsyncQueryMethodsMixin.update", new_callable=AsyncMock) as mock_update:
            mock_update.return_value = 1
            run_async(Users.disable_password(mock_session, "user-id"))

            mock_update.assert_called_once_with(mock_session, "user-id", password_hash=None)


class TestUsersGetByEmail:
    """Tests for Users.get_by_email method"""

    def test_get_by_email_returns_user(self):
        """Test get_by_email returns user when found"""
        mock_session = AsyncMock()
        mock_user = MagicMock()

        with patch.object(Users.__bases__[3], "query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = [mock_user]
            result = run_async(Users.get_by_email(mock_session, "test@test.com"))

            assert result == mock_user

    def test_get_by_email_returns_none_when_not_found(self):
        """Test get_by_email returns None when user not found"""
        mock_session = AsyncMock()

        with patch.object(Users.__bases__[3], "query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = []
            result = run_async(Users.get_by_email(mock_session, "notfound@test.com"))

            assert result is None


class TestUsersGetByApiKey:
    """Tests for Users.get_by_api_key method"""

    def test_get_by_api_key_returns_user(self):
        """Test get_by_api_key returns user when found"""
        mock_session = AsyncMock()
        mock_user = MagicMock()

        with patch.object(Users.__bases__[3], "query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = [mock_user]
            result = run_async(Users.get_by_api_key(mock_session, "api-key-123"))

            assert result == mock_user

    def test_get_by_api_key_returns_none_when_not_found(self):
        """Test get_by_api_key returns None when user not found"""
        mock_session = AsyncMock()

        with patch.object(Users.__bases__[3], "query", new_callable=AsyncMock) as mock_query:
            mock_query.return_value = []
            result = run_async(Users.get_by_api_key(mock_session, "invalid-key"))

            assert result is None
