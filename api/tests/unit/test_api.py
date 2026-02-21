"""Tests for api.py module - FastAPI application setup"""

import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from schema import SchemaError
from sqlalchemy.exc import DataError, IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


# Lazy import of the api module to ensure CONFIG is already loaded
@pytest.fixture
def api_module():
    """Import api.api module (it should be importable after config is set up)"""
    import api.api as module

    return module


class TestUserMessageError:
    """Tests for UserMessageError exception class"""

    def test_init_with_all_params(self, api_module):
        """Test initialization with all parameters"""
        error = api_module.UserMessageError(response_code=400, user_msg="User friendly message", server_msg="Server log message")

        assert error.response_code == 400
        assert error.user_msg == "User friendly message"
        assert error.server_msg == "Server log message"

    def test_init_with_only_response_code(self, api_module):
        """Test initialization with only response code"""
        error = api_module.UserMessageError(response_code=500)

        assert error.response_code == 500
        assert error.user_msg == ""
        assert error.server_msg == ""

    def test_init_server_msg_defaults_to_user_msg(self, api_module):
        """Test server_msg defaults to user_msg when not provided"""
        error = api_module.UserMessageError(response_code=400, user_msg="User message")

        assert error.user_msg == "User message"
        assert error.server_msg == "User message"

    def test_is_exception(self, api_module):
        """Test that UserMessageError is an Exception"""
        error = api_module.UserMessageError(response_code=400)

        assert isinstance(error, Exception)


class TestUserMessageErrorHandler:
    """Tests for user_message_error_handler"""

    def test_returns_json_response(self, api_module):
        """Test returns JSONResponse with correct status and message"""
        mock_request = MagicMock(spec=Request)
        exc = api_module.UserMessageError(response_code=400, user_msg="Bad request")

        result = run_async(api_module.user_message_error_handler(mock_request, exc))

        assert isinstance(result, JSONResponse)
        assert result.status_code == 400

    def test_uses_user_msg_in_response(self, api_module):
        """Test uses user_msg in response content"""
        mock_request = MagicMock(spec=Request)
        exc = api_module.UserMessageError(response_code=403, user_msg="Access denied", server_msg="User attempted unauthorized access")

        result = run_async(api_module.user_message_error_handler(mock_request, exc))

        # Decode the response body to check content
        assert result.status_code == 403


class TestValidationExceptionHandler:
    """Tests for validation_exception_handler"""

    def test_returns_400_status(self, api_module):
        """Test returns 400 status code"""
        mock_request = MagicMock(spec=Request)
        exc = RequestValidationError(errors=[{"loc": ["body", "name"], "msg": "field required"}])

        result = run_async(api_module.validation_exception_handler(mock_request, exc))

        assert isinstance(result, JSONResponse)
        assert result.status_code == 400

    def test_includes_validation_error_in_message(self, api_module):
        """Test includes 'Validation error' in response"""
        mock_request = MagicMock(spec=Request)
        exc = RequestValidationError(errors=[])

        result = run_async(api_module.validation_exception_handler(mock_request, exc))

        assert result.status_code == 400


class TestIntegrityErrorHandler:
    """Tests for integrity_error_handler"""

    def test_returns_400_status(self, api_module):
        """Test returns 400 status code for integrity errors"""
        mock_request = MagicMock(spec=Request)
        exc = IntegrityError(statement="INSERT", params={}, orig=Exception("duplicate key"))

        result = run_async(api_module.integrity_error_handler(mock_request, exc))

        assert isinstance(result, JSONResponse)
        assert result.status_code == 400


class TestDataErrorHandler:
    """Tests for data_error_handler"""

    def test_returns_400_status(self, api_module):
        """Test returns 400 status code for data errors"""
        mock_request = MagicMock(spec=Request)
        exc = DataError(statement="INSERT", params={}, orig=Exception("invalid data"))

        result = run_async(api_module.data_error_handler(mock_request, exc))

        assert isinstance(result, JSONResponse)
        assert result.status_code == 400


class TestSchemaErrorHandler:
    """Tests for schema_error_handler"""

    def test_returns_400_status(self, api_module):
        """Test returns 400 status code for schema errors"""
        mock_request = MagicMock(spec=Request)
        exc = SchemaError("Invalid schema")

        result = run_async(api_module.schema_error_handler(mock_request, exc))

        assert isinstance(result, JSONResponse)
        assert result.status_code == 400


class TestGenericExceptionHandler:
    """Tests for generic_exception_handler"""

    def test_returns_500_status(self, api_module):
        """Test returns 500 status code for unhandled exceptions"""
        mock_request = MagicMock(spec=Request)
        exc = Exception("Something went wrong")

        result = run_async(api_module.generic_exception_handler(mock_request, exc))

        assert isinstance(result, JSONResponse)
        assert result.status_code == 500


