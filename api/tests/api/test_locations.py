"""
Functional tests for the Locations API endpoints.
"""

import pytest
import requests

pytestmark = pytest.mark.functional

from .seed_data import (
    LOCATION_MAIN_ID,
    LOCATION_SECONDARY_ID,
    LOCATION_EMPTY_ID,
    LOCATIONS,
)


class TestGetLocations:
    """Tests for GET /locations endpoint."""

    def test_returns_all_locations(self, api_client: requests.Session, api_base_url: str):
        """Test that all seeded locations are returned."""
        response = api_client.get(f"{api_base_url}/locations")

        assert response.status_code == 200
        locations = response.json()

        # API returns a list directly
        assert isinstance(locations, list)

        # Should have at least the seeded locations
        assert len(locations) >= len(LOCATIONS)

        # Check that all seeded locations are present
        location_ids = [loc["id"] for loc in locations]
        assert LOCATION_MAIN_ID in location_ids
        assert LOCATION_SECONDARY_ID in location_ids
        assert LOCATION_EMPTY_ID in location_ids

    def test_location_has_expected_fields(self, api_client: requests.Session, api_base_url: str):
        """Test that location response includes expected fields."""
        response = api_client.get(f"{api_base_url}/locations")

        assert response.status_code == 200
        locations = response.json()

        location = locations[0]

        # Check required fields
        assert "id" in location
        assert "name" in location
        assert "description" in location


class TestGetLocationById:
    """Tests for GET /locations/{id} endpoint."""

    def test_returns_location_by_id(self, api_client: requests.Session, api_base_url: str):
        """Test getting a specific location by ID."""
        response = api_client.get(f"{api_base_url}/locations/{LOCATION_MAIN_ID}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == LOCATION_MAIN_ID
        assert data["name"] == "main-taproom"
        assert data["description"] == "Main Taproom - 3 Taps"

    def test_returns_404_for_nonexistent_location(self, api_client: requests.Session, api_base_url: str):
        """Test that 404 is returned for non-existent location."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.get(f"{api_base_url}/locations/{fake_id}")

        assert response.status_code == 404


class TestCreateLocation:
    """Tests for POST /locations endpoint."""

    def test_creates_new_location(self, api_client: requests.Session, api_base_url: str):
        """Test creating a new location."""
        new_location = {
            "name": "test-new-location",
            "description": "A new test location"
        }

        response = api_client.post(f"{api_base_url}/locations", json=new_location)

        # API returns 200 for successful creation
        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["name"] == new_location["name"]
        assert data["description"] == new_location["description"]

        # Verify it persisted - use query param since direct ID lookup may not work
        get_response = api_client.get(f"{api_base_url}/locations")
        assert get_response.status_code == 200
        locations = get_response.json()
        location_ids = [loc["id"] for loc in locations]
        assert data["id"] in location_ids

    def test_create_location_requires_name(self, api_client: requests.Session, api_base_url: str):
        """Test that name is required when creating a location."""
        invalid_location = {
            "description": "Missing name field"
        }

        response = api_client.post(f"{api_base_url}/locations", json=invalid_location)

        # Should return validation error
        assert response.status_code in [400, 422]


class TestUpdateLocation:
    """Tests for PATCH /locations/{id} endpoint."""

    def test_updates_location(self, api_client: requests.Session, api_base_url: str):
        """Test updating a location's fields."""
        update_data = {
            "description": "Updated description"
        }

        response = api_client.patch(
            f"{api_base_url}/locations/{LOCATION_MAIN_ID}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["description"] == update_data["description"]
        # Name should be unchanged
        assert data["name"] == "main-taproom"


class TestDeleteLocation:
    """Tests for DELETE /locations/{id} endpoint."""

    def test_deletes_location(self, api_client: requests.Session, api_base_url: str):
        """Test deleting a location."""
        # First create a location to delete
        new_location = {
            "name": "location-to-delete",
            "description": "This will be deleted"
        }
        create_response = api_client.post(f"{api_base_url}/locations", json=new_location)
        assert create_response.status_code == 201
        location_id = create_response.json()["id"]

        # Delete it
        delete_response = api_client.delete(f"{api_base_url}/locations/{location_id}")
        assert delete_response.status_code == 204

        # Verify it's gone by checking it's not in the list
        get_response = api_client.get(f"{api_base_url}/locations")
        assert get_response.status_code == 200
        location_ids = [loc["id"] for loc in get_response.json()]
        assert location_id not in location_ids
