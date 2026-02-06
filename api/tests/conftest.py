"""Pytest configuration for API tests"""

import sys
import os

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

    # Create a mock for the lib.logging module
    class MockLoggingModule:
        @staticmethod
        def getLogger(name):
            return MockLogger()

    # Patch the lib module's logging
    try:
        import lib
        monkeypatch.setattr(lib, 'logging', MockLoggingModule())
    except (ImportError, AttributeError):
        pass
