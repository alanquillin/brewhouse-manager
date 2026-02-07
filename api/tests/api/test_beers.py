"""
Functional tests for the Beers API endpoints.
"""

import pytest
import requests

pytestmark = pytest.mark.functional

from .seed_data import (
    BEER_IPA_ID,
    BEER_STOUT_ID,
    BEER_LAGER_ID,
    BEER_WHEAT_ID,
    BEERS,
)


class TestGetBeers:
    """Tests for GET /beers endpoint."""

    def test_returns_all_beers(self, api_client: requests.Session, api_base_url: str):
        """Test that all seeded beers are returned."""
        response = api_client.get(f"{api_base_url}/beers")

        assert response.status_code == 200
        beers = response.json()

        # Should have at least the seeded beers
        assert len(beers) >= len(BEERS)

        # Check that all seeded beers are present
        beer_ids = [beer["id"] for beer in beers]
        assert BEER_IPA_ID in beer_ids
        assert BEER_STOUT_ID in beer_ids
        assert BEER_LAGER_ID in beer_ids
        assert BEER_WHEAT_ID in beer_ids

    def test_beer_has_expected_fields(self, api_client: requests.Session, api_base_url: str):
        """Test that beer response includes expected fields."""
        response = api_client.get(f"{api_base_url}/beers/{BEER_IPA_ID}")

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "id" in data
        assert "name" in data
        assert data["name"] == "Test IPA"
        assert data["style"] == "IPA"
        assert data["abv"] == 6.5
        assert data["ibu"] == 65


class TestGetBeerById:
    """Tests for GET /beers/{id} endpoint."""

    def test_returns_beer_by_id(self, api_client: requests.Session, api_base_url: str):
        """Test getting a specific beer by ID."""
        response = api_client.get(f"{api_base_url}/beers/{BEER_STOUT_ID}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == BEER_STOUT_ID
        assert data["name"] == "Test Stout"
        assert data["style"] == "Stout"

    def test_returns_404_for_nonexistent_beer(self, api_client: requests.Session, api_base_url: str):
        """Test that 404 is returned for non-existent beer."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.get(f"{api_base_url}/beers/{fake_id}")

        assert response.status_code == 404


class TestCreateBeer:
    """Tests for POST /beers endpoint."""

    def test_creates_new_beer(self, api_client: requests.Session, api_base_url: str):
        """Test creating a new beer."""
        new_beer = {
            "name": "Test New Pale Ale",
            "description": "A new test pale ale",
            "style": "Pale Ale",
            "abv": 5.5,
            "ibu": 40,
            "srm": 10.0
        }

        response = api_client.post(f"{api_base_url}/beers", json=new_beer)

        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["name"] == new_beer["name"]
        assert data["style"] == new_beer["style"]
        assert data["abv"] == new_beer["abv"]

        # Verify it persisted
        get_response = api_client.get(f"{api_base_url}/beers/{data['id']}")
        assert get_response.status_code == 200

    def test_creates_beer_with_minimal_fields(self, api_client: requests.Session, api_base_url: str):
        """Test creating a beer with only required fields."""
        new_beer = {
            "name": "Minimal Beer"
        }

        response = api_client.post(f"{api_base_url}/beers", json=new_beer)

        assert response.status_code == 201
        data = response.json()

        assert data["name"] == new_beer["name"]


class TestUpdateBeer:
    """Tests for PATCH /beers/{id} endpoint."""

    def test_updates_beer(self, api_client: requests.Session, api_base_url: str):
        """Test updating a beer's fields."""
        update_data = {
            "description": "Updated IPA description",
            "abv": 7.0
        }

        response = api_client.patch(
            f"{api_base_url}/beers/{BEER_IPA_ID}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["description"] == update_data["description"]
        assert data["abv"] == update_data["abv"]
        # Name should be unchanged
        assert data["name"] == "Test IPA"


class TestDeleteBeer:
    """Tests for DELETE /beers/{id} endpoint."""

    def test_deletes_beer(self, api_client: requests.Session, api_base_url: str):
        """Test deleting a beer."""
        # First create a beer to delete
        new_beer = {
            "name": "Beer To Delete",
            "style": "Delete Me"
        }
        create_response = api_client.post(f"{api_base_url}/beers", json=new_beer)
        assert create_response.status_code == 201
        beer_id = create_response.json()["id"]

        # Delete it
        delete_response = api_client.delete(f"{api_base_url}/beers/{beer_id}")
        assert delete_response.status_code == 204

        # Verify it's gone
        get_response = api_client.get(f"{api_base_url}/beers/{beer_id}")
        assert get_response.status_code == 404