class TestHttpExceptionHandler:
    """Tests for http_exception_handler"""

    def test_returns_exception_status_code(self, api_module):
        """Test returns the exception's status code"""
        mock_request = MagicMock(spec=Request)
        exc = StarletteHTTPException(status_code=404, detail="Not found")

        result = run_async(api_module.http_exception_handler(mock_request, exc))

        assert isinstance(result, JSONResponse)
        assert result.status_code == 404

    def test_returns_403_forbidden(self, api_module):
        """Test handles 403 forbidden"""
        mock_request = MagicMock(spec=Request)
        exc = StarletteHTTPException(status_code=403, detail="Forbidden")

        result = run_async(api_module.http_exception_handler(mock_request, exc))

        assert result.status_code == 403


class TestHealthCheck:
    """Tests for health_check endpoint"""

    def test_returns_healthy_true(self, api_module):
        """Test returns healthy: true"""
        result = run_async(api_module.health_check())

        assert result == {"healthy": True}


class TestServeSpa:
    """Tests for serve_spa endpoint"""

    def test_returns_404_when_no_static_dir(self, api_module):
        """Test returns 404 when static directory doesn't exist"""
        with patch.object(api_module, "STATIC_DIR", "/nonexistent"), patch("os.path.isfile", return_value=False), patch("os.path.exists", return_value=False):
            result = run_async(api_module.serve_spa("some/path"))

        assert isinstance(result, JSONResponse)
        assert result.status_code == 404

    def test_serves_static_file_when_exists(self, api_module):
        """Test serves static file when it exists"""
        mock_file_response = MagicMock()

        with patch.object(api_module, "STATIC_DIR", "/static"), patch("os.path.isfile", return_value=True), patch(
            "api.api.FileResponse", return_value=mock_file_response
        ) as mock_fr_class:
            result = run_async(api_module.serve_spa("js/app.js"))

        mock_fr_class.assert_called_once_with("/static/js/app.js")
        assert result == mock_file_response

    def test_serves_index_html_for_spa_routes(self, api_module):
        """Test serves index.html for SPA routes"""
        mock_file_response = MagicMock()

        with patch.object(api_module, "STATIC_DIR", "/static"), patch("os.path.isfile", return_value=False), patch("os.path.exists", return_value=True), patch(
            "api.api.FileResponse", return_value=mock_file_response
        ) as mock_fr_class:
            result = run_async(api_module.serve_spa("manage/locations"))

        mock_fr_class.assert_called_once_with("/static/index.html")
        assert result == mock_file_response


class TestFastAPIAppConfiguration:
    """Tests for FastAPI app configuration"""

    def test_api_has_title(self, api_module):
        """Test API has correct title"""
        assert api_module.api.title == "Brewhouse Manager"

    def test_api_has_version(self, api_module):
        """Test API has version set"""
        assert api_module.api.version is not None
        assert api_module.api.version == "0.8.0"

    def test_api_has_docs_url(self, api_module):
        """Test API has docs URL configured"""
        assert api_module.api.docs_url == "/api/docs"

    def test_api_has_health_route(self, api_module):
        """Test API has health check route"""
        routes = [route.path for route in api_module.api.routes]
        assert "/health" in routes

    def test_api_includes_auth_router(self, api_module):
        """Test API includes auth routes"""
        routes = [route.path for route in api_module.api.routes]
        assert "/login" in routes

    def test_api_includes_beers_router(self, api_module):
        """Test API includes beers routes"""
        routes = [route.path for route in api_module.api.routes]
        assert "/api/v1/beers" in routes

    def test_api_includes_locations_router(self, api_module):
        """Test API includes locations routes"""
        routes = [route.path for route in api_module.api.routes]
        assert "/api/v1/locations" in routes

    def test_api_includes_users_router(self, api_module):
        """Test API includes users routes"""
        routes = [route.path for route in api_module.api.routes]
        assert "/api/v1/users" in routes

    def test_api_includes_taps_router(self, api_module):
        """Test API includes taps routes"""
        routes = [route.path for route in api_module.api.routes]
        assert "/api/v1/taps" in routes

    def test_api_includes_tap_monitors_router(self, api_module):
        """Test API includes tap_monitors routes"""
        routes = [route.path for route in api_module.api.routes]
        assert "/api/v1/tap_monitors" in routes

    def test_api_includes_batches_router(self, api_module):
        """Test API includes batches routes"""
        routes = [route.path for route in api_module.api.routes]
        assert "/api/v1/batches" in routes

    def test_api_includes_dashboard_router(self, api_module):
        """Test API includes dashboard routes"""
        routes = [route.path for route in api_module.api.routes]
        assert "/api/v1/dashboard/locations" in routes

    def test_api_includes_settings_router(self, api_module):
        """Test API includes settings routes"""
        routes = [route.path for route in api_module.api.routes]
        assert "/api/v1/settings" in routes

    def test_api_includes_location_nested_routes(self, api_module):
        """Test API includes location-nested routes for taps"""
        routes = [route.path for route in api_module.api.routes]
        # Location-nested taps route
        assert "/api/v1/locations/{location}/taps" in routes

    def test_api_includes_location_nested_tap_monitors(self, api_module):
        """Test API includes location-nested routes for tap_monitors"""
        routes = [route.path for route in api_module.api.routes]
        assert "/api/v1/locations/{location}/tap_monitors" in routes
