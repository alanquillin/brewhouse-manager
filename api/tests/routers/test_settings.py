"""Tests for routers/settings.py module - Settings router"""

import asyncio
import pytest
from unittest.mock import MagicMock, patch


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestGetSettings:
    """Tests for get_settings endpoint"""

    def test_returns_basic_settings(self):
        """Test returns basic application settings"""
        with patch('routers.settings.CONFIG') as mock_config:
            mock_config.get.side_effect = lambda key, default=None: {
                "auth.oidc.google.enabled": True,
                "taps.refresh.base_sec": 60,
                "taps.refresh.variable": 0.2,
                "beverages.default_type": "beer",
                "beverages.supported_types": ["beer", "cider", "mead"],
                "dashboard.refresh_sec": 30,
                "tap_monitors.plaato_keg.enabled": False,
            }.get(key, default)

            from routers.settings import get_settings
            result = run_async(get_settings())

            assert result["googleSSOEnabled"] is True
            assert result["taps"]["refresh"]["baseSec"] == 60
            assert result["taps"]["refresh"]["variable"] == 0.2
            assert result["beverages"]["defaultType"] == "beer"
            assert result["beverages"]["supportedTypes"] == ["beer", "cider", "mead"]
            assert result["dashboard"]["refreshSec"] == 30

    def test_plaato_disabled_by_default(self):
        """Test plaato_keg_devices returns enabled=False when disabled"""
        with patch('routers.settings.CONFIG') as mock_config:
            mock_config.get.side_effect = lambda key, default=None: {
                "auth.oidc.google.enabled": False,
                "taps.refresh.base_sec": 60,
                "taps.refresh.variable": 0.2,
                "beverages.default_type": "beer",
                "beverages.supported_types": ["beer"],
                "dashboard.refresh_sec": 30,
                "tap_monitors.plaato_keg.enabled": False,
            }.get(key, default)

            from routers.settings import get_settings
            result = run_async(get_settings())

            assert result["plaato_keg_devices"]["enabled"] is False
            assert "config" not in result["plaato_keg_devices"]

    def test_plaato_enabled_includes_config(self):
        """Test plaato_keg_devices includes config when enabled"""
        with patch('routers.settings.CONFIG') as mock_config:
            mock_config.get.side_effect = lambda key, default=None: {
                "auth.oidc.google.enabled": False,
                "taps.refresh.base_sec": 60,
                "taps.refresh.variable": 0.2,
                "beverages.default_type": "beer",
                "beverages.supported_types": ["beer"],
                "dashboard.refresh_sec": 30,
                "tap_monitors.plaato_keg.enabled": True,
                "tap_monitors.plaato_keg.device_config.host": "192.168.1.100",
                "tap_monitors.plaato_keg.device_config.port": 5001,
            }.get(key, default)

            from routers.settings import get_settings
            result = run_async(get_settings())

            assert result["plaato_keg_devices"]["enabled"] is True
            assert result["plaato_keg_devices"]["config"]["host"] == "192.168.1.100"
            assert result["plaato_keg_devices"]["config"]["port"] == 5001

    def test_no_auth_required(self):
        """Test that get_settings has no auth dependency (checking function signature)"""
        from routers.settings import get_settings
        import inspect

        sig = inspect.signature(get_settings)
        params = list(sig.parameters.keys())

        # Should have no parameters (no dependencies)
        assert len(params) == 0
