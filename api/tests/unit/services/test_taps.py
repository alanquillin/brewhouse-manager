"""Tests for services/taps.py module - Tap service"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch


class _AwaitableValue:
    __slots__ = ("_value",)

    def __init__(self, value):
        self._value = value

    def __await__(self):
        return self._coro().__await__()

    async def _coro(self):
        return self._value


import pytest

from services.taps import TapService


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


def create_mock_tap(
    id_="tap-1",
    tap_number=1,
    location=None,
    on_tap=None,
    tap_monitor=None,
):
    """Helper to create mock tap"""
    mock_tap = MagicMock()
    mock_tap.id = id_
    mock_tap.tap_number = tap_number
    mock_tap.location = location
    mock_tap.on_tap = on_tap
    mock_tap.tap_monitor = tap_monitor

    mock_tap.to_dict.return_value = {
        "id": id_,
        "tap_number": tap_number,
        "on_tap_id": on_tap.id if on_tap else None,
    }

    mock_tap.awaitable_attrs = MagicMock()
    mock_tap.awaitable_attrs.location = _AwaitableValue(location)
    mock_tap.awaitable_attrs.on_tap = _AwaitableValue(on_tap)
    mock_tap.awaitable_attrs.tap_monitor = _AwaitableValue(tap_monitor)

    return mock_tap


class TestTapServiceTransformTapResponse:
    """Tests for TapService.transform_tap_response method"""

    def test_basic_transformation(self):
        """Test basic tap transformation for batch response"""
        mock_tap = create_mock_tap(tap_number=1)
        mock_session = AsyncMock()

        result = run_async(TapService.transform_tap_response(mock_tap, mock_session, include_location=False))

        assert result is not None
        assert result["tapNumber"] == 1

    def test_includes_location_when_requested(self):
        """Test includes location when include_location=True"""
        mock_location = MagicMock(id="loc-1")
        mock_tap = create_mock_tap(location=mock_location)
        mock_session = AsyncMock()

        with patch("services.locations.LocationService.transform_response", new_callable=AsyncMock) as mock_loc:
            mock_loc.return_value = {"id": "loc-1", "name": "Test Location"}

            result = run_async(TapService.transform_tap_response(mock_tap, mock_session, include_location=True))

        assert "location" in result
        assert result["location"]["name"] == "Test Location"

    def test_includes_tap_monitor_when_requested(self):
        """Test includes tap monitor when include_tap_monitor=True"""
        mock_monitor = MagicMock(id="monitor-1")
        mock_tap = create_mock_tap(tap_monitor=mock_monitor)
        mock_session = AsyncMock()

        with patch("services.tap_monitors.TapMonitorService.transform_response", new_callable=AsyncMock) as mock_monitor_transform:
            mock_monitor_transform.return_value = {"id": "monitor-1", "monitorType": "kegtron-pro"}

            result = run_async(TapService.transform_tap_response(mock_tap, mock_session, include_location=False, include_tap_monitor=True))

        assert "tapMonitor" in result
        assert result["tapMonitor"]["monitorType"] == "kegtron-pro"

    def test_excludes_tap_monitor_by_default(self):
        """Test excludes tap monitor by default"""
        mock_monitor = MagicMock(id="monitor-1")
        mock_tap = create_mock_tap(tap_monitor=mock_monitor)
        mock_session = AsyncMock()

        result = run_async(TapService.transform_tap_response(mock_tap, mock_session, include_location=False))

        assert "tapMonitor" not in result


class TestTapServiceTransformResponse:
    """Tests for TapService.transform_response method"""

    def test_returns_none_for_none_input(self):
        """Test returns None when tap is None"""
        mock_session = AsyncMock()
        result = run_async(TapService.transform_response(None, mock_session))
        assert result is None

    def test_basic_transformation(self):
        """Test basic tap transformation"""
        mock_tap = create_mock_tap(tap_number=2)
        mock_session = AsyncMock()

        result = run_async(TapService.transform_response(mock_tap, mock_session, include_location=False))

        assert result is not None
        assert result["tapNumber"] == 2

    def test_removes_on_tap_id(self):
        """Test removes on_tap_id from response"""
        # Create mock tap without on_tap to avoid needing complex nested mocks
        mock_tap = create_mock_tap(on_tap=None)
        mock_tap.to_dict.return_value = {
            "id": "tap-1",
            "tap_number": 1,
            "on_tap_id": "on-tap-1",  # This should be removed
        }
        mock_session = AsyncMock()

        result = run_async(TapService.transform_response(mock_tap, mock_session, include_location=False))

        assert "onTapId" not in result
        assert "on_tap_id" not in result

    def test_includes_on_tap_batch_details(self):
        """Test includes batch details when on_tap exists"""
        mock_beer = MagicMock(id="beer-1")
        mock_batch = MagicMock(id="batch-1", beer=mock_beer, beverage=None, beer_id="beer-1", beverage_id=None)

        mock_batch.awaitable_attrs = MagicMock()
        mock_batch.awaitable_attrs.beer = _AwaitableValue(mock_beer)
        mock_batch.awaitable_attrs.beverage = _AwaitableValue(None)

        mock_on_tap = MagicMock(id="on-tap-1", batch=mock_batch, batch_id="batch-1")
        mock_on_tap.awaitable_attrs = MagicMock()
        mock_on_tap.awaitable_attrs.batch = _AwaitableValue(mock_batch)

        mock_tap = create_mock_tap(on_tap=mock_on_tap)
        mock_session = AsyncMock()

        with patch("services.batches.BatchService.transform_response", new_callable=AsyncMock) as mock_batch_transform, patch(
            "services.beers.BeerService.transform_response", new_callable=AsyncMock
        ) as mock_beer_transform:
            mock_batch_transform.return_value = {"id": "batch-1"}
            mock_beer_transform.return_value = {"id": "beer-1", "name": "Test Beer"}

            result = run_async(TapService.transform_response(mock_tap, mock_session, include_location=False))

        assert "batch" in result
        assert result["batchId"] == "batch-1"
        assert "beer" in result
        assert result["beerId"] == "beer-1"

    def test_includes_tap_monitor(self):
        """Test includes tap monitor details"""
        mock_monitor = MagicMock(id="monitor-1")
        mock_tap = create_mock_tap(tap_monitor=mock_monitor)
        mock_session = AsyncMock()

        with patch("services.tap_monitors.TapMonitorService.transform_response", new_callable=AsyncMock) as mock_monitor_transform:
            mock_monitor_transform.return_value = {"id": "monitor-1", "name": "Test Monitor"}

            result = run_async(TapService.transform_response(mock_tap, mock_session, include_location=False))

        assert "tapMonitor" in result
        assert result["tapMonitor"]["name"] == "Test Monitor"

    def test_includes_location(self):
        """Test includes location when requested"""
        mock_location = MagicMock(id="loc-1")
        mock_tap = create_mock_tap(location=mock_location)
        mock_session = AsyncMock()

        with patch("services.locations.LocationService.transform_response", new_callable=AsyncMock) as mock_loc:
            mock_loc.return_value = {"id": "loc-1", "name": "Test Location"}

            result = run_async(TapService.transform_response(mock_tap, mock_session, include_location=True))

        assert "location" in result
        assert result["location"]["name"] == "Test Location"

    def test_includes_error_for_unsupported_tap_monitor(self):
        """Test tap monitor includes error field when type is unsupported"""
        mock_monitor = MagicMock(id="monitor-1", monitor_type="unsupported-type")
        mock_tap = create_mock_tap(tap_monitor=mock_monitor)
        mock_session = AsyncMock()

        with patch("services.tap_monitors.TapMonitorService.transform_response", new_callable=AsyncMock) as mock_monitor_transform, patch(
            "services.taps.get_tap_monitor_lib", return_value=None
        ):
            mock_monitor_transform.return_value = {"id": "monitor-1", "monitorType": "unsupported-type"}

            result = run_async(TapService.transform_response(mock_tap, mock_session, include_location=False))

        assert "tapMonitor" in result
        assert "error" in result["tapMonitor"]
        assert "unsupported-type" in result["tapMonitor"]["error"].lower()

    def test_no_error_for_supported_tap_monitor(self):
        """Test tap monitor does not include error field when type is supported"""
        mock_monitor = MagicMock(id="monitor-1", monitor_type="open-plaato-keg")
        mock_tap = create_mock_tap(tap_monitor=mock_monitor)
        mock_session = AsyncMock()

        with patch("services.tap_monitors.TapMonitorService.transform_response", new_callable=AsyncMock) as mock_monitor_transform, patch(
            "services.taps.get_tap_monitor_lib", return_value=MagicMock()
        ):
            mock_monitor_transform.return_value = {"id": "monitor-1", "monitorType": "open-plaato-keg"}

            result = run_async(TapService.transform_response(mock_tap, mock_session, include_location=False))

        assert "tapMonitor" in result
        assert "error" not in result["tapMonitor"]

    def test_filter_unsupported_excludes_monitor_no_error(self):
        """Test filter_unsupported_tap_monitor=True excludes unsupported monitors entirely (no error field)"""
        mock_monitor = MagicMock(id="monitor-1", monitor_type="unsupported-type")
        mock_tap = create_mock_tap(tap_monitor=mock_monitor)
        mock_session = AsyncMock()

        with patch("services.tap_monitors.TapMonitorService.transform_response", new_callable=AsyncMock) as mock_monitor_transform, patch(
            "services.taps.get_tap_monitor_lib", return_value=None
        ):
            mock_monitor_transform.return_value = {"id": "monitor-1", "monitorType": "unsupported-type"}

            result = run_async(TapService.transform_response(mock_tap, mock_session, include_location=False, filter_unsupported_tap_monitor=True))

        assert "tapMonitor" not in result


class TestClearOnTapReferencesForBatch:
    """Tests for TapService.clear_on_tap_references_for_batch"""

    def test_clears_on_tap_id_for_matching_taps(self):
        """Test clears on_tap_id for taps still referencing the batch"""
        mock_session = AsyncMock()
        mock_tap = MagicMock()
        mock_tap.id = "tap-1"
        mock_tap.on_tap_id = "on-tap-1"

        with patch("services.taps.TapsDB.get_by_batch", new_callable=AsyncMock) as mock_get_by_batch, patch(
            "services.taps.TapsDB.update", new_callable=AsyncMock
        ) as mock_update:
            mock_get_by_batch.return_value = [mock_tap]

            run_async(TapService.clear_on_tap_references_for_batch(mock_session, "batch-1", autocommit=False))

            mock_update.assert_called_once_with(mock_session, "tap-1", on_tap_id=None, autocommit=False)

    def test_skips_taps_without_on_tap_id(self):
        """Test does not update taps that have no on_tap_id"""
        mock_session = AsyncMock()
        mock_tap = MagicMock()
        mock_tap.id = "tap-1"
        mock_tap.on_tap_id = None

        with patch("services.taps.TapsDB.get_by_batch", new_callable=AsyncMock) as mock_get_by_batch, patch(
            "services.taps.TapsDB.update", new_callable=AsyncMock
        ) as mock_update:
            mock_get_by_batch.return_value = [mock_tap]

            run_async(TapService.clear_on_tap_references_for_batch(mock_session, "batch-1"))

            mock_update.assert_not_called()
