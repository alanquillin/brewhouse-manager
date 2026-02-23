"""
Functional tests for the Dashboard API endpoints.

Tests verify that unsupported tap monitors are properly filtered
from dashboard responses.
"""

import pytest
import requests

pytestmark = pytest.mark.functional

from .seed_data import LOCATION_MAIN_ID, TAP_1_ID, TAP_MONITOR_1_ID, TAP_MONITOR_UNSUPPORTED_ID, TAP_UNSUPPORTED_MONITOR_ID


class TestGetDashboardTapMonitor:
    """Tests for GET /dashboard/tap_monitors/{id} endpoint."""

    def test_returns_supported_monitor(self, api_client: requests.Session, api_base_url: str):
        """Test that a supported tap monitor is returned successfully."""
        response = api_client.get(f"{api_base_url}/dashboard/tap_monitors/{TAP_MONITOR_1_ID}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == TAP_MONITOR_1_ID
        assert data["monitorType"] == "open-plaato-keg"

    def test_returns_400_for_unsupported_monitor(self, api_client: requests.Session, api_base_url: str):
        """Test that an unsupported tap monitor returns 400."""
        response = api_client.get(f"{api_base_url}/dashboard/tap_monitors/{TAP_MONITOR_UNSUPPORTED_ID}")

        assert response.status_code == 400
        assert "not supported" in response.json()["message"].lower()

    def test_returns_404_for_nonexistent_monitor(self, api_client: requests.Session, api_base_url: str):
        """Test that a non-existent tap monitor returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.get(f"{api_base_url}/dashboard/tap_monitors/{fake_id}")

        assert response.status_code == 404


class TestGetDashboardTap:
    """Tests for GET /dashboard/taps/{id} endpoint."""

    def test_includes_tap_monitor_for_supported_type(self, api_client: requests.Session, api_base_url: str):
        """Test that a tap with a supported monitor includes tapMonitor in response."""
        response = api_client.get(f"{api_base_url}/dashboard/taps/{TAP_1_ID}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == TAP_1_ID
        assert "tapMonitor" in data
        assert "tapMonitorId" in data
        assert data["tapMonitor"] is not None

    def test_excludes_tap_monitor_for_unsupported_type(self, api_client: requests.Session, api_base_url: str):
        """Test that a tap with an unsupported monitor excludes tapMonitor from response."""
        response = api_client.get(f"{api_base_url}/dashboard/taps/{TAP_UNSUPPORTED_MONITOR_ID}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == TAP_UNSUPPORTED_MONITOR_ID
        assert "tapMonitor" not in data
        assert "tapMonitorId" not in data

    def test_returns_404_for_nonexistent_tap(self, api_client: requests.Session, api_base_url: str):
        """Test that a non-existent tap returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.get(f"{api_base_url}/dashboard/taps/{fake_id}")

        assert response.status_code == 404


class TestGetDashboardLocation:
    """Tests for GET /dashboard/locations/{location} endpoint."""

    def test_includes_tap_monitors_for_supported_types(self, api_client: requests.Session, api_base_url: str):
        """Test that taps with supported monitors include tapMonitor in the location dashboard."""
        response = api_client.get(f"{api_base_url}/dashboard/locations/{LOCATION_MAIN_ID}")

        assert response.status_code == 200
        data = response.json()
        assert "taps" in data

        # Find TAP_1 which has a supported monitor
        tap_1 = next((t for t in data["taps"] if t["id"] == TAP_1_ID), None)
        assert tap_1 is not None
        assert "tapMonitor" in tap_1
        assert "tapMonitorId" in tap_1
        assert tap_1["tapMonitor"] is not None

    def test_excludes_tap_monitors_for_unsupported_types(self, api_client: requests.Session, api_base_url: str):
        """Test that taps with unsupported monitors exclude tapMonitor from location dashboard."""
        response = api_client.get(f"{api_base_url}/dashboard/locations/{LOCATION_MAIN_ID}")

        assert response.status_code == 200
        data = response.json()

        # Find the seed tap with the unsupported monitor
        unsupported_tap = next((t for t in data["taps"] if t["id"] == TAP_UNSUPPORTED_MONITOR_ID), None)
        assert unsupported_tap is not None
        assert "tapMonitor" not in unsupported_tap
        assert "tapMonitorId" not in unsupported_tap

    def test_returns_location_data(self, api_client: requests.Session, api_base_url: str):
        """Test that location dashboard returns expected structure."""
        response = api_client.get(f"{api_base_url}/dashboard/locations/{LOCATION_MAIN_ID}")

        assert response.status_code == 200
        data = response.json()

        assert "taps" in data
        assert "locations" in data
        assert "location" in data
        assert data["location"]["id"] == LOCATION_MAIN_ID

    def test_returns_404_for_nonexistent_location(self, api_client: requests.Session, api_base_url: str):
        """Test that a non-existent location returns 404."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = api_client.get(f"{api_base_url}/dashboard/locations/{fake_id}")

        assert response.status_code == 404
