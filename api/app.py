#! /usr/bin/env python3

import argparse
import os
import sys

from lib import logging
from lib.config import Config

# Initialize configuration
CONFIG = Config()
CONFIG.setup(config_files=["default.json"])

# Initialize logging
logging.init(fmt=logging.DEFAULT_LOG_FMT)

import asyncio

import uvicorn

from api import api

LOGGER = logging.getLogger(__name__)


class Application:
    """Main application class"""

    def __init__(self, log_level: str = "INFO"):
        self.tcp_task = None
        self.http_server = None
        self.plaato_service = None
        self.log_level = log_level

    async def initialize_first_user(self):
        """Create initial user if no users exist"""
        from db import async_session_scope
        from db.users import Users as UsersDB

        async with async_session_scope(CONFIG) as db_session:
            users = await UsersDB.query(db_session)

            if not users:
                init_user_email = CONFIG.get("auth.initial_user.email")
                set_init_user_pass = CONFIG.get("auth.initial_user.set_password")
                init_user_fname = CONFIG.get("auth.initial_user.first_name")
                init_user_lname = CONFIG.get("auth.initial_user.last_name")
                google_sso_enabled = CONFIG.get("auth.oidc.google.enabled")

                if not google_sso_enabled and not set_init_user_pass:
                    LOGGER.error("Cannot create an initial user! auth.initial_user.set_password and google authentication is disabled!")
                    sys.exit(1)

                data = {"email": init_user_email, "admin": True}
                if init_user_fname:
                    data["first_name"] = init_user_fname
                if init_user_lname:
                    data["last_name"] = init_user_lname

                LOGGER.info("No users exist, creating initial user: %s", data)
                if set_init_user_pass:
                    data["password"] = CONFIG.get("auth.initial_user.password")
                    LOGGER.warning("Creating initial user with password: %s", data["password"])
                    LOGGER.warning("PLEASE REMEMBER TO LOG IN AND CHANGE IT ASAP!!")

                await UsersDB.create(db_session, **data)

    async def start_plaato_service(self):
        from lib.devices.plaato_keg import service_handler as plaato_service_handler

        self.plaato_service = plaato_service_handler

        host = CONFIG.get("tap_monitors.plaato_keg.host", "localhost")
        port = CONFIG.get("tap_monitors.plaato_keg.port", 5001)
        LOGGER.info(f"Starting Plaato TCP server on {host}:{port}")

        self.tcp_task = asyncio.create_task(plaato_service_handler.connection_handler.start_server(host=host, port=port))

    async def start_http_server(self):
        """Start the HTTP/WebSocket server"""
        host = CONFIG.get("api.host", "localhost")
        port = CONFIG.get("api.port", 5000)
        LOGGER.info(f"Serving API on {host}:{port}")

        config = uvicorn.Config(
            app=api,
            host=host,
            port=port,
            log_level=self.log_level.lower(),
            proxy_headers=True,  # Handle X-Forwarded-* headers (replaces ProxyFix)
            forwarded_allow_ips="*",
            reload=CONFIG.get("ENV") == "development",  # Auto-reload in development
        )
        self.http_server = uvicorn.Server(config)
        await self.http_server.serve()

    async def run(self):
        # Initialize first user if needed
        LOGGER.info("Checking for initial user...")
        await self.initialize_first_user()

        start_plaato_service = CONFIG.get("tap_monitors.plaato_keg.enabled")
        if start_plaato_service:
            LOGGER.info("Starting the Plaato TCP Service task...")
            await self.start_plaato_service()

        try:
            await self.start_http_server()
        except asyncio.CancelledError:
            LOGGER.info("Application shutting down...")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Cleanup on shutdown"""
        LOGGER.info("Shutting down application...")

        if self.plaato_service and self.plaato_service.connection_handler:
            self.plaato_service.connection_handler.stop_server()

        if self.tcp_task:
            self.tcp_task.cancel()
            try:
                await self.tcp_task
            except asyncio.CancelledError:
                pass

        if self.plaato_service:
            await self.plaato_service.connection_handler.stop_server()

        LOGGER.info("Application shutdown complete")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--log",
        dest="loglevel",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=os.environ.get("LOG_LEVEL", logging.get_def_log_level(CONFIG)).upper(),
        help="Set the logging level",
    )
    args = parser.parse_args()

    # Update logging level
    logging_level = logging.get_log_level(args.loglevel)
    logging.set_log_level(logging_level)

    app_instance = Application(log_level=args.loglevel)

    try:
        asyncio.run(app_instance.run())
    except KeyboardInterrupt:
        LOGGER.info("Received keyboard interrupt, shutting down...")
        app_instance.shutdown()
    except Exception as e:
        LOGGER.error(f"Unhandled application error", stack_info=True, exc_info=True)
        sys.exit(1)
