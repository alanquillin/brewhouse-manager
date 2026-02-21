"""Tests for services/beverages.py module - Beverage service"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.beverages import BeverageService


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


def create_mock_beverage(
    id_="bev-1",
    name="Test Cider",
    batches=None,
):
    """Helper to create mock beverage"""
    mock_bev = MagicMock()
    mock_bev.id = id_
    mock_bev.name = name
    mock_bev.batches = batches or []

    mock_bev.to_dict.return_value = {
        "id": id_,
        "name": name,
    }

    async def _awaitable_batches():
        return batches or []

    mock_bev.awaitable_attrs = MagicMock()
    mock_bev.awaitable_attrs.batches = _awaitable_batches()

    return mock_bev


class TestBeverageServiceTransformResponse:
    """Tests for BeverageService.transform_response method"""

    def test_returns_none_for_none_input(self):
        """Test returns None when beverage is None"""
        mock_session = AsyncMock()
        result = run_async(BeverageService.transform_response(None, mock_session))
        assert result is None

    def test_basic_transformation(self):
        """Test basic beverage transformation"""
        mock_bev = create_mock_beverage(name="Apple Cider")
        mock_session = AsyncMock()

        with patch("services.beverages.ImageTransitionsDB") as mock_it_db:
            mock_it_db.query = AsyncMock(return_value=[])
            result = run_async(BeverageService.transform_response(mock_bev, mock_session, include_batches=False))

        assert result is not None
        assert result["name"] == "Apple Cider"

    def test_includes_batches_when_requested(self):
        """Test includes batches when include_batches=True"""
        mock_batch = MagicMock()
        mock_bev = create_mock_beverage(batches=[mock_batch])
        mock_session = AsyncMock()

        with patch("services.beverages.ImageTransitionsDB") as mock_it_db, patch(
            "services.batches.BatchService.transform_response", new_callable=AsyncMock
        ) as mock_batch_transform:
            mock_it_db.query = AsyncMock(return_value=[])
            mock_batch_transform.return_value = {"id": "batch-1"}

            result = run_async(BeverageService.transform_response(mock_bev, mock_session, include_batches=True))

        assert "batches" in result
        assert len(result["batches"]) == 1

    def test_includes_image_transitions(self):
        """Test includes image transitions"""
        mock_bev = create_mock_beverage()
        mock_session = AsyncMock()

        mock_transition = MagicMock()
        mock_transition.to_dict.return_value = {"id": "it-1", "img_url": "http://example.com/img.jpg"}

        with patch("services.beverages.ImageTransitionsDB") as mock_it_db:
            mock_it_db.query = AsyncMock(return_value=[mock_transition])
            result = run_async(BeverageService.transform_response(mock_bev, mock_session, include_batches=False))

        assert "imageTransitions" in result
        assert len(result["imageTransitions"]) == 1

    def test_uses_provided_image_transitions(self):
        """Test uses provided image_transitions instead of querying"""
        mock_bev = create_mock_beverage()
        mock_session = AsyncMock()

        mock_transition = MagicMock()
        mock_transition.to_dict.return_value = {"id": "it-provided"}

        with patch("services.beverages.ImageTransitionsDB") as mock_it_db:
            mock_it_db.query = AsyncMock(return_value=[])
            result = run_async(BeverageService.transform_response(mock_bev, mock_session, include_batches=False, image_transitions=[mock_transition]))

        # Should NOT have queried DB since transitions were provided
        mock_it_db.query.assert_not_called()
        assert result["imageTransitions"][0]["id"] == "it-provided"


class TestBeverageServiceProcessImageTransitions:
    """Tests for BeverageService.process_image_transitions method"""

    def test_returns_none_for_empty_data(self):
        """Test returns None for empty/None input"""
        mock_session = AsyncMock()

        result = run_async(BeverageService.process_image_transitions(mock_session, None))
        assert result is None

        result = run_async(BeverageService.process_image_transitions(mock_session, []))
        assert result is None

    def test_creates_new_transitions(self):
        """Test creates new transitions without id"""
        mock_session = AsyncMock()
        transitions = [{"img_url": "http://example.com/img.jpg"}]

        with patch("services.beverages.ImageTransitionsDB") as mock_it_db:
            mock_it_db.create = AsyncMock(return_value=MagicMock())
            result = run_async(BeverageService.process_image_transitions(mock_session, transitions, beverage_id="bev-1"))

        mock_it_db.create.assert_called_once()
        assert len(result) == 1

    def test_updates_existing_transitions(self):
        """Test updates transitions with id"""
        mock_session = AsyncMock()
        transitions = [{"id": "it-1", "img_url": "http://example.com/new.jpg"}]

        with patch("services.beverages.ImageTransitionsDB") as mock_it_db:
            mock_it_db.update = AsyncMock(return_value=MagicMock())
            mock_it_db.get_by_pkey = AsyncMock(return_value=MagicMock())
            result = run_async(BeverageService.process_image_transitions(mock_session, transitions))

        mock_it_db.update.assert_called_once()

    def test_adds_kwargs_to_transition_data(self):
        """Test adds kwargs to each transition"""
        mock_session = AsyncMock()
        transitions = [{"img_url": "http://example.com/img.jpg"}]

        with patch("services.beverages.ImageTransitionsDB") as mock_it_db:
            mock_it_db.create = AsyncMock(return_value=MagicMock())
            run_async(BeverageService.process_image_transitions(mock_session, transitions, beverage_id="bev-123"))

        call_kwargs = mock_it_db.create.call_args[1]
        assert call_kwargs["beverage_id"] == "bev-123"
