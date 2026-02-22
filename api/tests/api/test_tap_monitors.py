"""
Functional tests for the Tap Monitors API endpoints.
"""

import pytest
import requests

pytestmark = pytest.mark.functional

from .seed_data import (
    LOCATION_MAIN_ID,
    LOCATION_SECONDARY_ID,
    TAP_1_ID,
    TAP_MONITOR_1_ID,
    TAP_MONITOR_2_ID,
    TAP_MONITOR_3_ID,
    TAP_MONITOR_SECONDARY_ID,
    TAP_MONITORS,
)


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

    def test_returns_tap_details_when_requested(self, api_client: requests.Session, api_base_url: str):
        """Test that tap details are included when include_tap_details=true."""
        response = api_client.get(f"{api_base_url}/tap_monitors", params={"include_tap_details": "true"})

        assert response.status_code == 200
        monitors = response.json()

        # Find monitor 1 which is connected to tap 1
        monitor_1 = next(m for m in monitors if m["id"] == TAP_MONITOR_1_ID)
        assert "tap" in monitor_1
        assert monitor_1["tap"] is not None
        assert monitor_1["tap"]["id"] == TAP_1_ID

    @pytest.mark.parametrize("param_value", ["true", "yes", "1", "True", "YES"])
    def test_include_tap_details_truthy_values(self, api_client: requests.Session, api_base_url: str, param_value: str):
        """Test that various truthy values for include_tap_details return tap objects."""
        response = api_client.get(f"{api_base_url}/tap_monitors", params={"include_tap_details": param_value})

        assert response.status_code == 200
        monitors = response.json()

        monitor_1 = next(m for m in monitors if m["id"] == TAP_MONITOR_1_ID)
        assert "tap" in monitor_1
        assert monitor_1["tap"] is not None

    def test_does_not_include_tap_when_not_requested(self, api_client: requests.Session, api_base_url: str):
        """Test that tap details are not included by default."""
        response = api_client.get(f"{api_base_url}/tap_monitors")

        assert response.status_code == 200
        monitors = response.json()

        monitor_1 = next(m for m in monitors if m["id"] == TAP_MONITOR_1_ID)
        assert "tap" not in monitor_1


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

    def test_returns_tap_details_when_requested(self, api_client: requests.Session, api_base_url: str):
        """Test that tap details are included for a monitor connected to a tap."""
        response = api_client.get(
            f"{api_base_url}/tap_monitors/{TAP_MONITOR_1_ID}",
            params={"include_tap_details": "true"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "tap" in data
        assert data["tap"] is not None
        assert data["tap"]["id"] == TAP_1_ID
        assert "tapNumber" in data["tap"]
        assert "description" in data["tap"]

    @pytest.mark.parametrize("param_value", ["true", "yes", "1", "True", "YES"])
    def test_include_tap_details_truthy_values(self, api_client: requests.Session, api_base_url: str, param_value: str):
        """Test that various truthy values for include_tap_details return the tap object."""
        response = api_client.get(
            f"{api_base_url}/tap_monitors/{TAP_MONITOR_1_ID}",
            params={"include_tap_details": param_value},
        )

        assert response.status_code == 200
        data = response.json()
        assert "tap" in data
        assert data["tap"] is not None

    def test_returns_null_tap_when_monitor_not_connected(self, api_client: requests.Session, api_base_url: str):
        """Test that tap is null when monitor is not connected to any tap."""
        # Create a monitor with no tap association
        new_monitor = {
            "name": "Unconnected Monitor",
            "monitorType": "open-plaato-keg",
            "locationId": LOCATION_SECONDARY_ID,
            "meta": {"deviceId": "unconnected-device-001"},
        }
        create_response = api_client.post(f"{api_base_url}/tap_monitors", json=new_monitor)
        assert create_response.status_code == 201
        monitor_id = create_response.json()["id"]

        # Get with include_tap_details - tap should be null
        response = api_client.get(
            f"{api_base_url}/tap_monitors/{monitor_id}",
            params={"include_tap_details": "true"},
        )

        assert response.status_code == 200
        data = response.json()
        assert "tap" not in data or data.get("tap") is None

    def test_does_not_include_tap_when_not_requested(self, api_client: requests.Session, api_base_url: str):
        """Test that tap details are not included by default."""
        response = api_client.get(f"{api_base_url}/tap_monitors/{TAP_MONITOR_1_ID}")

        assert response.status_code == 200
        data = response.json()
        assert "tap" not in data


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

    def test_returns_409_for_duplicate_device_id_and_monitor_type(self, api_client: requests.Session, api_base_url: str):
        """Test creating a tap monitor with the same device_id and monitor_type as an existing one returns 409."""
        device_id = "test-duplicate-check-device"
        monitor_type = "open-plaato-keg"

        # Create the first monitor
        first_monitor = {
            "name": "First Monitor",
            "monitorType": monitor_type,
            "locationId": LOCATION_MAIN_ID,
            "meta": {"deviceId": device_id},
        }
        first_response = api_client.post(f"{api_base_url}/tap_monitors", json=first_monitor)
        assert first_response.status_code == 201

        # Attempt to create a second monitor with the same device_id and monitor_type
        second_monitor = {
            "name": "Duplicate Monitor",
            "monitorType": monitor_type,
            "locationId": LOCATION_SECONDARY_ID,
            "meta": {"deviceId": device_id},
        }
        second_response = api_client.post(f"{api_base_url}/tap_monitors", json=second_monitor)
        assert second_response.status_code == 409
        assert device_id in second_response.json()["message"]


class TestCreateKegtronProValidation:
    """Tests for kegtron-pro meta validation on POST /tap_monitors."""

    def test_returns_400_when_missing_all_required_meta(self, api_client: requests.Session, api_base_url: str):
        """Test creating kegtron-pro monitor without required meta fields returns 400."""
        new_monitor = {
            "name": "Bad Kegtron",
            "monitorType": "kegtron-pro",
            "locationId": LOCATION_MAIN_ID,
            "meta": {},
        }

        response = api_client.post(f"{api_base_url}/tap_monitors", json=new_monitor)

        assert response.status_code == 400
        detail = response.json()["message"]
        assert "port_num" in detail
        assert "device_id" in detail
        assert "access_token" in detail

    def test_returns_400_when_missing_some_required_meta(self, api_client: requests.Session, api_base_url: str):
        """Test that only the missing fields are listed in the error."""
        new_monitor = {
            "name": "Partial Kegtron",
            "monitorType": "kegtron-pro",
            "locationId": LOCATION_MAIN_ID,
            "meta": {"accessToken": "tok123"},
        }

        response = api_client.post(f"{api_base_url}/tap_monitors", json=new_monitor)

        assert response.status_code == 400
        detail = response.json()["message"]
        assert "port_num" in detail
        assert "device_id" in detail
        assert "access_token" not in detail

    def test_returns_400_when_no_meta(self, api_client: requests.Session, api_base_url: str):
        """Test creating kegtron-pro monitor with no meta at all returns 400."""
        new_monitor = {
            "name": "No Meta Kegtron",
            "monitorType": "kegtron-pro",
            "locationId": LOCATION_MAIN_ID,
        }

        response = api_client.post(f"{api_base_url}/tap_monitors", json=new_monitor)

        assert response.status_code == 400

    def test_creates_kegtron_pro_with_valid_meta(self, api_client: requests.Session, api_base_url: str):
        """Test creating kegtron-pro monitor succeeds with all required meta fields."""
        new_monitor = {
            "name": "Valid Kegtron",
            "monitorType": "kegtron-pro",
            "locationId": LOCATION_MAIN_ID,
            "meta": {
                "portNum": 0,
                "deviceId": "kegtron-func-test-dev",
                "accessToken": "kegtron-func-test-tok",
            },
        }

        response = api_client.post(f"{api_base_url}/tap_monitors", json=new_monitor)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Valid Kegtron"
        assert data["monitorType"] == "kegtron-pro"
        assert data["meta"]["portNum"] == 0
        assert data["meta"]["deviceId"] == "kegtron-func-test-dev"
        assert data["meta"]["accessToken"] == "kegtron-func-test-tok"

    def test_returns_400_when_meta_values_are_empty(self, api_client: requests.Session, api_base_url: str):
        """Test that empty string values are rejected."""
        new_monitor = {
            "name": "Empty Values Kegtron",
            "monitorType": "kegtron-pro",
            "locationId": LOCATION_MAIN_ID,
            "meta": {
                "portNum": 0,
                "deviceId": "",
                "accessToken": "tok",
            },
        }

        response = api_client.post(f"{api_base_url}/tap_monitors", json=new_monitor)

        assert response.status_code == 400
        detail = response.json()["message"]
        assert "device_id" in detail

    def test_non_kegtron_type_not_affected(self, api_client: requests.Session, api_base_url: str):
        """Test that non-kegtron-pro types are not subject to kegtron meta validation."""
        new_monitor = {
            "name": "Non-Kegtron Monitor",
            "monitorType": "open-plaato-keg",
            "locationId": LOCATION_SECONDARY_ID,
            "meta": {"deviceId": "non-kegtron-func-test-dev"},
        }

        response = api_client.post(f"{api_base_url}/tap_monitors", json=new_monitor)

        assert response.status_code == 201


class TestUpdateKegtronProValidation:
    """Tests for kegtron-pro meta validation on PATCH /tap_monitors/{id}."""

    def _create_kegtron_monitor(self, api_client, api_base_url, suffix=""):
        """Helper to create a kegtron-pro monitor for update tests."""
        new_monitor = {
            "name": f"Kegtron For Update{suffix}",
            "monitorType": "kegtron-pro",
            "locationId": LOCATION_MAIN_ID,
            "meta": {
                "portNum": 0,
                "deviceId": f"kegtron-update-test-dev{suffix}",
                "accessToken": f"kegtron-update-test-tok{suffix}",
            },
        }
        response = api_client.post(f"{api_base_url}/tap_monitors", json=new_monitor)
        assert response.status_code == 201
        return response.json()["id"]

    def test_returns_400_when_meta_has_empty_values(self, api_client: requests.Session, api_base_url: str):
        """Test updating kegtron-pro meta with empty values returns 400."""
        monitor_id = self._create_kegtron_monitor(api_client, api_base_url, "-empty-val")

        update_data = {"meta": {"accessToken": ""}}

        response = api_client.patch(f"{api_base_url}/tap_monitors/{monitor_id}", json=update_data)

        assert response.status_code == 400
        detail = response.json()["message"]
        assert "access_token" in detail

    def test_allows_partial_meta_update(self, api_client: requests.Session, api_base_url: str):
        """Test updating kegtron-pro meta with a subset of required fields succeeds (allow_missing)."""
        monitor_id = self._create_kegtron_monitor(api_client, api_base_url, "-partial")

        update_data = {"meta": {"accessToken": "new-token"}}

        response = api_client.patch(f"{api_base_url}/tap_monitors/{monitor_id}", json=update_data)

        assert response.status_code == 200
        assert response.json()["meta"]["accessToken"] == "new-token"

    def test_name_update_skips_meta_validation(self, api_client: requests.Session, api_base_url: str):
        """Test updating only the name does not trigger meta validation."""
        monitor_id = self._create_kegtron_monitor(api_client, api_base_url, "-name-only")

        update_data = {"name": "Renamed Kegtron"}

        response = api_client.patch(f"{api_base_url}/tap_monitors/{monitor_id}", json=update_data)

        assert response.status_code == 200
        assert response.json()["name"] == "Renamed Kegtron"

    def test_returns_400_when_changing_monitor_type(self, api_client: requests.Session, api_base_url: str):
        """Test that changing monitor_type on an existing monitor is rejected."""
        monitor_id = self._create_kegtron_monitor(api_client, api_base_url, "-type-change")

        update_data = {"monitorType": "open-plaato-keg"}

        response = api_client.patch(f"{api_base_url}/tap_monitors/{monitor_id}", json=update_data)

        assert response.status_code == 400
        assert "cannot change the type" in response.json()["message"].lower()


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
