#! /usr/bin/env python3

import argparse
import logging as std_logging
import os
import sys
import uuid

from lib.config import Config
from lib import logging

# Initialize configuration
CONFIG = Config()
CONFIG.setup(config_files=["default.json"])

# Initialize logging
logging.init(fmt=logging.DEFAULT_LOG_FMT)

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.exc import IntegrityError, DataError
from schema import SchemaError

#from resources.exceptions import UserMessageError

class UserMessageError(Exception):
    def __init__(self, response_code, user_msg=None, server_msg=None):
        self.user_msg = user_msg or ""
        self.server_msg = server_msg or self.user_msg
        self.response_code = response_code
        super().__init__()

LOGGER = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Brewhouse Manager",
    version="0.6.1",
    docs_url="/api/docs",
    redoc_url="/api/redoc" if CONFIG.get("ENV") == "development" else None,
)

# Session middleware - must be added before any dependencies use it
app.add_middleware(
    SessionMiddleware,
    secret_key=CONFIG.get("app.secret_key", str(uuid.uuid4())),
    session_cookie="session",
    max_age=None,  # Session expires when browser closes
    same_site=CONFIG.get("api.cookies.samesite", "lax"),
    https_only=CONFIG.get("api.cookies.secure", True),
)

# CORS middleware
if CONFIG.get("ENV") == "development":
    LOGGER.debug("Setting up development environment with full CORS")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Production - selective CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=CONFIG.get("api.registration_allow_origins", []),
        allow_methods=["PUT", "OPTIONS"],
        allow_headers=["Content-Type"],
        expose_headers=["Content-Type"],
        max_age=3000,
        allow_credentials=True,
    )


# Exception handlers
@app.exception_handler(UserMessageError)
async def user_message_error_handler(request: Request, exc: UserMessageError):
    """Handle custom user message errors from resources"""
    LOGGER.exception(exc.server_msg)
    return JSONResponse(
        status_code=exc.response_code,
        content={"message": exc.user_msg}
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    return JSONResponse(
        status_code=400,
        content={"message": f"Validation error: {str(exc)}"}
    )


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors"""
    LOGGER.exception("Database integrity error:")
    return JSONResponse(
        status_code=400,
        content={"message": "Database integrity error"}
    )


@app.exception_handler(DataError)
async def data_error_handler(request: Request, exc: DataError):
    """Handle database data errors"""
    LOGGER.exception("Database data error:")
    return JSONResponse(
        status_code=400,
        content={"message": "Invalid data format"}
    )


@app.exception_handler(SchemaError)
async def schema_error_handler(request: Request, exc: SchemaError):
    """Handle schema validation errors"""
    return JSONResponse(
        status_code=400,
        content={"message": f"Schema validation error: {str(exc)}"}
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler"""
    LOGGER.exception("Unhandled exception while processing request:")
    return JSONResponse(
        status_code=500,
        content={"message": "An unhandled error occurred while processing the request"}
    )

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail}
    )


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    return {"healthy": True}


# Register routers
from routers import (
    auth, beers, beverages, batches, locations, sensors, taps, users,
    dashboard, assets, settings, external_brew_tools, image_transitions,
    pages
)

app.include_router(auth.router)
app.include_router(beers.router)
app.include_router(beverages.router)
app.include_router(batches.router, prefix="/api/v1/batches", tags=["batches"])
app.include_router(batches.router, prefix="/api/v1/locations/{location}/batches", tags=["location_batches"])
app.include_router(batches.router, prefix="/api/v1/beers/{beer_id}/batches", tags=["beer_batches"])
app.include_router(batches.router, prefix="/api/v1/beverages/{beverage_id}/batches", tags=["beverage_batches"])
app.include_router(locations.router)
app.include_router(sensors.router, prefix="/api/v1/sensors", tags=["sensors"])
app.include_router(sensors.router, prefix="/api/v1/locations/{location}/sensors", tags=["location_sensors"])
app.include_router(taps.router, prefix="/api/v1/taps", tags=["taps"])
app.include_router(taps.router, prefix="/api/v1/locations/{location}/taps", tags=["location_taps"])
app.include_router(users.router)
app.include_router(dashboard.router)
app.include_router(assets.router)
app.include_router(settings.router)
app.include_router(external_brew_tools.router)
app.include_router(image_transitions.router)

# Register pages router last (has catch-all routes)
app.include_router(pages.router)


# Mount static files (Angular SPA)
STATIC_DIR = os.path.join(os.getcwd(), "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# SPA routing - serve index.html for all unmatched routes
@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """
    Serve Angular SPA for all unmatched routes.
    This allows Angular to handle client-side routing.
    """
    # Check if it's a file in static directory
    static_file_path = os.path.join(STATIC_DIR, full_path)
    if os.path.isfile(static_file_path):
        return FileResponse(static_file_path)

    # Otherwise serve index.html (Angular will handle routing)
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)

    # If no static directory exists, return 404
    return JSONResponse(
        status_code=404,
        content={"message": "Not found"}
    )


async def initialize_first_user():
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


# Application startup
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    LOGGER.info("Starting Brewhouse Manager API...")
    LOGGER.debug("Config: %s", CONFIG.data_flat)


if __name__ == "__main__":
    import asyncio
    import uvicorn

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-l",
        "--log",
        dest="loglevel",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=os.environ.get("LOG_LEVEL", "INFO").upper(),
        help="Set the logging level",
    )
    args = parser.parse_args()

    # Update logging level
    logging_level = getattr(std_logging, args.loglevel)
    std_logging.getLogger().setLevel(logging_level)

    port = CONFIG.get("api.port", 5000)

    # Initialize first user if needed
    LOGGER.info("Checking for initial user...")
    asyncio.run(initialize_first_user())

    # Run uvicorn
    LOGGER.info("Serving on port %s", port)
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=port,
        log_level=args.loglevel.lower(),
        proxy_headers=True,  # Handle X-Forwarded-* headers (replaces ProxyFix)
        forwarded_allow_ips="*",
        reload=CONFIG.get("ENV") == "development",  # Auto-reload in development
    )
