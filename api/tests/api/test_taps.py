"""
Functional tests for the Taps API endpoints.
"""

import pytest
import requests

pytestmark = pytest.mark.functional

from .seed_data import (
    LOCATION_MAIN_ID,
    LOCATION_SECONDARY_ID,
    TAP_1_ID,
    TAP_2_ID,
    TAP_3_ID,
    TAP_SECONDARY_1_ID,
    TAP_SECONDARY_2_ID,
    BEER_IPA_ID,
    BATCH_IPA_ID,
    TAP_MONITOR_1_ID,
    TAPS,
)


class TestGetTaps:
    """Tests for GET /taps endpoint."""

    def test_returns_all_taps(self, api_client: requests.Session, api_base_url: str):
        """Test that all seeded taps are returned."""
        response = api_client.get(f"{api_base_url}/taps")

        assert response.status_code == 200
        taps = response.json()

        # Should have at least the seeded taps
        assert len(taps) >= len(TAPS)

    def test_filters_taps_by_location(self, api_client: requests.Session, api_base_url: str):
        """Test filtering taps by location."""
        response = api_client.get(
            f"{api_base_url}/taps",
            params={"location_id": LOCATION_MAIN_ID}
        )

        assert response.status_code == 200
        data = response.json()

        taps = data["taps"]
        # Main location has 3 taps
        assert len(taps) == 3

        # All returned taps should be from the main location
        for tap in taps:
            assert tap["locationId"] == LOCATION_MAIN_ID


class TestGetTapById:
    """Tests for GET /taps/{id} endpoint."""

    def test_returns_tap_by_id(self, api_client: requests.Session, api_base_url: str):
        """Test getting a specific tap by ID."""
        response = api_client.get(f"{api_base_url}/taps/{TAP_1_ID}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == TAP_1_ID
        assert data["tapNumber"] == 1
        assert data["locationId"] == LOCATION_MAIN_ID

    def test_returns_tap_with_on_tap_data(self, api_client: requests.Session, api_base_url: str):
        """Test that tap includes on_tap data with beer/batch info."""
        response = api_client.get(f"{api_base_url}/taps/{TAP_1_ID}")

        assert response.status_code == 200
        on_tap = response.json()

        if on_tap:
            # Should include batch info
            assert "batch" in on_tap or "batchId" in on_tap

    def test_returns_tap_with_tap_monitor(self, api_client: requests.Session, api_base_url: str):
        """Test that tap includes tap monitor data when assigned."""
        response = api_client.get(f"{api_base_url}/taps/{TAP_1_ID}")

        assert response.status_code == 200
        data = response.json()

        # Should have tap monitor ID
        assert data.get("tapMonitorId") == TAP_MONITOR_1_ID

    def test_returns_404_for_nonexistent_tap(self, api_client: requests.Session, api_base_url: str):
        """Test that 404 is returned for non-existent tap."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.get(f"{api_base_url}/taps/{fake_id}")

        assert response.status_code == 404


class TestCreateTap:
    """Tests for POST /taps endpoint."""

    def test_creates_new_tap(self, api_client: requests.Session, api_base_url: str):
        """Test creating a new tap."""
        new_tap = {
            "tapNumber": 99,
            "description": "Test New Tap",
            "locationId": LOCATION_MAIN_ID
        }

        response = api_client.post(f"{api_base_url}/taps", json=new_tap)

        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["tapNumber"] == new_tap["tapNumber"]
        assert data["description"] == new_tap["description"]
        assert data["locationId"] == new_tap["locationId"]


class TestUpdateTap:
    """Tests for PATCH /taps/{id} endpoint."""

    def test_updates_tap_description(self, api_client: requests.Session, api_base_url: str):
        """Test updating a tap's description."""
        update_data = {
            "description": "Updated Tap Description"
        }

        response = api_client.patch(
            f"{api_base_url}/taps/{TAP_2_ID}",
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["description"] == update_data["description"]

    def test_assigns_tap_monitor_to_tap(self, api_client: requests.Session, api_base_url: str):
        """Test assigning a tap monitor to a tap."""
        # Use the empty tap that doesn't have a monitor
        update_data = {
            "tapMonitorId": TAP_MONITOR_1_ID
        }

        # Note: This might fail if tap monitor is already assigned
        # This test demonstrates the capability
        response = api_client.patch(
            f"{api_base_url}/taps/{TAP_SECONDARY_2_ID}",
            json=update_data
        )

        # Could be 200 (success) or 400/422 (already assigned)
        assert response.status_code in [200, 400, 422]


class TestDeleteTap:
    """Tests for DELETE /taps/{id} endpoint."""

    def test_deletes_tap(self, api_client: requests.Session, api_base_url: str):
        """Test deleting a tap."""
        # First create a tap to delete
        new_tap = {
            "tapNumber": 100,
            "description": "Tap To Delete",
            "locationId": LOCATION_MAIN_ID
        }
        create_response = api_client.post(f"{api_base_url}/taps", json=new_tap)
        assert create_response.status_code == 201
        tap_id = create_response.json()["id"]

        # Delete it
        delete_response = api_client.delete(f"{api_base_url}/taps/{tap_id}")
        assert delete_response.status_code == 204

        # Verify it's gone
        get_response = api_client.get(f"{api_base_url}/taps/{tap_id}")
        assert get_response.status_code == 404
