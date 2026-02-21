"""Tests for lib/external_brew_tools/__init__.py module"""

from unittest.mock import MagicMock, patch

import pytest


class TestExternalBrewTools:
    """Tests for external brew tools registry"""

    def test_get_types_returns_keys(self):
        """Test get_types returns available tool types"""
        from lib.external_brew_tools import get_types

        types = list(get_types())
        assert "brewfather" in types

    def test_get_tool_brewfather(self):
        """Test get_tool returns Brewfather instance"""
        from lib.external_brew_tools import get_tool
        from lib.external_brew_tools.brewfather import Brewfather

        tool = get_tool("brewfather")
        assert isinstance(tool, Brewfather)

    def test_get_tool_unknown_returns_none(self):
        """Test get_tool returns None for unknown type"""
        from lib.external_brew_tools import get_tool

        tool = get_tool("unknown_tool")
        assert tool is None


class TestExternalBrewToolBase:
    """Tests for ExternalBrewToolBase class"""

    @patch("lib.external_brew_tools.Config")
    @patch("lib.external_brew_tools.logging")
    def test_init(self, mock_logging, mock_config):
        """Test ExternalBrewToolBase initialization"""
        from lib.external_brew_tools import ExternalBrewToolBase

        mock_logger = MagicMock()
        mock_logging.getLogger.return_value = mock_logger

        base = ExternalBrewToolBase()

        assert base.config is not None
        assert base.logger == mock_logger
        mock_logging.getLogger.assert_called_with("ExternalBrewToolBase")
