"""
Functional tests for the Taps API endpoints.
"""

import pytest
import requests

pytestmark = pytest.mark.functional

from .seed_data import (
    BATCH_IPA_ID,
    BEER_IPA_ID,
    LOCATION_MAIN_ID,
    LOCATION_SECONDARY_ID,
    TAP_1_ID,
    TAP_2_ID,
    TAP_3_ID,
    TAP_MONITOR_1_ID,
    TAP_MONITOR_SECONDARY_ID,
    TAP_MONITOR_UNSUPPORTED_ID,
    TAP_SECONDARY_1_ID,
    TAP_SECONDARY_2_ID,
    TAP_UNSUPPORTED_MONITOR_ID,
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

    def test_filters_taps_by_query_string_location(self, api_client: requests.Session, api_base_url: str):
        """Test filtering taps by location."""
        response = api_client.get(f"{api_base_url}/taps", params={"location": LOCATION_MAIN_ID})

        assert response.status_code == 200
        taps = response.json()
        # Main location has 4 taps (3 supported + 1 unsupported monitor)
        assert len(taps) == 4

        # All returned taps should be from the main location
        for tap in taps:
            assert tap["locationId"] == LOCATION_MAIN_ID

    def test_filters_taps_by_path_location(self, api_client: requests.Session, api_base_url: str):
        """Test filtering taps by location."""
        response = api_client.get(
            f"{api_base_url}/locations/{LOCATION_MAIN_ID}/taps",
        )

        assert response.status_code == 200
        taps = response.json()
        # Main location has 4 taps (3 supported + 1 unsupported monitor)
        assert len(taps) == 4

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

    def test_tap_monitor_has_error_for_unsupported_type(self, api_client: requests.Session, api_base_url: str):
        """Test that a tap with an unsupported monitor includes tapMonitor with an error field."""
        response = api_client.get(f"{api_base_url}/taps/{TAP_UNSUPPORTED_MONITOR_ID}")

        assert response.status_code == 200
        data = response.json()
        assert "tapMonitor" in data
        assert data["tapMonitor"] is not None
        assert "error" in data["tapMonitor"]
        assert "unsupported" in data["tapMonitor"]["error"].lower()

    def test_tap_monitor_no_error_for_supported_type(self, api_client: requests.Session, api_base_url: str):
        """Test that a tap with a supported monitor does not have an error field."""
        response = api_client.get(f"{api_base_url}/taps/{TAP_1_ID}")

        assert response.status_code == 200
        data = response.json()
        assert "tapMonitor" in data
        assert data["tapMonitor"] is not None
        assert "error" not in data["tapMonitor"]


class TestGetTapsUnsupportedMonitor:
    """Tests for GET /taps with unsupported tap monitors."""

    def test_list_taps_includes_unsupported_monitor_with_error(self, api_client: requests.Session, api_base_url: str):
        """Test that list taps includes tap monitors with unsupported types and an error field."""
        response = api_client.get(f"{api_base_url}/taps")

        assert response.status_code == 200
        taps = response.json()

        # Find the seed tap with the unsupported monitor
        unsupported_tap = next((t for t in taps if t["id"] == TAP_UNSUPPORTED_MONITOR_ID), None)
        assert unsupported_tap is not None
        assert "tapMonitor" in unsupported_tap
        assert unsupported_tap["tapMonitor"] is not None
        assert "error" in unsupported_tap["tapMonitor"]
        assert "unsupported" in unsupported_tap["tapMonitor"]["error"].lower()

    def test_list_taps_supported_monitors_have_no_error(self, api_client: requests.Session, api_base_url: str):
        """Test that supported monitors in list taps do not have error fields."""
        response = api_client.get(f"{api_base_url}/taps")

        assert response.status_code == 200
        taps = response.json()

        # Find TAP_1 which has a supported monitor
        tap_1 = next((t for t in taps if t["id"] == TAP_1_ID), None)
        assert tap_1 is not None
        assert "tapMonitor" in tap_1
        assert tap_1["tapMonitor"] is not None
        assert "error" not in tap_1["tapMonitor"]


class TestCreateTap:
    """Tests for POST /taps endpoint."""

    def test_creates_new_tap(self, api_client: requests.Session, api_base_url: str):
        """Test creating a new tap."""
        new_tap = {"tapNumber": 99, "description": "Test New Tap", "locationId": LOCATION_MAIN_ID}

        response = api_client.post(f"{api_base_url}/taps", json=new_tap)

        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["tapNumber"] == new_tap["tapNumber"]
        assert data["description"] == new_tap["description"]
        assert data["locationId"] == new_tap["locationId"]

        # clean up
        response = api_client.delete(f"{api_base_url}/taps/{data['id']}")
        assert response.status_code == 204

    def test_creates_tap_with_supported_tap_monitor(self, api_client: requests.Session, api_base_url: str):
        """Test creating a tap with a supported tap monitor succeeds."""
        new_tap = {
            "tapNumber": 70,
            "description": "Tap with supported monitor",
            "locationId": LOCATION_MAIN_ID,
            "tapMonitorId": TAP_MONITOR_1_ID,
        }

        response = api_client.post(f"{api_base_url}/taps", json=new_tap)

        assert response.status_code == 201
        data = response.json()
        assert data["tapMonitorId"] == TAP_MONITOR_1_ID

        # clean up
        response = api_client.delete(f"{api_base_url}/taps/{data['id']}")
        assert response.status_code == 204

    def test_rejects_create_with_nonexistent_tap_monitor(self, api_client: requests.Session, api_base_url: str):
        """Test that creating a tap with a nonexistent tap monitor returns 404."""
        fake_monitor_id = "00000000-0000-0000-0000-000000000000"
        new_tap = {
            "tapNumber": 71,
            "description": "Tap with fake monitor",
            "locationId": LOCATION_MAIN_ID,
            "tapMonitorId": fake_monitor_id,
        }

        response = api_client.post(f"{api_base_url}/taps", json=new_tap)

        assert response.status_code == 404
        assert "tap monitor not found" in response.json()["message"].lower()

    def test_rejects_create_with_unsupported_tap_monitor(self, api_client: requests.Session, api_base_url: str):
        """Test that creating a tap with an unsupported tap monitor returns 400."""
        new_tap = {
            "tapNumber": 72,
            "description": "Tap with unsupported monitor",
            "locationId": LOCATION_MAIN_ID,
            "tapMonitorId": TAP_MONITOR_UNSUPPORTED_ID,
        }

        response = api_client.post(f"{api_base_url}/taps", json=new_tap)

        assert response.status_code == 400
        assert "unsupported" in response.json()["message"].lower()

    def test_rejects_create_with_tap_monitor_from_wrong_location(self, api_client: requests.Session, api_base_url: str):
        """Test that creating a tap with a monitor from a different location returns 400."""
        new_tap = {
            "tapNumber": 73,
            "description": "Tap with wrong location monitor",
            "locationId": LOCATION_SECONDARY_ID,
            "tapMonitorId": TAP_MONITOR_1_ID,  # This monitor is at LOCATION_MAIN_ID
        }

        response = api_client.post(f"{api_base_url}/taps", json=new_tap)

        assert response.status_code == 400
        assert "not associated with this location" in response.json()["message"].lower()


class TestUpdateTap:
    """Tests for PATCH /taps/{id} endpoint."""

    def test_updates_tap_description(self, api_client: requests.Session, api_base_url: str):
        """Test updating a tap's description."""
        update_data = {"description": "Updated Tap Description"}

        response = api_client.patch(f"{api_base_url}/taps/{TAP_2_ID}", json=update_data)

        assert response.status_code == 200
        data = response.json()

        assert data["description"] == update_data["description"]

    def test_assigns_supported_tap_monitor_to_tap(self, api_client: requests.Session, api_base_url: str):
        """Test assigning a supported tap monitor to a tap succeeds."""
        update_data = {"tapMonitorId": TAP_MONITOR_SECONDARY_ID}

        response = api_client.patch(f"{api_base_url}/taps/{TAP_SECONDARY_2_ID}", json=update_data)

        assert response.status_code == 200
        data = response.json()
        assert data["tapMonitorId"] == TAP_MONITOR_SECONDARY_ID

    def test_rejects_update_with_nonexistent_tap_monitor(self, api_client: requests.Session, api_base_url: str):
        """Test that updating a tap with a nonexistent tap monitor returns 404."""
        fake_monitor_id = "00000000-0000-0000-0000-000000000000"
        update_data = {"tapMonitorId": fake_monitor_id}

        response = api_client.patch(f"{api_base_url}/taps/{TAP_SECONDARY_2_ID}", json=update_data)

        assert response.status_code == 404
        assert "tap monitor not found" in response.json()["message"].lower()

    def test_rejects_update_with_unsupported_tap_monitor(self, api_client: requests.Session, api_base_url: str):
        """Test that updating a tap with an unsupported tap monitor returns 400."""
        update_data = {"tapMonitorId": TAP_MONITOR_UNSUPPORTED_ID}

        response = api_client.patch(f"{api_base_url}/taps/{TAP_1_ID}", json=update_data)

        assert response.status_code == 400
        assert "unsupported" in response.json()["message"].lower()

    def test_rejects_update_with_tap_monitor_from_wrong_location(self, api_client: requests.Session, api_base_url: str):
        """Test that updating a tap with a monitor from a different location returns 400."""
        # TAP_SECONDARY_2_ID is at LOCATION_SECONDARY_ID, TAP_MONITOR_1_ID is at LOCATION_MAIN_ID
        update_data = {"tapMonitorId": TAP_MONITOR_1_ID}

        response = api_client.patch(f"{api_base_url}/taps/{TAP_SECONDARY_2_ID}", json=update_data)

        assert response.status_code == 400
        assert "not associated with this location" in response.json()["message"].lower()


class TestDeleteTap:
    """Tests for DELETE /taps/{id} endpoint."""

    def test_deletes_tap(self, api_client: requests.Session, api_base_url: str):
        """Test deleting a tap."""
        # First create a tap to delete
        new_tap = {"tapNumber": 100, "description": "Tap To Delete", "locationId": LOCATION_MAIN_ID}
        create_response = api_client.post(f"{api_base_url}/taps", json=new_tap)
        assert create_response.status_code == 201
        tap_id = create_response.json()["id"]

        # Delete it
        delete_response = api_client.delete(f"{api_base_url}/taps/{tap_id}")
        assert delete_response.status_code == 204

        # Verify it's gone
        get_response = api_client.get(f"{api_base_url}/taps/{tap_id}")
        assert get_response.status_code == 404
