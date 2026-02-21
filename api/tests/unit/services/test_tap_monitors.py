"""Tests for services/tap_monitors.py module - Tap monitor service"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.tap_monitors import TapMonitorService, TapMonitorTypeService


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


def create_mock_tap_monitor(
    id_="monitor-1",
    name="Test Monitor",
    monitor_type="plaato_keg",
    location=None,
):
    """Helper to create mock tap monitor"""
    mock_monitor = MagicMock()
    mock_monitor.id = id_
    mock_monitor.name = name
    mock_monitor.monitor_type = monitor_type
    mock_monitor.location = location

    mock_monitor.to_dict.return_value = {
        "id": id_,
        "name": name,
        "monitor_type": monitor_type,
    }

    async def _awaitable_location():
        return location

    mock_monitor.awaitable_attrs = MagicMock()
    mock_monitor.awaitable_attrs.location = _awaitable_location()

    return mock_monitor


class TestTapMonitorServiceTransformResponse:
    """Tests for TapMonitorService.transform_response method"""

    def test_returns_none_for_none_input(self):
        """Test returns None when tap_monitor is None"""
        mock_session = AsyncMock()
        result = run_async(TapMonitorService.transform_response(None, mock_session))
        assert result is None

    def test_basic_transformation(self):
        """Test basic tap monitor transformation"""
        mock_monitor = create_mock_tap_monitor(name="My Monitor")
        mock_session = AsyncMock()

        mock_tap_monitor_lib = MagicMock()
        mock_tap_monitor_lib.reports_online_status.return_value = False

        with patch("lib.tap_monitors.get_tap_monitor_lib", return_value=mock_tap_monitor_lib):
            result = run_async(TapMonitorService.transform_response(mock_monitor, mock_session, include_location=False))

        assert result is not None
        assert result["name"] == "My Monitor"
        assert result["monitorType"] == "plaato_keg"

    def test_includes_location_when_requested(self):
        """Test includes location when include_location=True"""
        mock_location = MagicMock(id="loc-1")
        mock_monitor = create_mock_tap_monitor(location=mock_location)
        mock_session = AsyncMock()

        mock_tap_monitor_lib = MagicMock()
        mock_tap_monitor_lib.reports_online_status.return_value = False

        with patch("services.locations.LocationService.transform_response", new_callable=AsyncMock) as mock_loc, patch(
            "lib.tap_monitors.get_tap_monitor_lib", return_value=mock_tap_monitor_lib
        ):
            mock_loc.return_value = {"id": "loc-1", "name": "Test Location"}

            result = run_async(TapMonitorService.transform_response(mock_monitor, mock_session, include_location=True))

        assert "location" in result
        assert result["location"]["name"] == "Test Location"

    def test_excludes_location_when_not_requested(self):
        """Test excludes location when include_location=False"""
        mock_location = MagicMock(id="loc-1")
        mock_monitor = create_mock_tap_monitor(location=mock_location)
        mock_session = AsyncMock()

        mock_tap_monitor_lib = MagicMock()
        mock_tap_monitor_lib.reports_online_status.return_value = False

        with patch("lib.tap_monitors.get_tap_monitor_lib", return_value=mock_tap_monitor_lib):
            result = run_async(TapMonitorService.transform_response(mock_monitor, mock_session, include_location=False))

        assert "location" not in result

    def test_includes_tap_when_requested(self):
        """Test includes tap when include_tap=True"""
        mock_monitor = create_mock_tap_monitor()
        mock_session = AsyncMock()
        mock_tap = MagicMock(id="tap-1")

        mock_tap_monitor_lib = MagicMock()
        mock_tap_monitor_lib.reports_online_status.return_value = False

        with patch("db.taps.Taps.query", new_callable=AsyncMock) as mock_taps_query, patch(
            "services.taps.TapService.transform_response", new_callable=AsyncMock
        ) as mock_tap_transform, patch("lib.tap_monitors.get_tap_monitor_lib", return_value=mock_tap_monitor_lib):
            mock_taps_query.return_value = [mock_tap]
            mock_tap_transform.return_value = {"id": "tap-1", "tapNumber": 1}

            result = run_async(TapMonitorService.transform_response(mock_monitor, mock_session, include_location=False, include_tap=True))

        assert "tap" in result
        assert result["tap"]["tapNumber"] == 1

    def test_no_tap_when_none_associated(self):
        """Test no tap when monitor has no associated tap"""
        mock_monitor = create_mock_tap_monitor()
        mock_session = AsyncMock()

        mock_tap_monitor_lib = MagicMock()
        mock_tap_monitor_lib.reports_online_status.return_value = False

        with patch("db.taps.Taps.query", new_callable=AsyncMock) as mock_taps_query, patch(
            "lib.tap_monitors.get_tap_monitor_lib", return_value=mock_tap_monitor_lib
        ):
            mock_taps_query.return_value = []

            result = run_async(TapMonitorService.transform_response(mock_monitor, mock_session, include_location=False, include_tap=True))

        assert "tap" not in result


class TestTapMonitorTypeServiceTransformResponse:
    """Tests for TapMonitorTypeService.transform_response method"""

    def test_returns_none_for_none_input(self):
        """Test returns None when data is None"""
        result = run_async(TapMonitorTypeService.transform_response(None))
        assert result is None

    def test_returns_none_for_empty_dict(self):
        """Test returns None for empty dict"""
        result = run_async(TapMonitorTypeService.transform_response({}))
        assert result is None

    def test_transforms_dict_to_camel_case(self):
        """Test transforms dict keys to camelCase"""
        data = {
            "monitor_type": "plaato_keg",
            "display_name": "Plaato Keg",
            "supports_weight": True,
        }

        result = run_async(TapMonitorTypeService.transform_response(data))

        assert "monitorType" in result
        assert "displayName" in result
        assert "supportsWeight" in result
        assert result["monitorType"] == "plaato_keg"
