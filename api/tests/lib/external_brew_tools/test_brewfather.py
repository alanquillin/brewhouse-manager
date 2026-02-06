"""Tests for lib/external_brew_tools/brewfather.py module"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import BasicAuth

from lib.external_brew_tools.brewfather import Brewfather
from lib.external_brew_tools.exceptions import ResourceNotFoundError


# Helper to run async functions in sync tests
def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


class TestBrewfather:
    """Tests for Brewfather class"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config"""
        config = MagicMock()
        config.get.side_effect = lambda key: {
            "external_brew_tools.brewfather.username": "test_user",
            "external_brew_tools.brewfather.api_key": "test_key",
            "external_brew_tools.brewfather.timeout_sec": 30,
            "external_brew_tools.brewfather.completed_statuses": ["Completed", "Archived"],
        }.get(key)
        return config

    @pytest.fixture
    @patch("lib.external_brew_tools.brewfather.ExternalBrewToolBase.__init__")
    def brewfather(self, mock_init, mock_config):
        """Create a Brewfather instance with mocked dependencies"""
        mock_init.return_value = None
        bf = Brewfather.__new__(Brewfather)
        bf.config = mock_config
        bf.logger = MagicMock()
        return bf

    def test_get_auth_default(self, brewfather):
        """Test _get_auth with default config"""
        auth = brewfather._get_auth()
        assert isinstance(auth, BasicAuth)

    def test_get_auth_with_meta(self, brewfather):
        """Test _get_auth with meta credentials"""
        meta = {"username": "meta_user", "api_key": "meta_key"}
        auth = brewfather._get_auth(meta)
        assert isinstance(auth, BasicAuth)

    def test_get_auth_named_config(self, brewfather, mock_config):
        """Test _get_auth with named configuration"""
        # Add named config values
        mock_config.get.side_effect = lambda key: {
            "external_brew_tools.brewfather.username": "default_user",
            "external_brew_tools.brewfather.api_key": "default_key",
            "external_brew_tools.brewfather.secondary.username": "secondary_user",
            "external_brew_tools.brewfather.secondary.api_key": "secondary_key",
            "external_brew_tools.brewfather.timeout_sec": 30,
            "external_brew_tools.brewfather.completed_statuses": ["Completed", "Archived"],
        }.get(key)

        meta = {"name": "secondary"}
        auth = brewfather._get_auth(meta)
        # Should look for external_brew_tools.brewfather.secondary.username
        assert isinstance(auth, BasicAuth)

    def test_say_hello(self, brewfather):
        """Test _say_hello helper method"""
        result = brewfather._say_hello()
        assert result == "hello"


