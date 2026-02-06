"""Tests for app.py module - Application entry point"""

import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock


def run_async(coro):
    """Helper to run async functions in sync tests"""
    return asyncio.get_event_loop().run_until_complete(coro)


# Lazy import of the app module
@pytest.fixture
def app_module():
    """Import api.app module"""
    import api.app as module
    return module


class TestApplicationInit:
    """Tests for Application.__init__"""

    def test_default_init(self, app_module):
        """Test default initialization"""
        app = app_module.Application()

        assert app.tcp_task is None
        assert app.http_server is None
        assert app.plaato_service is None
        assert app.log_level == "INFO"

    def test_custom_log_level(self, app_module):
        """Test initialization with custom log level"""
        app = app_module.Application(log_level="DEBUG")

        assert app.log_level == "DEBUG"

    def test_init_with_warning_level(self, app_module):
        """Test initialization with WARNING log level"""
        app = app_module.Application(log_level="WARNING")

        assert app.log_level == "WARNING"


class TestApplicationInitializeFirstUser:
    """Tests for Application.initialize_first_user"""

    def test_does_nothing_when_users_exist(self, app_module):
        """Test does nothing when users already exist"""
        app = app_module.Application()
        mock_user = MagicMock()

        with patch('db.async_session_scope') as mock_scope, \
             patch('db.users.Users') as mock_users_db:
            mock_session = AsyncMock()
            mock_scope.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_scope.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_users_db.query = AsyncMock(return_value=[mock_user])

            run_async(app.initialize_first_user())

            mock_users_db.create.assert_not_called()

    def test_creates_user_when_none_exist(self, app_module):
        """Test creates initial user when no users exist"""
        app = app_module.Application()

        with patch('db.async_session_scope') as mock_scope, \
             patch('db.users.Users') as mock_users_db, \
             patch.object(app_module, 'CONFIG') as mock_config:
            mock_session = AsyncMock()
            mock_scope.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_scope.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_users_db.query = AsyncMock(return_value=[])
            mock_users_db.create = AsyncMock()
            mock_config.get.side_effect = lambda key, default=None: {
                "auth.initial_user.email": "admin@example.com",
                "auth.initial_user.set_password": False,
                "auth.initial_user.first_name": "Admin",
                "auth.initial_user.last_name": "User",
                "auth.oidc.google.enabled": True,
            }.get(key, default)

            run_async(app.initialize_first_user())

            mock_users_db.create.assert_called_once()
            call_kwargs = mock_users_db.create.call_args[1]
            assert call_kwargs["email"] == "admin@example.com"
            assert call_kwargs["admin"] is True

    def test_creates_user_with_password(self, app_module):
        """Test creates initial user with password when set_password is true"""
        app = app_module.Application()

        with patch('db.async_session_scope') as mock_scope, \
             patch('db.users.Users') as mock_users_db, \
             patch.object(app_module, 'CONFIG') as mock_config:
            mock_session = AsyncMock()
            mock_scope.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_scope.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_users_db.query = AsyncMock(return_value=[])
            mock_users_db.create = AsyncMock()
            mock_config.get.side_effect = lambda key, default=None: {
                "auth.initial_user.email": "admin@example.com",
                "auth.initial_user.set_password": True,
                "auth.initial_user.password": "initial_password",
                "auth.initial_user.first_name": None,
                "auth.initial_user.last_name": None,
                "auth.oidc.google.enabled": False,
            }.get(key, default)

            run_async(app.initialize_first_user())

            call_kwargs = mock_users_db.create.call_args[1]
            assert call_kwargs["password"] == "initial_password"

    def test_exits_when_no_auth_method(self, app_module):
        """Test exits when no authentication method available"""
        app = app_module.Application()

        with patch('db.async_session_scope') as mock_scope, \
             patch('db.users.Users') as mock_users_db, \
             patch.object(app_module, 'CONFIG') as mock_config, \
             patch.object(app_module, 'sys') as mock_sys:
            mock_session = AsyncMock()
            mock_scope.return_value.__aenter__ = AsyncMock(return_value=mock_session)
            mock_scope.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_users_db.query = AsyncMock(return_value=[])
            mock_config.get.side_effect = lambda key, default=None: {
                "auth.initial_user.email": "admin@example.com",
                "auth.initial_user.set_password": False,
                "auth.initial_user.first_name": None,
                "auth.initial_user.last_name": None,
                "auth.oidc.google.enabled": False,
            }.get(key, default)
            # Make sys.exit raise SystemExit so code stops
            mock_sys.exit.side_effect = SystemExit(1)

            with pytest.raises(SystemExit):
                run_async(app.initialize_first_user())

            mock_sys.exit.assert_called_once_with(1)


