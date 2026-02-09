"""
Functional tests for the Tap Monitors API endpoints.
"""

import pytest
import requests

pytestmark = pytest.mark.functional

from .seed_data import LOCATION_MAIN_ID, LOCATION_SECONDARY_ID, TAP_MONITOR_1_ID, TAP_MONITOR_2_ID, TAP_MONITOR_3_ID, TAP_MONITOR_SECONDARY_ID, TAP_MONITORS


class TestGetTapMonitors:
    """Tests for GET /tap_monitors endpoint."""

    def test_returns_all_tap_monitors(self, api_client: requests.Session, api_base_url: str):
        """Test that all seeded tap monitors are returned."""
        response = api_client.get(f"{api_base_url}/tap_monitors")

        assert response.status_code == 200
        monitors = response.json()

        # Should have at least the seeded tap monitors
        assert len(monitors) >= len(TAP_MONITORS)

        # Check that all seeded monitors are present
        monitor_ids = [m["id"] for m in monitors]
        assert TAP_MONITOR_1_ID in monitor_ids
        assert TAP_MONITOR_2_ID in monitor_ids
        assert TAP_MONITOR_3_ID in monitor_ids
        assert TAP_MONITOR_SECONDARY_ID in monitor_ids

    def test_filters_by_query_string_location(self, api_client: requests.Session, api_base_url: str):
        """Test filtering tap monitors by location."""
        response = api_client.get(f"{api_base_url}/tap_monitors", params={"location": LOCATION_MAIN_ID})

        assert response.status_code == 200
        monitors = response.json()

        # Main location has 3 tap monitors
        assert len(monitors) == 3

        # All returned monitors should be from the main location
        for monitor in monitors:
            assert monitor["locationId"] == LOCATION_MAIN_ID

    def test_filters_by_path_location(self, api_client: requests.Session, api_base_url: str):
        """Test filtering tap monitors by location."""
        response = api_client.get(
            f"{api_base_url}/locations/{LOCATION_MAIN_ID}/tap_monitors",
        )

        assert response.status_code == 200
        monitors = response.json()

        # Main location has 3 tap monitors
        assert len(monitors) == 3

        # All returned monitors should be from the main location
        for monitor in monitors:
            assert monitor["locationId"] == LOCATION_MAIN_ID

    def test_tap_monitor_has_expected_fields(self, api_client: requests.Session, api_base_url: str):
        """Test that tap monitor response includes expected fields."""
        response = api_client.get(f"{api_base_url}/tap_monitors/{TAP_MONITOR_1_ID}")

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "id" in data
        assert "name" in data
        assert "monitorType" in data
        assert "locationId" in data

        # Verify specific values
        assert data["id"] == TAP_MONITOR_1_ID
        assert data["name"] == "Monitor 1"
        assert data["monitorType"] == "open-plaato-keg"
        assert data["locationId"] == LOCATION_MAIN_ID


