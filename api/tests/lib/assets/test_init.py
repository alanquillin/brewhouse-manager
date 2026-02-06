"""Tests for lib/assets/__init__.py module (AssetManagerBase)"""

from unittest.mock import MagicMock, patch

import pytest

from lib.assets import AssetManagerBase


class TestAssetManagerBase:
    """Tests for AssetManagerBase class"""

    @patch("lib.assets.Config")
    @patch("lib.assets.logging")
    def test_init(self, mock_logging, mock_config):
        """Test AssetManagerBase initialization"""
        mock_logger = MagicMock()
        mock_logging.getLogger.return_value = mock_logger

        manager = AssetManagerBase()

        assert manager.config is not None
        assert manager.logger == mock_logger


class TestGetFileExtension:
    """Tests for get_file_extension static method"""

    def test_simple_extension(self):
        """Test getting simple file extension"""
        assert AssetManagerBase.get_file_extension("image.png") == "png"
        assert AssetManagerBase.get_file_extension("document.pdf") == "pdf"

    def test_uppercase_extension(self):
        """Test that extension is lowercased"""
        assert AssetManagerBase.get_file_extension("image.PNG") == "png"
        assert AssetManagerBase.get_file_extension("image.JPEG") == "jpeg"

    def test_multiple_dots(self):
        """Test filename with multiple dots"""
        assert AssetManagerBase.get_file_extension("file.name.txt") == "txt"
        assert AssetManagerBase.get_file_extension("archive.tar.gz") == "gz"


class TestGenerateRandomFilename:
    """Tests for generate_random_filename static method"""

    def test_preserves_extension(self):
        """Test that extension is preserved"""
        result = AssetManagerBase.generate_random_filename("myfile.png")
        assert result.endswith(".png")

    def test_generates_uuid_filename(self):
        """Test that filename contains UUID-like string"""
        result = AssetManagerBase.generate_random_filename("test.jpg")
        # UUID format: 8-4-4-4-12 = 36 chars + .jpg = 40 chars
        assert len(result) == 40
        assert result.endswith(".jpg")

    def test_different_calls_produce_different_names(self):
        """Test that each call produces a different name"""
        result1 = AssetManagerBase.generate_random_filename("file.txt")
        result2 = AssetManagerBase.generate_random_filename("file.txt")
        assert result1 != result2

    def test_secure_filename(self):
        """Test that result is a secure filename"""
        # secure_filename should sanitize any special characters
        result = AssetManagerBase.generate_random_filename("test.png")
        # Result should only contain safe characters
        assert "/" not in result
        assert ".." not in result