class TestApplicationStartPlaatoService:
    """Tests for Application.start_plaato_service"""

    def test_starts_plaato_tcp_server(self, app_module):
        """Test starts Plaato TCP server"""
        app = app_module.Application()

        with patch('lib.devices.plaato_keg.service_handler') as mock_handler, \
             patch.object(app_module, 'CONFIG') as mock_config, \
             patch('asyncio.create_task') as mock_create_task:
            mock_config.get.side_effect = lambda key, default=None: {
                "tap_monitors.plaato_keg.host": "0.0.0.0",
                "tap_monitors.plaato_keg.port": 5001,
            }.get(key, default)
            mock_handler.connection_handler.start_server = AsyncMock()
            mock_create_task.return_value = MagicMock()

            run_async(app.start_plaato_service())

            assert app.plaato_service == mock_handler
            mock_create_task.assert_called_once()

    def test_uses_default_host_and_port(self, app_module):
        """Test uses default host and port when not configured"""
        app = app_module.Application()

        with patch('lib.devices.plaato_keg.service_handler') as mock_handler, \
             patch.object(app_module, 'CONFIG') as mock_config, \
             patch('asyncio.create_task') as mock_create_task:
            mock_config.get.side_effect = lambda key, default=None: default
            mock_handler.connection_handler.start_server = AsyncMock()
            mock_create_task.return_value = MagicMock()

            run_async(app.start_plaato_service())

            # Should use defaults
            mock_handler.connection_handler.start_server.assert_called_once_with(
                host="localhost",
                port=5001
            )


class TestApplicationStartHttpServer:
    """Tests for Application.start_http_server"""

    def test_starts_uvicorn_server(self, app_module):
        """Test starts uvicorn server with correct config"""
        app = app_module.Application(log_level="INFO")

        with patch('api.app.CONFIG') as mock_config, \
             patch('api.app.uvicorn.Config') as mock_uvicorn_config, \
             patch('api.app.uvicorn.Server') as mock_uvicorn_server:
            mock_config.get.side_effect = lambda key, default=None: {
                "api.host": "0.0.0.0",
                "api.port": 8000,
                "ENV": "production",
            }.get(key, default)
            mock_server_instance = MagicMock()
            mock_server_instance.serve = AsyncMock()
            mock_uvicorn_server.return_value = mock_server_instance

            run_async(app.start_http_server())

            mock_uvicorn_config.assert_called_once()
            call_kwargs = mock_uvicorn_config.call_args[1]
            assert call_kwargs["host"] == "0.0.0.0"
            assert call_kwargs["port"] == 8000
            assert call_kwargs["log_level"] == "info"

    def test_uses_default_host_and_port(self, app_module):
        """Test uses default host and port when not configured"""
        app = app_module.Application()

        with patch('api.app.CONFIG') as mock_config, \
             patch('api.app.uvicorn.Config') as mock_uvicorn_config, \
             patch('api.app.uvicorn.Server') as mock_uvicorn_server:
            mock_config.get.side_effect = lambda key, default=None: default
            mock_server_instance = MagicMock()
            mock_server_instance.serve = AsyncMock()
            mock_uvicorn_server.return_value = mock_server_instance

            run_async(app.start_http_server())

            call_kwargs = mock_uvicorn_config.call_args[1]
            assert call_kwargs["host"] == "localhost"
            assert call_kwargs["port"] == 5000

    def test_enables_reload_in_development(self, app_module):
        """Test enables reload in development environment"""
        app = app_module.Application()

        with patch('api.app.CONFIG') as mock_config, \
             patch('api.app.uvicorn.Config') as mock_uvicorn_config, \
             patch('api.app.uvicorn.Server') as mock_uvicorn_server:
            mock_config.get.side_effect = lambda key, default=None: {
                "api.host": "localhost",
                "api.port": 5000,
                "ENV": "development",
            }.get(key, default)
            mock_server_instance = MagicMock()
            mock_server_instance.serve = AsyncMock()
            mock_uvicorn_server.return_value = mock_server_instance

            run_async(app.start_http_server())

            call_kwargs = mock_uvicorn_config.call_args[1]
            assert call_kwargs["reload"] is True