class TestGetTapMonitorById:
    """Tests for GET /tap_monitors/{id} endpoint."""

    def test_returns_tap_monitor_by_id(self, api_client: requests.Session, api_base_url: str):
        """Test getting a specific tap monitor by ID."""
        response = api_client.get(f"{api_base_url}/tap_monitors/{TAP_MONITOR_2_ID}")

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == TAP_MONITOR_2_ID
        assert data["name"] == "Monitor 2"
        assert data["monitorType"] == "open-plaato-keg"

    def test_returns_tap_monitor_with_meta(self, api_client: requests.Session, api_base_url: str):
        """Test that tap monitor includes meta data."""
        response = api_client.get(f"{api_base_url}/tap_monitors/{TAP_MONITOR_1_ID}")

        assert response.status_code == 200
        data = response.json()

        # Should have meta data
        assert "meta" in data
        meta = data["meta"]

        assert meta["deviceId"] == "test-device-001"
        assert meta["emptyKegWeight"] == 4400

    def test_returns_404_for_nonexistent_tap_monitor(self, api_client: requests.Session, api_base_url: str):
        """Test that 404 is returned for non-existent tap monitor."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.get(f"{api_base_url}/tap_monitors/{fake_id}")

        assert response.status_code == 404


class TestGetTapMonitorTypes:
    """Tests for GET /tap_monitors/types endpoint."""

    def test_returns_tap_monitor_types(self, api_client: requests.Session, api_base_url: str):
        """Test getting available tap monitor types."""
        response = api_client.get(f"{api_base_url}/tap_monitors/types")

        assert response.status_code == 200
        types = response.json()

        # Should have at least some types
        assert len(types) > 0

        # Each type should have required fields
        for monitor_type in types:
            assert "type" in monitor_type
            assert "supportsDiscovery" in monitor_type
            assert "reportsOnlineStatus" in monitor_type


class TestCreateTapMonitor:
    """Tests for POST /tap_monitors endpoint."""

    def test_creates_new_tap_monitor(self, api_client: requests.Session, api_base_url: str):
        """Test creating a new tap monitor."""
        new_monitor = {
            "name": "Test New Monitor",
            "monitorType": "open-plaato-keg",
            "locationId": LOCATION_MAIN_ID,
            "meta": {"deviceId": "test-new-device-999", "emptyKegWeight": 5000, "emptyKegWeightUnit": "g", "maxKegVolume": 5, "maxKegVolumeUnit": "gal"},
        }

        response = api_client.post(f"{api_base_url}/tap_monitors", json=new_monitor)

        assert response.status_code == 201
        data = response.json()

        assert "id" in data
        assert data["name"] == new_monitor["name"]
        assert data["monitorType"] == new_monitor["monitorType"]
        assert data["locationId"] == new_monitor["locationId"]

        # Verify it persisted
        get_response = api_client.get(f"{api_base_url}/tap_monitors/{data['id']}")
        assert get_response.status_code == 200


class TestUpdateTapMonitor:
    """Tests for PATCH /tap_monitors/{id} endpoint."""

    def test_updates_tap_monitor_name(self, api_client: requests.Session, api_base_url: str):
        """Test updating a tap monitor's name."""
        update_data = {"name": "Updated Monitor Name"}

        response = api_client.patch(f"{api_base_url}/tap_monitors/{TAP_MONITOR_3_ID}", json=update_data)

        assert response.status_code == 200
        data = response.json()

        assert data["name"] == update_data["name"]
        # Other fields should be unchanged
        assert data["monitorType"] == "keg-volume-monitor-weight"

    def test_updates_tap_monitor_meta(self, api_client: requests.Session, api_base_url: str):
        """Test updating a tap monitor's meta data."""
        update_data = {
            "meta": {
                "deviceId": "test-device-001",
                "emptyKegWeight": 4500,  # Changed from 4400
                "emptyKegWeightUnit": "g",
                "maxKegVolume": 5,
                "maxKegVolumeUnit": "gal",
            }
        }

        response = api_client.patch(f"{api_base_url}/tap_monitors/{TAP_MONITOR_1_ID}", json=update_data)

        assert response.status_code == 200
        data = response.json()

        assert data["meta"]["emptyKegWeight"] == 4500


class TestDeleteTapMonitor:
    """Tests for DELETE /tap_monitors/{id} endpoint."""

    def test_deletes_tap_monitor(self, api_client: requests.Session, api_base_url: str):
        """Test deleting a tap monitor."""
        # First create a tap monitor to delete
        new_monitor = {
            "name": "Monitor To Delete",
            "monitorType": "open-plaato-keg",
            "locationId": LOCATION_SECONDARY_ID,
            "meta": {"deviceId": "delete-me-device"},
        }
        create_response = api_client.post(f"{api_base_url}/tap_monitors", json=new_monitor)
        assert create_response.status_code == 201
        monitor_id = create_response.json()["id"]

        # Delete it
        delete_response = api_client.delete(f"{api_base_url}/tap_monitors/{monitor_id}")
        assert delete_response.status_code == 204

        # Verify it's gone
        get_response = api_client.get(f"{api_base_url}/tap_monitors/{monitor_id}")
        assert get_response.status_code == 404
