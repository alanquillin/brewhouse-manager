"""
Functional tests for the Plaato Keg device delete endpoint,
specifically the tap monitor reference check and force delete behavior.
"""

import pytest
import requests

pytestmark = pytest.mark.functional

from .seed_data import LOCATION_MAIN_ID


def create_device(api_client, api_base_url, name="Test Device"):
    """Helper to create a plaato keg device and return its id."""
    response = api_client.post(f"{api_base_url}/devices/plaato_keg", json={"name": name})
    assert response.status_code == 201, f"Failed to create device: {response.text}"
    return response.json()["id"]


def create_tap_monitor(api_client, api_base_url, device_id, name="Test Monitor"):
    """Helper to create a tap monitor referencing a device and return its id."""
    monitor_data = {
        "name": name,
        "monitorType": "plaato-keg",
        "locationId": LOCATION_MAIN_ID,
        "meta": {"deviceId": device_id},
    }
    response = api_client.post(f"{api_base_url}/tap_monitors", json=monitor_data)
    assert response.status_code == 201, f"Failed to create tap monitor: {response.text}"
    return response.json()["id"]


class TestDeletePlaatoKegDevice:
    """Tests for DELETE /devices/plaato_keg/{device_id} endpoint."""

    def test_deletes_device_with_no_tap_monitors(self, api_client: requests.Session, api_base_url: str):
        """Test deleting a device that has no associated tap monitors succeeds."""
        device_id = create_device(api_client, api_base_url, name="Unreferenced Device")

        response = api_client.delete(f"{api_base_url}/devices/plaato_keg/{device_id}")
        assert response.status_code == 204

        # Verify it's gone
        get_response = api_client.get(f"{api_base_url}/devices/plaato_keg/{device_id}")
        assert get_response.status_code == 404

    def test_returns_409_when_tap_monitor_references_device(self, api_client: requests.Session, api_base_url: str):
        """Test deleting a device referenced by a tap monitor returns 409 Conflict."""
        device_id = create_device(api_client, api_base_url, name="Referenced Device")
        monitor_id = create_tap_monitor(api_client, api_base_url, device_id, name="Blocking Monitor")

        response = api_client.delete(f"{api_base_url}/devices/plaato_keg/{device_id}")
        assert response.status_code == 409
        assert "Blocking Monitor" in response.json()["message"]

        # Verify device still exists
        get_response = api_client.get(f"{api_base_url}/devices/plaato_keg/{device_id}")
        assert get_response.status_code == 200

        # Verify tap monitor still exists
        get_monitor = api_client.get(f"{api_base_url}/tap_monitors/{monitor_id}")
        assert get_monitor.status_code == 200
        
        response = api_client.delete(f"{api_base_url}/tap_monitors/{monitor_id}")
        assert response.status_code == 204

        response = api_client.delete(f"{api_base_url}/devices/plaato_keg/{device_id}")
        assert response.status_code == 204

    def test_force_delete_removes_tap_monitors_and_device(self, api_client: requests.Session, api_base_url: str):
        """Test force_delete_tap_monitor=true deletes referencing monitors and the device."""
        device_id = create_device(api_client, api_base_url, name="Force Delete Device")
        monitor_id = create_tap_monitor(api_client, api_base_url, device_id, name="Force Deleted Monitor")

        response = api_client.delete(f"{api_base_url}/devices/plaato_keg/{device_id}", params={"force_delete_tap_monitor": "true"})
        assert response.status_code == 204

        # Verify device is gone
        get_device = api_client.get(f"{api_base_url}/devices/plaato_keg/{device_id}")
        assert get_device.status_code == 404

        # Verify tap monitor is also gone
        get_monitor = api_client.get(f"{api_base_url}/tap_monitors/{monitor_id}")
        assert get_monitor.status_code == 404

    def test_force_delete_removes_multiple_tap_monitors(self, api_client: requests.Session, api_base_url: str):
        """Test force delete removes all referencing monitors."""
        device_id = create_device(api_client, api_base_url, name="Multi Monitor Device")
        monitor_id_1 = create_tap_monitor(api_client, api_base_url, device_id, name="Monitor A")
        monitor_id_2 = create_tap_monitor(api_client, api_base_url, device_id, name="Monitor B")

        response = api_client.delete(f"{api_base_url}/devices/plaato_keg/{device_id}", params={"force_delete_tap_monitor": "true"})
        assert response.status_code == 204

        # Verify all are gone
        assert api_client.get(f"{api_base_url}/devices/plaato_keg/{device_id}").status_code == 404
        assert api_client.get(f"{api_base_url}/tap_monitors/{monitor_id_1}").status_code == 404
        assert api_client.get(f"{api_base_url}/tap_monitors/{monitor_id_2}").status_code == 404

    def test_returns_404_for_nonexistent_device(self, api_client: requests.Session, api_base_url: str):
        """Test deleting a non-existent device returns 404."""
        response = api_client.delete(f"{api_base_url}/devices/plaato_keg/nonexistent-device-id")
        assert response.status_code == 404
