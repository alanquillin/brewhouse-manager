"""Root pytest configuration - ensures api/ is in sys.path."""

import os
import sys

# Add the api directory to sys.path so imports like 'from db import ...' work.
# Note: pyproject.toml has pythonpath=["api"] and --import-mode=importlib which
# handles most import issues, but this provides a fallback.
_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
api_path = os.path.join(_ROOT_DIR, "api")
if api_path not in sys.path:
    sys.path.insert(0, api_path)
