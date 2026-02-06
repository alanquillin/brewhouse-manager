"""Tests for lib/assets/files.py module (FileAssetManager)"""

import os
import pytest
from unittest.mock import patch, MagicMock, mock_open
from io import BytesIO

from lib.assets.files import FileAssetManager


class TestFileAssetManager:
    """Tests for FileAssetManager class"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config"""
        config = MagicMock()
        config.get.return_value = "/tmp/uploads"
        return config

    @pytest.fixture
    @patch('lib.assets.files.AssetManagerBase.__init__')
    def manager(self, mock_init, mock_config):
        """Create a FileAssetManager with mocked dependencies"""
        mock_init.return_value = None
        manager = FileAssetManager.__new__(FileAssetManager)
        manager.config = mock_config
        manager.logger = MagicMock()
        manager.assets_base_dir = "/tmp/uploads"
        return manager

    def test_get_parent_dir(self, manager):
        """Test get_parent_dir returns correct path"""
        result = manager.get_parent_dir("beer")
        assert result == "/tmp/uploads/img/beer"

        result = manager.get_parent_dir("user")
        assert result == "/tmp/uploads/img/user"

    def test_get(self, manager):
        """Test get returns correct URL path"""
        result = manager.get("beer", "image.png")
        assert result == "/assets/uploads/img/beer/image.png"

    @patch('os.listdir')
    @patch('os.path.isfile')
    def test_list(self, mock_isfile, mock_listdir, manager):
        """Test list returns filtered file URLs"""
        mock_listdir.return_value = ["file1.png", "file2.jpg", ".hidden", "file3.gif"]
        mock_isfile.return_value = True

        result = manager.list("beer")

        assert len(result) == 3
        assert "/assets/uploads/img/beer/file1.png" in result
        assert "/assets/uploads/img/beer/file2.jpg" in result
        assert "/assets/uploads/img/beer/file3.gif" in result
        # Hidden files should be excluded
        assert ".hidden" not in str(result)

    @patch('os.listdir')
    @patch('os.path.isfile')
    def test_list_excludes_directories(self, mock_isfile, mock_listdir, manager):
        """Test list excludes directories"""
        mock_listdir.return_value = ["file.png", "subdir"]
        mock_isfile.side_effect = lambda p: "file.png" in p

        result = manager.list("beer")

        assert len(result) == 1
        assert "file.png" in result[0]

    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_save_flask_file(self, mock_makedirs, mock_exists, manager):
        """Test save with Flask werkzeug FileStorage"""
        mock_exists.return_value = True

        mock_file = MagicMock()
        mock_file.filename = "original.png"
        mock_file.save = MagicMock()

        with patch.object(manager, 'generate_random_filename', return_value="uuid.png"):
            old_name, new_name, url = manager.save("beer", mock_file)

        assert old_name == "original.png"
        assert new_name == "uuid.png"
        assert url == "/assets/uploads/img/beer/uuid.png"
        mock_file.save.assert_called_once()

    @patch('os.path.exists')
    @patch('os.makedirs')
    @patch('builtins.open', new_callable=mock_open)
    def test_save_fastapi_file(self, mock_file_open, mock_makedirs, mock_exists, manager):
        """Test save with FastAPI UploadFile"""
        mock_exists.return_value = True

        # FastAPI UploadFile doesn't have .save() method
        mock_file = MagicMock(spec=['filename', 'file'])
        mock_file.filename = "original.jpg"
        mock_file.file = BytesIO(b"file content")

        with patch.object(manager, 'generate_random_filename', return_value="uuid.jpg"):
            old_name, new_name, url = manager.save("beer", mock_file)

        assert old_name == "original.jpg"
        assert new_name == "uuid.jpg"
        mock_file_open.assert_called_once()

    @patch('os.path.exists')
    @patch('os.makedirs')
    def test_save_creates_directory_if_not_exists(self, mock_makedirs, mock_exists, manager):
        """Test save creates directory if it doesn't exist"""
        mock_exists.return_value = False

        mock_file = MagicMock()
        mock_file.filename = "test.png"
        mock_file.save = MagicMock()

        with patch.object(manager, 'generate_random_filename', return_value="uuid.png"):
            manager.save("newtype", mock_file)

        mock_makedirs.assert_called_once()
