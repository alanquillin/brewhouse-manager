"""Pytest configuration for API tests"""

import sys
import os

# Set CONFIG_BASE_DIR before any imports that might trigger Config loading.
# The default.json config file is at the project root's config/ directory.
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("CONFIG_BASE_DIR", os.path.join(_PROJECT_ROOT, "config"))

# Add the api directory to the path so imports work correctly
api_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if api_path not in sys.path:
    sys.path.insert(0, api_path)

import pytest


@pytest.fixture(autouse=True)
def mock_logging(monkeypatch):
    """Mock logging to prevent import issues during tests"""
    import logging

    class MockLogger:
        def debug(self, *args, **kwargs):
            pass

        def info(self, *args, **kwargs):
            pass

        def warning(self, *args, **kwargs):
            pass

        def error(self, *args, **kwargs):
            pass

        def exception(self, *args, **kwargs):
            pass

    # Create a mock for the lib.logging module
    class MockLoggingModule:
        DEFAULT_LOG_FMT = "%(message)s"

        @staticmethod
        def getLogger(name):
            return MockLogger()

        @staticmethod
        def init(*args, **kwargs):
            pass

        @staticmethod
        def get_def_log_level(*args, **kwargs):
            return "INFO"

        @staticmethod
        def get_log_level(*args, **kwargs):
            return logging.INFO

        @staticmethod
        def set_log_level(*args, **kwargs):
            pass

    # Patch the lib module's logging
    try:
        import lib
        monkeypatch.setattr(lib, 'logging', MockLoggingModule())
    except (ImportError, AttributeError):
        pass
