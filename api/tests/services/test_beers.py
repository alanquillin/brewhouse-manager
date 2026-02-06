"""Tests for services/beers.py module - Beer service"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timezone

from services.beers import BeerService


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


def create_mock_beer(
    id_="beer-1",
    name="Test IPA",
    external_brewing_tool=None,
    external_brewing_tool_meta=None,
    batches=None,
):
    """Helper to create mock beer"""
    mock_beer = MagicMock()
    mock_beer.id = id_
    mock_beer.name = name
    mock_beer.external_brewing_tool = external_brewing_tool
    mock_beer.external_brewing_tool_meta = external_brewing_tool_meta
    mock_beer.batches = batches or []

    mock_beer.to_dict.return_value = {
        "id": id_,
        "name": name,
        "external_brewing_tool": external_brewing_tool,
        "external_brewing_tool_meta": external_brewing_tool_meta,
    }

    async def _awaitable_batches():
        return batches or []

    mock_beer.awaitable_attrs = MagicMock()
    mock_beer.awaitable_attrs.batches = _awaitable_batches()

    return mock_beer


class TestBeerServiceTransformResponse:
    """Tests for BeerService.transform_response method"""

    def test_returns_none_for_none_input(self):
        """Test returns None when beer is None"""
        mock_session = AsyncMock()
        result = run_async(BeerService.transform_response(None, mock_session))
        assert result is None

    def test_basic_transformation(self):
        """Test basic beer transformation"""
        mock_beer = create_mock_beer(name="Test Beer")
        mock_session = AsyncMock()

        with patch('services.beers.ImageTransitionsDB') as mock_it_db:
            mock_it_db.query = AsyncMock(return_value=[])
            result = run_async(BeerService.transform_response(
                mock_beer,
                mock_session,
                skip_meta_refresh=True,
                include_batches=False
            ))

        assert result is not None
        assert result["name"] == "Test Beer"

    def test_includes_batches_when_requested(self):
        """Test includes batches when include_batches=True"""
        mock_batch = MagicMock()
        mock_beer = create_mock_beer(batches=[mock_batch])
        mock_session = AsyncMock()

        with patch('services.beers.ImageTransitionsDB') as mock_it_db, \
             patch('services.batches.BatchService.transform_response', new_callable=AsyncMock) as mock_batch_transform:
            mock_it_db.query = AsyncMock(return_value=[])
            mock_batch_transform.return_value = {"id": "batch-1"}

            result = run_async(BeerService.transform_response(
                mock_beer,
                mock_session,
                skip_meta_refresh=True,
                include_batches=True
            ))

        assert "batches" in result
        assert len(result["batches"]) == 1

    def test_skips_batches_when_not_requested(self):
        """Test skips batches when include_batches=False"""
        mock_beer = create_mock_beer()
        mock_session = AsyncMock()

        with patch('services.beers.ImageTransitionsDB') as mock_it_db:
            mock_it_db.query = AsyncMock(return_value=[])
            result = run_async(BeerService.transform_response(
                mock_beer,
                mock_session,
                skip_meta_refresh=True,
                include_batches=False
            ))

        assert "batches" not in result

    def test_includes_image_transitions(self):
        """Test includes image transitions"""
        mock_beer = create_mock_beer()
        mock_session = AsyncMock()

        mock_transition = MagicMock()
        mock_transition.to_dict.return_value = {"id": "it-1", "img_url": "http://example.com/img.jpg"}

        with patch('services.beers.ImageTransitionsDB') as mock_it_db:
            mock_it_db.query = AsyncMock(return_value=[mock_transition])
            result = run_async(BeerService.transform_response(
                mock_beer,
                mock_session,
                skip_meta_refresh=True,
                include_batches=False
            ))

        assert "imageTransitions" in result
        assert len(result["imageTransitions"]) == 1


class TestBeerServiceStoreMetadata:
    """Tests for BeerService.store_metadata method"""

    def test_adds_last_refreshed_on(self):
        """Test adds _last_refreshed_on timestamp"""
        metadata = {"recipe_id": "123"}
        ex_details = {"name": "Test Recipe"}

        result = BeerService.store_metadata(metadata, ex_details)

        assert "_last_refreshed_on" in result["details"]
        assert result["recipe_id"] == "123"

    def test_uses_provided_now(self):
        """Test uses provided now timestamp"""
        metadata = {}
        ex_details = {}
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        result = BeerService.store_metadata(metadata, ex_details, now=now)

        assert result["details"]["_last_refreshed_on"] == now.isoformat()

    def test_preserves_existing_metadata(self):
        """Test preserves existing metadata fields"""
        metadata = {"recipe_id": "123", "source": "brewfather"}
        ex_details = {"name": "Test"}

        result = BeerService.store_metadata(metadata, ex_details)

        assert result["recipe_id"] == "123"
        assert result["source"] == "brewfather"
        assert "details" in result


class TestBeerServiceProcessImageTransitions:
    """Tests for BeerService.process_image_transitions method"""

    def test_returns_none_for_empty_data(self):
        """Test returns None for empty/None input"""
        mock_session = AsyncMock()

        result = run_async(BeerService.process_image_transitions(mock_session, None))
        assert result is None

        result = run_async(BeerService.process_image_transitions(mock_session, []))
        assert result is None

    def test_creates_new_transitions(self):
        """Test creates new transitions without id"""
        mock_session = AsyncMock()
        transitions = [{"img_url": "http://example.com/img.jpg", "change_percent": 50}]

        with patch('services.beers.ImageTransitionsDB') as mock_it_db:
            mock_it_db.create = AsyncMock(return_value=MagicMock())
            result = run_async(BeerService.process_image_transitions(
                mock_session,
                transitions,
                beer_id="beer-1"
            ))

        mock_it_db.create.assert_called_once()
        assert len(result) == 1

    def test_updates_existing_transitions(self):
        """Test updates transitions with id"""
        mock_session = AsyncMock()
        transitions = [{"id": "it-1", "img_url": "http://example.com/new.jpg"}]

        with patch('services.beers.ImageTransitionsDB') as mock_it_db:
            mock_it_db.update = AsyncMock(return_value=MagicMock())
            result = run_async(BeerService.process_image_transitions(
                mock_session,
                transitions
            ))

        mock_it_db.update.assert_called_once()
        assert len(result) == 1

    def test_handles_pydantic_models(self):
        """Test handles pydantic models with model_dump"""
        mock_session = AsyncMock()

        mock_transition = MagicMock()
        mock_transition.model_dump.return_value = {"img_url": "http://example.com/img.jpg"}

        with patch('services.beers.ImageTransitionsDB') as mock_it_db:
            mock_it_db.create = AsyncMock(return_value=MagicMock())
            result = run_async(BeerService.process_image_transitions(
                mock_session,
                [mock_transition]
            ))

        mock_transition.model_dump.assert_called_once()


class TestBeerServiceVerifyExternalBrewToolRecipe:
    """Tests for BeerService.verify_and_update_external_brew_tool_recipe method"""

    def test_returns_unchanged_without_external_tool(self):
        """Test returns data unchanged when no external tool"""
        request_data = {"name": "Test Beer"}

        result = run_async(BeerService.verify_and_update_external_brew_tool_recipe(request_data))

        assert result == request_data

    def test_raises_error_without_recipe_id(self):
        """Test raises HTTPException when recipe_id missing"""
        from fastapi import HTTPException

        request_data = {
            "name": "Test Beer",
            "external_brewing_tool": "brewfather",
            "external_brewing_tool_meta": {}
        }

        with pytest.raises(HTTPException) as exc_info:
            run_async(BeerService.verify_and_update_external_brew_tool_recipe(request_data))

        assert exc_info.value.status_code == 400
        assert "recipe id is required" in exc_info.value.detail

    def test_raises_error_when_recipe_not_found(self):
        """Test raises HTTPException when recipe not found"""
        from fastapi import HTTPException
        from lib.external_brew_tools.exceptions import ResourceNotFoundError

        request_data = {
            "external_brewing_tool": "brewfather",
            "external_brewing_tool_meta": {"recipe_id": "123"}
        }

        with patch('services.beers.get_external_brewing_tool') as mock_get_tool:
            mock_tool = MagicMock()
            mock_tool.get_recipe_details = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
            mock_get_tool.return_value = mock_tool

            with pytest.raises(HTTPException) as exc_info:
                run_async(BeerService.verify_and_update_external_brew_tool_recipe(request_data))

        assert exc_info.value.status_code == 400
        assert "not found" in exc_info.value.detail

    def test_updates_metadata_on_success(self):
        """Test updates metadata when recipe found"""
        request_data = {
            "external_brewing_tool": "brewfather",
            "external_brewing_tool_meta": {"recipe_id": "123"}
        }

        with patch('services.beers.get_external_brewing_tool') as mock_get_tool:
            mock_tool = MagicMock()
            mock_tool.get_recipe_details = AsyncMock(return_value={"name": "Found Recipe"})
            mock_get_tool.return_value = mock_tool

            result = run_async(BeerService.verify_and_update_external_brew_tool_recipe(request_data))

        assert "details" in result["external_brewing_tool_meta"]
        assert result["external_brewing_tool_meta"]["details"]["name"] == "Found Recipe"
