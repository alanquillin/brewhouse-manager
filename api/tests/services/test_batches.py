"""Tests for services/batches.py module - Batch service"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import date, datetime, timezone

from services.batches import BatchService


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


def create_mock_batch(
    id_="batch-1",
    name="Batch #1",
    external_brewing_tool=None,
    external_brewing_tool_meta=None,
    locations=None,
    brew_date=None,
    keg_date=None,
):
    """Helper to create mock batch"""
    mock_batch = MagicMock()
    mock_batch.id = id_
    mock_batch.name = name
    mock_batch.external_brewing_tool = external_brewing_tool
    mock_batch.external_brewing_tool_meta = external_brewing_tool_meta
    mock_batch.locations = locations or []
    mock_batch.brew_date = brew_date
    mock_batch.keg_date = keg_date

    mock_batch.to_dict.return_value = {
        "id": id_,
        "name": name,
        "external_brewing_tool": external_brewing_tool,
        "external_brewing_tool_meta": external_brewing_tool_meta,
        "brew_date": brew_date,
        "keg_date": keg_date,
    }

    async def _awaitable_locations():
        return locations or []

    mock_batch.awaitable_attrs = MagicMock()
    mock_batch.awaitable_attrs.locations = _awaitable_locations()

    return mock_batch


def create_mock_user(id_="user-1", admin=False, locations=None):
    """Helper to create mock user"""
    mock = MagicMock()
    mock.id = id_
    mock.admin = admin
    mock.locations = locations or []
    return mock


class TestBatchServiceTransformResponse:
    """Tests for BatchService.transform_response method"""

    def test_returns_none_for_none_input(self):
        """Test returns None when batch is None"""
        mock_session = AsyncMock()
        result = run_async(BatchService.transform_response(None, mock_session))
        assert result is None

    def test_basic_transformation(self):
        """Test basic batch transformation"""
        mock_batch = create_mock_batch(name="Test Batch")
        mock_session = AsyncMock()

        result = run_async(BatchService.transform_response(
            mock_batch,
            mock_session,
            skip_meta_refresh=True,
            include_location=False
        ))

        assert result is not None
        assert result["name"] == "Test Batch"

    def test_includes_location_ids(self):
        """Test includes location IDs"""
        loc1 = MagicMock(id="loc-1")
        loc2 = MagicMock(id="loc-2")
        mock_batch = create_mock_batch(locations=[loc1, loc2])
        mock_session = AsyncMock()

        result = run_async(BatchService.transform_response(
            mock_batch,
            mock_session,
            skip_meta_refresh=True,
            include_location=False
        ))

        assert "locationIds" in result
        assert result["locationIds"] == ["loc-1", "loc-2"]

    def test_includes_locations_when_requested(self):
        """Test includes full locations when include_location=True"""
        loc = MagicMock(id="loc-1")
        mock_batch = create_mock_batch(locations=[loc])
        mock_session = AsyncMock()

        with patch('services.locations.LocationService.transform_response', new_callable=AsyncMock) as mock_loc:
            mock_loc.return_value = {"id": "loc-1", "name": "Test Location"}

            result = run_async(BatchService.transform_response(
                mock_batch,
                mock_session,
                skip_meta_refresh=True,
                include_location=True
            ))

        assert "locations" in result
        assert len(result["locations"]) == 1
        assert result["locations"][0]["name"] == "Test Location"

    def test_converts_dates_to_timestamps(self):
        """Test converts date fields to timestamps"""
        brew = date(2024, 1, 15)
        mock_batch = create_mock_batch(brew_date=brew)
        mock_batch.to_dict.return_value["brew_date"] = brew
        mock_session = AsyncMock()

        result = run_async(BatchService.transform_response(
            mock_batch,
            mock_session,
            skip_meta_refresh=True,
            include_location=False
        ))

        # Should be a timestamp (number)
        assert isinstance(result["brewDate"], float)


class TestBatchServiceCanUserSeeBatch:
    """Tests for BatchService.can_user_see_batch method"""

    def test_admin_can_see_any_batch(self):
        """Test admin can always see batch"""
        mock_user = create_mock_user(admin=True, locations=[])
        mock_batch = create_mock_batch()

        async def _awaitable():
            return []
        mock_batch.awaitable_attrs.locations = _awaitable()

        result = run_async(BatchService.can_user_see_batch(mock_user, batch=mock_batch))
        assert result is True

    def test_user_can_see_batch_in_their_location(self):
        """Test user can see batch in their location"""
        mock_user = create_mock_user(admin=False, locations=["loc-1", "loc-2"])
        loc = MagicMock(id="loc-1")
        mock_batch = create_mock_batch(locations=[loc])

        async def _awaitable():
            return [loc]
        mock_batch.awaitable_attrs.locations = _awaitable()

        result = run_async(BatchService.can_user_see_batch(mock_user, batch=mock_batch))
        assert result is True

    def test_user_cannot_see_batch_not_in_their_location(self):
        """Test user cannot see batch not in their locations"""
        mock_user = create_mock_user(admin=False, locations=["loc-1"])
        loc = MagicMock(id="loc-other")
        mock_batch = create_mock_batch(locations=[loc])

        async def _awaitable():
            return [loc]
        mock_batch.awaitable_attrs.locations = _awaitable()

        result = run_async(BatchService.can_user_see_batch(mock_user, batch=mock_batch))
        assert result is False

    def test_uses_provided_location_ids(self):
        """Test can use provided location_ids instead of batch"""
        mock_user = create_mock_user(admin=False, locations=["loc-1"])

        result = run_async(BatchService.can_user_see_batch(
            mock_user,
            location_ids=["loc-1", "loc-2"]
        ))
        assert result is True

    def test_returns_false_for_empty_locations(self):
        """Test returns False when no locations"""
        mock_user = create_mock_user(admin=False, locations=["loc-1"])

        result = run_async(BatchService.can_user_see_batch(
            mock_user,
            location_ids=[]
        ))
        assert result is False


class TestBatchServiceStoreMetadata:
    """Tests for BatchService.store_metadata method"""

    def test_adds_last_refreshed_on(self):
        """Test adds _last_refreshed_on timestamp"""
        metadata = {"batch_id": "123"}
        ex_details = {"status": "Fermenting"}

        result = BatchService.store_metadata(metadata, ex_details)

        assert "_last_refreshed_on" in result["details"]
        assert result["batch_id"] == "123"

    def test_uses_provided_now(self):
        """Test uses provided now timestamp"""
        metadata = {}
        ex_details = {}
        now = datetime(2024, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        result = BatchService.store_metadata(metadata, ex_details, now=now)

        assert result["details"]["_last_refreshed_on"] == now.isoformat()


class TestBatchServiceVerifyExternalBrewToolBatch:
    """Tests for BatchService.verify_and_update_external_brew_tool_batch method"""

    def test_returns_unchanged_without_external_tool(self):
        """Test returns data unchanged when no external tool"""
        request_data = {"name": "Test Batch"}

        result = run_async(BatchService.verify_and_update_external_brew_tool_batch(request_data))

        assert result == request_data

    def test_raises_error_without_batch_id(self):
        """Test raises HTTPException when batch_id missing"""
        from fastapi import HTTPException

        request_data = {
            "name": "Test Batch",
            "external_brewing_tool": "brewfather",
            "external_brewing_tool_meta": {}
        }

        with pytest.raises(HTTPException) as exc_info:
            run_async(BatchService.verify_and_update_external_brew_tool_batch(request_data))

        assert exc_info.value.status_code == 400
        assert "batch id is required" in exc_info.value.detail

    def test_raises_error_when_batch_not_found(self):
        """Test raises HTTPException when batch not found"""
        from fastapi import HTTPException
        from lib.external_brew_tools.exceptions import ResourceNotFoundError

        request_data = {
            "external_brewing_tool": "brewfather",
            "external_brewing_tool_meta": {"batch_id": "123"}
        }

        with patch('services.batches.get_external_brewing_tool') as mock_get_tool:
            mock_tool = MagicMock()
            mock_tool.get_batch_details = AsyncMock(side_effect=ResourceNotFoundError("Not found"))
            mock_get_tool.return_value = mock_tool

            with pytest.raises(HTTPException) as exc_info:
                run_async(BatchService.verify_and_update_external_brew_tool_batch(request_data))

        assert exc_info.value.status_code == 400
        assert "not found" in exc_info.value.detail

    def test_updates_metadata_on_success(self):
        """Test updates metadata when batch found"""
        request_data = {
            "external_brewing_tool": "brewfather",
            "external_brewing_tool_meta": {"batch_id": "123"}
        }

        with patch('services.batches.get_external_brewing_tool') as mock_get_tool:
            mock_tool = MagicMock()
            mock_tool.get_batch_details = AsyncMock(return_value={"status": "Fermenting"})
            mock_get_tool.return_value = mock_tool

            result = run_async(BatchService.verify_and_update_external_brew_tool_batch(request_data))

        assert "details" in result["external_brewing_tool_meta"]
        assert result["external_brewing_tool_meta"]["details"]["status"] == "Fermenting"
