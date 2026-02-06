"""Tests for routers/batches.py module - Batches router"""

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


def create_mock_batch(
    id_="batch-1",
    name="Test Batch",
    beer_id=None,
    beverage_id=None,
    external_brewing_tool_meta=None,
):
    """Helper to create mock batch"""
    mock = MagicMock()
    mock.id = id_
    mock.name = name
    mock.beer_id = beer_id
    mock.beverage_id = beverage_id
    mock.external_brewing_tool_meta = external_brewing_tool_meta
    return mock


def create_mock_request(query_params=None):
    """Helper to create mock request"""
    mock = MagicMock()
    mock.query_params = query_params or {}
    return mock


class TestBeerOrBeverageOnlyError:
    """Tests for BeerOrBeverageOnlyError"""

    def test_error_details(self):
        """Test error has correct status code and message"""
        from routers.batches import BeerOrBeverageOnlyError

        error = BeerOrBeverageOnlyError()

        assert error.status_code == 400
        assert "beer" in error.detail.lower()
        assert "beverage" in error.detail.lower()


class TestListBatches:
    """Tests for list_batches endpoint"""

    def test_lists_batches(self):
        """Test lists batches for user"""
        from routers.batches import list_batches

        mock_request = create_mock_request()
        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_batch = create_mock_batch()

        with patch("routers.batches.BatchesDB") as mock_db, patch("routers.batches.BatchService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_batch])
            mock_service.can_user_see_batch = AsyncMock(return_value=True)
            mock_service.transform_response = AsyncMock(return_value={"id": "batch-1"})

            result = run_async(list_batches(mock_request, None, None, False, mock_auth_user, mock_session))

            assert len(result) == 1

    def test_filters_by_beer_id(self):
        """Test filters batches by beer_id"""
        from routers.batches import list_batches

        mock_request = create_mock_request()
        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_batch = create_mock_batch()

        with patch("routers.batches.BatchesDB") as mock_db, patch("routers.batches.BatchService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_batch])
            mock_service.can_user_see_batch = AsyncMock(return_value=True)
            mock_service.transform_response = AsyncMock(return_value={"id": "batch-1"})

            run_async(list_batches(mock_request, "beer-1", None, False, mock_auth_user, mock_session))

            call_kwargs = mock_db.query.call_args[1]
            assert call_kwargs["beer_id"] == "beer-1"

    def test_excludes_archived_by_default(self):
        """Test excludes archived batches by default"""
        from routers.batches import list_batches

        mock_request = create_mock_request()
        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()

        with patch("routers.batches.BatchesDB") as mock_db, patch("routers.batches.BatchService") as mock_service:
            mock_db.query = AsyncMock(return_value=[])
            mock_service.can_user_see_batch = AsyncMock(return_value=True)
            mock_service.transform_response = AsyncMock(return_value={})

            run_async(list_batches(mock_request, None, None, False, mock_auth_user, mock_session))

            call_kwargs = mock_db.query.call_args[1]
            assert call_kwargs["archived_on"] is None

    def test_includes_archived_when_requested(self):
        """Test includes archived batches when include_archived=True"""
        from routers.batches import list_batches

        mock_request = create_mock_request()
        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()

        with patch("routers.batches.BatchesDB") as mock_db, patch("routers.batches.BatchService") as mock_service:
            mock_db.query = AsyncMock(return_value=[])
            mock_service.can_user_see_batch = AsyncMock(return_value=True)
            mock_service.transform_response = AsyncMock(return_value={})

            run_async(list_batches(mock_request, None, None, True, mock_auth_user, mock_session))

            call_kwargs = mock_db.query.call_args[1]
            assert "archived_on" not in call_kwargs

    def test_filters_by_user_access(self):
        """Test filters batches by user access"""
        from routers.batches import list_batches

        mock_request = create_mock_request()
        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-1"])
        mock_session = AsyncMock()
        mock_batch1 = create_mock_batch(id_="batch-1")
        mock_batch2 = create_mock_batch(id_="batch-2")

        with patch("routers.batches.BatchesDB") as mock_db, patch("routers.batches.BatchService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_batch1, mock_batch2])
            # User can only see first batch
            mock_service.can_user_see_batch = AsyncMock(side_effect=[True, False])
            mock_service.transform_response = AsyncMock(return_value={"id": "batch-1"})

            result = run_async(list_batches(mock_request, None, None, False, mock_auth_user, mock_session))

            assert len(result) == 1


class TestCreateBatch:
    """Tests for create_batch endpoint"""

    def test_creates_batch(self):
        """Test creates batch successfully"""
        from routers.batches import create_batch
        from schemas.batches import BatchCreate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_batch = create_mock_batch()
        batch_data = BatchCreate(name="New Batch", beer_id="beer-1")

        with patch("routers.batches.BatchesDB") as mock_db, patch("routers.batches.BatchService") as mock_service:
            mock_db.create = AsyncMock(return_value=mock_batch)
            mock_service.verify_and_update_external_brew_tool_batch = AsyncMock(return_value={"name": "New Batch", "beer_id": "beer-1"})
            mock_service.transform_response = AsyncMock(return_value={"id": "batch-1"})

            result = run_async(create_batch(batch_data, mock_auth_user, mock_session))

            mock_db.create.assert_called_once()

    def test_creates_batch_with_locations(self):
        """Test creates batch with location associations"""
        from routers.batches import create_batch
        from schemas.batches import BatchCreate

        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-1"])
        mock_session = AsyncMock()
        mock_batch = create_mock_batch()
        batch_data = BatchCreate(name="New Batch", location_ids=["loc-1"])

        with patch("routers.batches.BatchesDB") as mock_batch_db, patch("routers.batches.BatchLocationsDB") as mock_batch_loc_db, patch(
            "routers.batches.BatchService"
        ) as mock_service:
            mock_batch_db.create = AsyncMock(return_value=mock_batch)
            mock_batch_db.get_by_pkey = AsyncMock(return_value=mock_batch)
            mock_batch_loc_db.create = AsyncMock()
            mock_service.verify_and_update_external_brew_tool_batch = AsyncMock(return_value={"name": "New Batch", "location_ids": ["loc-1"]})
            mock_service.can_user_see_batch = AsyncMock(return_value=True)
            mock_service.transform_response = AsyncMock(return_value={"id": "batch-1"})

            run_async(create_batch(batch_data, mock_auth_user, mock_session))

            mock_batch_loc_db.create.assert_called_once()

    def test_raises_403_for_unauthorized_locations(self):
        """Test raises 403 when creating batch in unauthorized locations"""
        from routers.batches import create_batch
        from schemas.batches import BatchCreate

        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-other"])
        mock_session = AsyncMock()
        batch_data = BatchCreate(name="New Batch", location_ids=["loc-1"])

        with patch("routers.batches.BatchService") as mock_service:
            mock_service.verify_and_update_external_brew_tool_batch = AsyncMock(return_value={"name": "New Batch", "location_ids": ["loc-1"]})
            mock_service.can_user_see_batch = AsyncMock(return_value=False)

            with pytest.raises(HTTPException) as exc_info:
                run_async(create_batch(batch_data, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 403

    def test_raises_400_for_beer_and_beverage(self):
        """Test raises 400 when both beer_id and beverage_id provided"""
        from routers.batches import create_batch
        from schemas.batches import BatchCreate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        batch_data = BatchCreate(name="New Batch", beer_id="beer-1", beverage_id="bev-1")

        with patch("routers.batches.BatchService") as mock_service:
            mock_service.verify_and_update_external_brew_tool_batch = AsyncMock(return_value={"name": "New Batch", "beer_id": "beer-1", "beverage_id": "bev-1"})

            with pytest.raises(HTTPException) as exc_info:
                run_async(create_batch(batch_data, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 400


class TestGetBatch:
    """Tests for get_batch endpoint"""

    def test_gets_batch_by_id(self):
        """Test gets batch by ID"""
        from routers.batches import get_batch

        mock_request = create_mock_request()
        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_batch = create_mock_batch()

        with patch("routers.batches.BatchesDB") as mock_db, patch("routers.batches.BatchService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_batch])
            mock_service.can_user_see_batch = AsyncMock(return_value=True)
            mock_service.transform_response = AsyncMock(return_value={"id": "batch-1"})

            result = run_async(get_batch("batch-1", mock_request, None, None, mock_auth_user, mock_session))

            assert result["id"] == "batch-1"

    def test_raises_404_when_not_found(self):
        """Test raises 404 when batch not found"""
        from routers.batches import get_batch

        mock_request = create_mock_request()
        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()

        with patch("routers.batches.BatchesDB") as mock_db:
            mock_db.query = AsyncMock(return_value=[])

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_batch("unknown", mock_request, None, None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404

    def test_raises_403_for_unauthorized_batch(self):
        """Test raises 403 when user not authorized for batch"""
        from routers.batches import get_batch

        mock_request = create_mock_request()
        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-other"])
        mock_session = AsyncMock()
        mock_batch = create_mock_batch()

        with patch("routers.batches.BatchesDB") as mock_db, patch("routers.batches.BatchService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_batch])
            mock_service.can_user_see_batch = AsyncMock(return_value=False)

            with pytest.raises(HTTPException) as exc_info:
                run_async(get_batch("batch-1", mock_request, None, None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 403


class TestUpdateBatch:
    """Tests for update_batch endpoint"""

    def test_updates_batch(self):
        """Test updates batch successfully"""
        from routers.batches import update_batch
        from schemas.batches import BatchUpdate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_batch = create_mock_batch()
        update_data = BatchUpdate(name="Updated Batch")

        with patch("routers.batches.BatchesDB") as mock_db, patch("routers.batches.BatchService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_batch])
            mock_db.update = AsyncMock()
            mock_db.get_by_pkey = AsyncMock(return_value=mock_batch)
            mock_service.can_user_see_batch = AsyncMock(return_value=True)
            mock_service.transform_response = AsyncMock(return_value={"id": "batch-1"})

            result = run_async(update_batch("batch-1", update_data, None, None, mock_auth_user, mock_session))

            mock_db.update.assert_called_once()

    def test_raises_404_when_not_found(self):
        """Test raises 404 when batch not found"""
        from routers.batches import update_batch
        from schemas.batches import BatchUpdate

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        update_data = BatchUpdate(name="Updated")

        with patch("routers.batches.BatchesDB") as mock_db:
            mock_db.query = AsyncMock(return_value=[])

            with pytest.raises(HTTPException) as exc_info:
                run_async(update_batch("unknown", update_data, None, None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404


class TestDeleteBatch:
    """Tests for delete_batch endpoint"""

    def test_deletes_batch(self):
        """Test deletes batch successfully"""
        from routers.batches import delete_batch

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()
        mock_batch = create_mock_batch()

        with patch("routers.batches.BatchesDB") as mock_db, patch("routers.batches.BatchService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_batch])
            mock_db.delete = AsyncMock()
            mock_service.can_user_see_batch = AsyncMock(return_value=True)

            result = run_async(delete_batch("batch-1", None, None, mock_auth_user, mock_session))

            assert result is True
            mock_db.delete.assert_called_once()

    def test_raises_404_when_not_found(self):
        """Test raises 404 when batch not found"""
        from routers.batches import delete_batch

        mock_auth_user = create_mock_auth_user(admin=True)
        mock_session = AsyncMock()

        with patch("routers.batches.BatchesDB") as mock_db:
            mock_db.query = AsyncMock(return_value=[])

            with pytest.raises(HTTPException) as exc_info:
                run_async(delete_batch("unknown", None, None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 404

    def test_raises_403_for_unauthorized_batch(self):
        """Test raises 403 when user not authorized to delete batch"""
        from routers.batches import delete_batch

        mock_auth_user = create_mock_auth_user(admin=False, locations=["loc-other"])
        mock_session = AsyncMock()
        mock_batch = create_mock_batch()

        with patch("routers.batches.BatchesDB") as mock_db, patch("routers.batches.BatchService") as mock_service:
            mock_db.query = AsyncMock(return_value=[mock_batch])
            mock_service.can_user_see_batch = AsyncMock(return_value=False)

            with pytest.raises(HTTPException) as exc_info:
                run_async(delete_batch("batch-1", None, None, mock_auth_user, mock_session))

            assert exc_info.value.status_code == 403