class TestBrewfatherAsync:
    """Tests for async Brewfather methods"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config"""
        config = MagicMock()
        config.get.side_effect = lambda key: {
            "external_brew_tools.brewfather.username": "test_user",
            "external_brew_tools.brewfather.api_key": "test_key",
            "external_brew_tools.brewfather.timeout_sec": 30,
            "external_brew_tools.brewfather.completed_statuses": ["Completed", "Archived"],
        }.get(key)
        return config

    @pytest.fixture
    @patch("lib.external_brew_tools.brewfather.ExternalBrewToolBase.__init__")
    def brewfather(self, mock_init, mock_config):
        """Create a Brewfather instance with mocked dependencies"""
        mock_init.return_value = None
        bf = Brewfather.__new__(Brewfather)
        bf.config = mock_config
        bf.logger = MagicMock()
        return bf

    @patch("lib.external_brew_tools.brewfather.AsyncClient")
    def test_get_success(self, mock_async_client, brewfather):
        """Test _get with successful response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "test"}

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        result = run_async(brewfather._get("v2/batches", {}))

        assert result == ({"data": "test"}, 200)

    @patch("lib.external_brew_tools.brewfather.AsyncClient")
    def test_get_not_found(self, mock_async_client, brewfather):
        """Test _get with 404 response"""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        result = run_async(brewfather._get("v2/batches/123", {}))

        assert result == (None, 404)

    @patch("lib.external_brew_tools.brewfather.AsyncClient")
    def test_get_batch_success(self, mock_async_client, brewfather):
        """Test _get_batch with successful response"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "123", "name": "Test Batch"}

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        meta = {"batch_id": "123"}
        result = run_async(brewfather._get_batch(meta=meta))

        assert result == {"id": "123", "name": "Test Batch"}

    @patch("lib.external_brew_tools.brewfather.AsyncClient")
    def test_get_batch_not_found_raises(self, mock_async_client, brewfather):
        """Test _get_batch raises ResourceNotFoundError on 404"""
        mock_response = MagicMock()
        mock_response.status_code = 404

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        meta = {"batch_id": "nonexistent"}
        with pytest.raises(ResourceNotFoundError):
            run_async(brewfather._get_batch(meta=meta))

    @patch("lib.external_brew_tools.brewfather.AsyncClient")
    def test_get_batches(self, mock_async_client, brewfather):
        """Test _get_batches returns list"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": "1"}, {"id": "2"}]

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        result = run_async(brewfather._get_batches())

        assert len(result) == 2

    @patch("lib.external_brew_tools.brewfather.AsyncClient")
    def test_get_batch_details(self, mock_async_client, brewfather):
        """Test get_batch_details parses response correctly"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "batchNo": 42,
            "measuredAbv": 5.5,
            "status": "Completed",
            "estimatedIbu": 35,
            "brewDate": 1640000000000,
            "bottlingDate": 1641000000000,
            "estimatedColor": 8,
            "recipe": {"name": "Test IPA", "img_url": "http://example.com/img.jpg", "style": {"name": "American IPA", "type": "IPA"}},
        }

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        meta = {"batch_id": "123"}
        result = run_async(brewfather.get_batch_details(meta=meta))

        assert result["name"] == "Test IPA"
        assert result["abv"] == 5.5
        assert result["status"] == "Completed"
        assert result["style"] == "American IPA"
        assert result["batch_number"] == "42"

    @patch("lib.external_brew_tools.brewfather.AsyncClient")
    def test_get_batch_details_incomplete_status(self, mock_async_client, brewfather):
        """Test get_batch_details marks refresh when status incomplete"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"batchNo": 1, "status": "Fermenting", "recipe": {"name": "Test", "style": {}}}

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        meta = {"batch_id": "123"}
        result = run_async(brewfather.get_batch_details(meta=meta))

        assert result.get("_refresh_on_next_check") is True
        assert "completed status" in result.get("_refresh_reason", "").lower()

    @patch("lib.external_brew_tools.brewfather.AsyncClient")
    def test_get_recipe_details(self, mock_async_client, brewfather):
        """Test get_recipe_details parses response correctly"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "name": "Test Recipe",
            "abv": 6.0,
            "ibu": 40,
            "color": 10,
            "img_url": "http://example.com/recipe.jpg",
            "style": {"name": "Pale Ale"},
        }

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        meta = {"recipe_id": "456"}
        result = run_async(brewfather.get_recipe_details(meta=meta))

        assert result["name"] == "Test Recipe"
        assert result["abv"] == 6.0
        assert result["ibu"] == 40
        assert result["srm"] == 10
        assert result["style"] == "Pale Ale"

    @patch("lib.external_brew_tools.brewfather.AsyncClient")
    def test_search_batches(self, mock_async_client, brewfather):
        """Test search_batches returns batch list"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [{"id": "1"}, {"id": "2"}, {"id": "3"}]

        mock_client = MagicMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        mock_async_client.return_value = mock_client

        result = run_async(brewfather.search_batches())

        assert len(result) == 3

    def test_get_batch_no_args_raises(self, brewfather):
        """Test _get_batch with no args raises exception"""
        with pytest.raises(Exception):
            run_async(brewfather._get_batch())

    def test_get_recipe_no_args_raises(self, brewfather):
        """Test _get_recipe with no args raises exception"""
        with pytest.raises(Exception):
            run_async(brewfather._get_recipe())
