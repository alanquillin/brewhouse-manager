"""Tests for lib/assets/s3.py module (S3AssetManager)"""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

from lib.assets.s3 import S3AssetManager


class TestS3AssetManager:
    """Tests for S3AssetManager class"""

    @pytest.fixture
    def mock_config(self):
        """Create a mock config"""
        config = MagicMock()
        config.get.side_effect = lambda key: {"uploads.s3.bucket.name": "my-bucket", "uploads.s3.bucket.prefix": "assets"}.get(key)
        return config

    @pytest.fixture
    @patch("lib.assets.s3.AssetManagerBase.__init__")
    def manager(self, mock_init, mock_config):
        """Create an S3AssetManager with mocked dependencies"""
        mock_init.return_value = None
        manager = S3AssetManager.__new__(S3AssetManager)
        manager.config = mock_config
        manager.logger = MagicMock()
        manager.bucket = "my-bucket"
        manager.prefix = "assets/"
        return manager

    @pytest.fixture
    @patch("lib.assets.s3.AssetManagerBase.__init__")
    def manager_no_prefix(self, mock_init):
        """Create an S3AssetManager without prefix"""
        mock_init.return_value = None
        manager = S3AssetManager.__new__(S3AssetManager)
        config = MagicMock()
        config.get.side_effect = lambda key: {"uploads.s3.bucket.name": "my-bucket", "uploads.s3.bucket.prefix": None}.get(key)
        manager.config = config
        manager.logger = MagicMock()
        manager.bucket = "my-bucket"
        manager.prefix = ""
        return manager

    def test_get_object_path_with_prefix(self, manager):
        """Test _get_object_path with prefix"""
        result = manager._get_object_path("beer", "image.png")
        assert result == "assets/beer/image.png"

    def test_get_object_path_without_prefix(self, manager_no_prefix):
        """Test _get_object_path without prefix"""
        result = manager_no_prefix._get_object_path("beer", "image.png")
        assert result == "beer/image.png"

    def test_get_url(self, manager):
        """Test _get returns correct S3 URL"""
        result = manager._get("assets/beer/image.png")
        assert result == "https://my-bucket.s3.amazonaws.com/assets/beer/image.png"

    def test_get(self, manager):
        """Test get returns correct full URL"""
        result = manager.get("beer", "image.png")
        assert result == "https://my-bucket.s3.amazonaws.com/assets/beer/image.png"

    @patch("lib.assets.s3.aws")
    def test_list_single_page(self, mock_aws, manager):
        """Test list with single page of results"""
        mock_s3 = MagicMock()
        mock_aws.client.return_value = mock_s3
        mock_s3.list_objects_v2.return_value = {
            "IsTruncated": False,
            "Contents": [
                {"Key": "beer/image1.png"},
                {"Key": "beer/image2.jpg"},
            ],
        }

        result = manager.list("beer")

        assert len(result) == 2
        assert "https://my-bucket.s3.amazonaws.com/beer/image1.png" in result
        assert "https://my-bucket.s3.amazonaws.com/beer/image2.jpg" in result

    @patch("lib.assets.s3.aws")
    def test_list_excludes_prefix_only(self, mock_aws, manager):
        """Test list excludes the prefix-only entry"""
        mock_s3 = MagicMock()
        mock_aws.client.return_value = mock_s3
        mock_s3.list_objects_v2.return_value = {
            "IsTruncated": False,
            "Contents": [
                {"Key": "beer/"},  # Prefix-only entry
                {"Key": "beer/image.png"},
            ],
        }

        result = manager.list("beer")

        assert len(result) == 1
        assert "image.png" in result[0]

    @patch("lib.assets.s3.aws")
    def test_list_pagination(self, mock_aws, manager):
        """Test list handles pagination"""
        mock_s3 = MagicMock()
        mock_aws.client.return_value = mock_s3

        # First page
        mock_s3.list_objects_v2.side_effect = [
            {"IsTruncated": True, "Contents": [{"Key": "beer/image1.png"}], "NextContinuationToken": "token123"},
            # Second page
            {
                "IsTruncated": False,
                "Contents": [{"Key": "beer/image2.png"}],
            },
        ]

        result = manager.list("beer")

        assert len(result) == 2
        assert mock_s3.list_objects_v2.call_count == 2

    @patch("lib.assets.s3.aws")
    def test_list_empty_bucket(self, mock_aws, manager):
        """Test list with empty bucket"""
        mock_s3 = MagicMock()
        mock_aws.client.return_value = mock_s3
        mock_s3.list_objects_v2.return_value = {"IsTruncated": False, "Contents": None}

        result = manager.list("beer")

        assert result == []

    @patch("lib.assets.s3.aws")
    def test_save_flask_file(self, mock_aws, manager):
        """Test save with Flask werkzeug FileStorage"""
        mock_s3 = MagicMock()
        mock_aws.client.return_value = mock_s3

        # Flask file doesn't have .file attribute
        mock_file = MagicMock(spec=["filename", "read", "seek"])
        mock_file.filename = "original.png"

        with patch.object(manager, "generate_random_filename", return_value="uuid.png"):
            old_name, new_name, url = manager.save("beer", mock_file)

        assert old_name == "original.png"
        assert new_name == "uuid.png"
        assert "uuid.png" in url
        mock_s3.upload_fileobj.assert_called_once()

    @patch("lib.assets.s3.aws")
    def test_save_fastapi_file(self, mock_aws, manager):
        """Test save with FastAPI UploadFile"""
        mock_s3 = MagicMock()
        mock_aws.client.return_value = mock_s3

        # FastAPI UploadFile has .file attribute
        mock_file = MagicMock()
        mock_file.filename = "original.jpg"
        mock_file.file = BytesIO(b"file content")

        with patch.object(manager, "generate_random_filename", return_value="uuid.jpg"):
            old_name, new_name, url = manager.save("beer", mock_file)

        assert old_name == "original.jpg"
        assert new_name == "uuid.jpg"
        # Should use the .file attribute for FastAPI
        mock_s3.upload_fileobj.assert_called_once()
        call_args = mock_s3.upload_fileobj.call_args
        assert call_args[0][0] == mock_file.file
