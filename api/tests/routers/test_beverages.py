"""Tests for routers/beverages.py module - Beverages router"""

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


def create_mock_beverage(id_="bev-1", name="Test Cider"):
    """Helper to create mock beverage"""
    mock = MagicMock()
    mock.id = id_
    mock.name = name
    return mock


class TestListBeverages:
    """Tests for list_beverages endpoint"""

    def test_lists_all_beverages(self):
        """Test lists all beverages"""
        from routers.beverages import list_beverages

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_beverage = create_mock_beverage()

        with patch("routers.beverages.BeveragesDB") as mock_db, patch("routers.beverages.BeverageService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_beverage])
            mock_service.transform_response = AsyncMock(return_value={"id": "bev-1"})

            result = run_async(list_beverages(mock_auth_user, mock_session))

            assert len(result) == 1
            assert result[0]["id"] == "bev-1"


class TestCreateBeverage:
    """Tests for create_beverage endpoint"""

    def test_creates_beverage(self):
        """Test creates beverage successfully"""
        from routers.beverages import create_beverage
        from schemas.beverages import BeverageCreate

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_beverage = create_mock_beverage()
        beverage_data = BeverageCreate(name="New Cider", type="cider")

        with patch("routers.beverages.BeveragesDB") as mock_db, patch("routers.beverages.BeverageService") as mock_service:
            mock_db.create = AsyncMock(return_value=mock_beverage)
            mock_service.process_image_transitions = AsyncMock(return_value=None)
            mock_service.transform_response = AsyncMock(return_value={"id": "bev-1", "name": "New Cider"})

            result = run_async(create_beverage(beverage_data, mock_auth_user, mock_session))

            mock_db.create.assert_called_once()
            assert result["name"] == "New Cider"

    def test_creates_beverage_with_image_transitions(self):
        """Test creates beverage with image transitions"""
        from routers.beverages import create_beverage
        from schemas.beverages import BeverageCreate

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_beverage = create_mock_beverage()
        beverage_data = BeverageCreate(name="New Cider", type="cider", image_transitions=[{"img_url": "http://example.com/img.jpg"}])

        with patch("routers.beverages.BeveragesDB") as mock_db, patch("routers.beverages.BeverageService") as mock_service:
            mock_db.create = AsyncMock(return_value=mock_beverage)
            mock_service.process_image_transitions = AsyncMock(return_value=[{"id": "it-1"}])
            mock_service.transform_response = AsyncMock(return_value={"id": "bev-1"})

            run_async(create_beverage(beverage_data, mock_auth_user, mock_session))

            mock_service.process_image_transitions.assert_called_once()


class TestGetBeverage:
    """Tests for get_beverage endpoint"""

    def test_gets_beverage_by_id(self):
        """Test gets beverage by ID"""
        from routers.beverages import get_beverage

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_beverage = create_mock_beverage()

        with patch("routers.beverages.BeveragesDB") as mock_db, patch("routers.beverages.BeverageService") as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_beverage)
            mock_service.transform_response = AsyncMock(return_value={"id": "bev-1"})

            result = run_async(get_beverage("bev-1", mock_auth_user, mock_session))

            assert result["id"] == "bev-1"

    def test_raises_404_when_not_found(self):
        """Test raises 404 when beverage not found"""
        from routers.beverages import get_beverage

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()

        with patch("routers.beverages.BeveragesDB") as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_beverage("unknown", mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404


class TestUpdateBeverage:
    """Tests for update_beverage endpoint"""

    def test_updates_beverage(self):
        """Test updates beverage successfully"""
        from routers.beverages import update_beverage
        from schemas.beverages import BeverageUpdate

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_beverage = create_mock_beverage()
        update_data = BeverageUpdate(name="Updated Cider")

        with patch("routers.beverages.BeveragesDB") as mock_db, patch("routers.beverages.BeverageService") as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_beverage)
            mock_db.update = AsyncMock()
            mock_service.process_image_transitions = AsyncMock(return_value=None)
            mock_service.transform_response = AsyncMock(return_value={"id": "bev-1", "name": "Updated Cider"})

            result = run_async(update_beverage("bev-1", update_data, mock_auth_user, mock_session))

            mock_db.update.assert_called_once()

    def test_raises_404_when_not_found(self):
        """Test raises 404 when beverage not found"""
        from routers.beverages import update_beverage
        from schemas.beverages import BeverageUpdate

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        update_data = BeverageUpdate(name="Updated")

        with patch("routers.beverages.BeveragesDB") as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(update_beverage("unknown", update_data, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404

    def test_updates_beverage_with_image_transitions(self):
        """Test updates beverage with image transitions"""
        from routers.beverages import update_beverage
        from schemas.beverages import BeverageUpdate

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_beverage = create_mock_beverage()
        update_data = BeverageUpdate(name="Updated Cider", image_transitions=[{"id": "it-1", "img_url": "http://example.com/new.jpg"}])

        with patch("routers.beverages.BeveragesDB") as mock_db, patch("routers.beverages.BeverageService") as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_beverage)
            mock_db.update = AsyncMock()
            mock_service.process_image_transitions = AsyncMock(return_value=[{"id": "it-1"}])
            mock_service.transform_response = AsyncMock(return_value={"id": "bev-1"})

            run_async(update_beverage("bev-1", update_data, mock_auth_user, mock_session))

            mock_service.process_image_transitions.assert_called_once()


class TestDeleteBeverage:
    """Tests for delete_beverage endpoint"""

    def test_deletes_beverage(self):
        """Test deletes beverage successfully"""
        from routers.beverages import delete_beverage

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_beverage = create_mock_beverage()

        with patch("routers.beverages.BeveragesDB") as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_beverage)
            mock_db.delete = AsyncMock()

            result = run_async(delete_beverage("bev-1", mock_auth_user, mock_session))

            assert result is True
            mock_db.delete.assert_called_once()

    def test_raises_404_when_not_found(self):
        """Test raises 404 when beverage not found"""
        from routers.beverages import delete_beverage

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()

        with patch("routers.beverages.BeveragesDB") as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(delete_beverage("unknown", mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404