class TestApplicationShutdown:
    """Tests for Application.shutdown"""

    def test_shutdown_with_no_services(self, app_module):
        """Test shutdown when no services are running"""
        app = app_module.Application()

        # Should not raise any errors
        run_async(app.shutdown())

    def test_shutdown_cancels_tcp_task(self, app_module):
        """Test shutdown cancels TCP task"""
        app = app_module.Application()

        # Create an awaitable mock task that raises CancelledError
        async def cancelled_coro():
            raise asyncio.CancelledError()

        mock_task = asyncio.ensure_future(cancelled_coro())
        mock_task.cancel = MagicMock(wraps=mock_task.cancel)
        app.tcp_task = mock_task

        run_async(app.shutdown())

        mock_task.cancel.assert_called_once()

    def test_shutdown_stops_plaato_service(self, app_module):
        """Test shutdown stops Plaato service"""
        app = app_module.Application()
        mock_plaato = MagicMock()
        mock_plaato.connection_handler = MagicMock()
        mock_plaato.connection_handler.stop_server = AsyncMock()
        app.plaato_service = mock_plaato

        run_async(app.shutdown())

        mock_plaato.connection_handler.stop_server.assert_called()


class TestApplicationRun:
    """Tests for Application.run"""

    def test_run_initializes_first_user(self, app_module):
        """Test run calls initialize_first_user"""
        app = app_module.Application()
        app.initialize_first_user = AsyncMock()
        app.start_http_server = AsyncMock(side_effect=asyncio.CancelledError())
        app.shutdown = AsyncMock()

        with patch('api.app.CONFIG') as mock_config:
            mock_config.get.return_value = False

            run_async(app.run())

            app.initialize_first_user.assert_called_once()

    def test_run_starts_plaato_when_enabled(self, app_module):
        """Test run starts Plaato service when enabled"""
        app = app_module.Application()
        app.initialize_first_user = AsyncMock()
        app.start_plaato_service = AsyncMock()
        app.start_http_server = AsyncMock(side_effect=asyncio.CancelledError())
        app.shutdown = AsyncMock()

        with patch('api.app.CONFIG') as mock_config:
            mock_config.get.side_effect = lambda key, default=None: {
                "tap_monitors.plaato_keg.enabled": True,
            }.get(key, default)

            run_async(app.run())

            app.start_plaato_service.assert_called_once()

    def test_run_skips_plaato_when_disabled(self, app_module):
        """Test run skips Plaato service when disabled"""
        app = app_module.Application()
        app.initialize_first_user = AsyncMock()
        app.start_plaato_service = AsyncMock()
        app.start_http_server = AsyncMock(side_effect=asyncio.CancelledError())
        app.shutdown = AsyncMock()

        with patch('api.app.CONFIG') as mock_config:
            mock_config.get.side_effect = lambda key, default=None: {
                "tap_monitors.plaato_keg.enabled": False,
            }.get(key, default)

            run_async(app.run())

            app.start_plaato_service.assert_not_called()

    def test_run_calls_shutdown_on_cancel(self, app_module):
        """Test run calls shutdown when cancelled"""
        app = app_module.Application()
        app.initialize_first_user = AsyncMock()
        app.start_http_server = AsyncMock(side_effect=asyncio.CancelledError())
        app.shutdown = AsyncMock()

        with patch('api.app.CONFIG') as mock_config:
            mock_config.get.return_value = False

            run_async(app.run())

            app.shutdown.assert_called_once()

    def test_run_starts_http_server(self, app_module):
        """Test run starts HTTP server"""
        app = app_module.Application()
        app.initialize_first_user = AsyncMock()
        app.start_http_server = AsyncMock()
        app.shutdown = AsyncMock()

        with patch('api.app.CONFIG') as mock_config:
            mock_config.get.return_value = False

            run_async(app.run())

            app.start_http_server.assert_called_once()
