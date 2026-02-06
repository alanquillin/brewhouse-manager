"""Tests for routers/beers.py module - Beers router"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
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


def create_mock_beer(id_="beer-1", name="Test Beer"):
    """Helper to create mock beer"""
    mock = MagicMock()
    mock.id = id_
    mock.name = name
    mock.external_brewing_tool = None
    mock.external_brewing_tool_meta = None
    return mock


def create_mock_request(query_params=None):
    """Helper to create mock request"""
    mock = MagicMock()
    mock.query_params = query_params or {}
    return mock


class TestListBeers:
    """Tests for list_beers endpoint"""

    def test_lists_all_beers(self):
        """Test lists all beers"""
        from routers.beers import list_beers

        mock_request = create_mock_request()
        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_beer = create_mock_beer()

        with patch('routers.beers.BeersDB') as mock_db, \
             patch('routers.beers.BeerService') as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_beer])
            mock_service.transform_response = AsyncMock(return_value={"id": "beer-1"})

            result = run_async(list_beers(mock_request, mock_auth_user, mock_session))

            assert len(result) == 1
            assert result[0]["id"] == "beer-1"

    def test_force_refresh_true(self):
        """Test force_refresh=true is passed to transform"""
        from routers.beers import list_beers

        mock_request = create_mock_request(query_params={"force_refresh": "true"})
        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_beer = create_mock_beer()

        with patch('routers.beers.BeersDB') as mock_db, \
             patch('routers.beers.BeerService') as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_beer])
            mock_service.transform_response = AsyncMock(return_value={"id": "beer-1"})

            run_async(list_beers(mock_request, mock_auth_user, mock_session))

            mock_service.transform_response.assert_called_with(
                mock_beer,
                db_session=mock_session,
                force_refresh=True
            )

    def test_force_refresh_false_by_default(self):
        """Test force_refresh defaults to false"""
        from routers.beers import list_beers

        mock_request = create_mock_request(query_params={})
        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_beer = create_mock_beer()

        with patch('routers.beers.BeersDB') as mock_db, \
             patch('routers.beers.BeerService') as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_beer])
            mock_service.transform_response = AsyncMock(return_value={"id": "beer-1"})

            run_async(list_beers(mock_request, mock_auth_user, mock_session))

            mock_service.transform_response.assert_called_with(
                mock_beer,
                db_session=mock_session,
                force_refresh=False
            )


class TestCreateBeer:
    """Tests for create_beer endpoint"""

    def test_creates_beer(self):
        """Test creates beer successfully"""
        from routers.beers import create_beer
        from schemas.beers import BeerCreate

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_beer = create_mock_beer()
        beer_data = BeerCreate(name="New Beer", style="IPA")

        with patch('routers.beers.BeersDB') as mock_db, \
             patch('routers.beers.BeerService') as mock_service:
            mock_db.create = AsyncMock(return_value=mock_beer)
            mock_service.verify_and_update_external_brew_tool_recipe = AsyncMock(
                return_value={"name": "New Beer", "style": "IPA"}
            )
            mock_service.process_image_transitions = AsyncMock(return_value=None)
            mock_service.transform_response = AsyncMock(return_value={"id": "beer-1", "name": "New Beer"})

            result = run_async(create_beer(beer_data, mock_auth_user, mock_session))

            mock_db.create.assert_called_once()
            assert result["name"] == "New Beer"

    def test_creates_beer_with_image_transitions(self):
        """Test creates beer with image transitions"""
        from routers.beers import create_beer
        from schemas.beers import BeerCreate

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_beer = create_mock_beer()
        beer_data = BeerCreate(
            name="New Beer",
            image_transitions=[{"img_url": "http://example.com/img.jpg"}]
        )

        with patch('routers.beers.BeersDB') as mock_db, \
             patch('routers.beers.BeerService') as mock_service:
            mock_db.create = AsyncMock(return_value=mock_beer)
            mock_service.verify_and_update_external_brew_tool_recipe = AsyncMock(
                return_value={"name": "New Beer"}
            )
            mock_service.process_image_transitions = AsyncMock(return_value=[{"id": "it-1"}])
            mock_service.transform_response = AsyncMock(return_value={"id": "beer-1"})

            run_async(create_beer(beer_data, mock_auth_user, mock_session))

            mock_service.process_image_transitions.assert_called_once()


class TestGetBeer:
    """Tests for get_beer endpoint"""

    def test_gets_beer_by_id(self):
        """Test gets beer by ID"""
        from routers.beers import get_beer

        mock_request = create_mock_request()
        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_beer = create_mock_beer()

        with patch('routers.beers.BeersDB') as mock_db, \
             patch('routers.beers.BeerService') as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_beer)
            mock_service.transform_response = AsyncMock(return_value={"id": "beer-1"})

            result = run_async(get_beer("beer-1", mock_request, mock_auth_user, mock_session))

            assert result["id"] == "beer-1"

    def test_raises_404_when_not_found(self):
        """Test raises 404 when beer not found"""
        from routers.beers import get_beer

        mock_request = create_mock_request()
        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()

        with patch('routers.beers.BeersDB') as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_beer("unknown", mock_request, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404


class TestUpdateBeer:
    """Tests for update_beer endpoint"""

    def test_updates_beer(self):
        """Test updates beer successfully"""
        from routers.beers import update_beer
        from schemas.beers import BeerUpdate

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_beer = create_mock_beer()
        update_data = BeerUpdate(name="Updated Beer")

        with patch('routers.beers.BeersDB') as mock_db, \
             patch('routers.beers.BeerService') as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_beer)
            mock_db.update = AsyncMock()
            mock_service.process_image_transitions = AsyncMock(return_value=None)
            mock_service.transform_response = AsyncMock(return_value={"id": "beer-1", "name": "Updated Beer"})

            result = run_async(update_beer("beer-1", update_data, mock_auth_user, mock_session))

            mock_db.update.assert_called_once()

    def test_raises_404_when_not_found(self):
        """Test raises 404 when beer not found"""
        from routers.beers import update_beer
        from schemas.beers import BeerUpdate

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        update_data = BeerUpdate(name="Updated")

        with patch('routers.beers.BeersDB') as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(update_beer("unknown", update_data, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404

    def test_updates_beer_with_image_transitions(self):
        """Test updates beer with image transitions"""
        from routers.beers import update_beer
        from schemas.beers import BeerUpdate

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_beer = create_mock_beer()
        update_data = BeerUpdate(
            name="Updated Beer",
            image_transitions=[{"id": "it-1", "img_url": "http://example.com/new.jpg"}]
        )

        with patch('routers.beers.BeersDB') as mock_db, \
             patch('routers.beers.BeerService') as mock_service:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_beer)
            mock_db.update = AsyncMock()
            mock_service.process_image_transitions = AsyncMock(return_value=[{"id": "it-1"}])
            mock_service.transform_response = AsyncMock(return_value={"id": "beer-1"})

            run_async(update_beer("beer-1", update_data, mock_auth_user, mock_session))

            mock_service.process_image_transitions.assert_called_once()


class TestDeleteBeer:
    """Tests for delete_beer endpoint"""

    def test_deletes_beer(self):
        """Test deletes beer successfully"""
        from routers.beers import delete_beer

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()
        mock_beer = create_mock_beer()

        with patch('routers.beers.BeersDB') as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=mock_beer)
            mock_db.delete = AsyncMock()

            result = run_async(delete_beer("beer-1", mock_auth_user, mock_session))

            assert result is True
            mock_db.delete.assert_called_once()

    def test_raises_404_when_not_found(self):
        """Test raises 404 when beer not found"""
        from routers.beers import delete_beer

        mock_auth_user = create_mock_auth_user()
        mock_session = AsyncMock()

        with patch('routers.beers.BeersDB') as mock_db:
            mock_db.get_by_pkey = AsyncMock(return_value=None)

            with pytest.raises(HTTPException) as exc_info:
                run_async(delete_beer("unknown", mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404
