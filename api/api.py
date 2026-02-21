#! /usr/bin/env python3
import os
import uuid

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from schema import SchemaError
from sqlalchemy.exc import DataError, IntegrityError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.sessions import SessionMiddleware

from lib import logging
from lib.config import Config

# from resources.exceptions import UserMessageError


class UserMessageError(Exception):
    def __init__(self, response_code, user_msg=None, server_msg=None):
        self.user_msg = user_msg or ""
        self.server_msg = server_msg or self.user_msg
        self.response_code = response_code
        super().__init__()


LOGGER = logging.getLogger(__name__)
CONFIG = Config()

# Create FastAPI app
api = FastAPI(
    title="Brewhouse Manager",
    version="0.8.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc" if CONFIG.get("ENV") == "development" else None,
)

# Session middleware - must be added before any dependencies use it
api.add_middleware(
    SessionMiddleware,
    secret_key=CONFIG.get("app.secret_key", str(uuid.uuid4())),
    session_cookie="session",
    max_age=None,  # Session expires when browser closes
    same_site=CONFIG.get("api.cookies.samesite", "lax"),
    https_only=CONFIG.get("api.cookies.secure", True),
)

# CORS middleware
if CONFIG.get("ENV") in ("development", "test"):
    LOGGER.debug("Setting up development/test environment with full CORS")
    api.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # Production - selective CORS
    api.add_middleware(
        CORSMiddleware,
        allow_origins=CONFIG.get("api.registration_allow_origins", []),
        allow_methods=["PUT", "OPTIONS"],
        allow_headers=["Content-Type"],
        expose_headers=["Content-Type"],
        max_age=3000,
        allow_credentials=True,
    )


# Exception handlers
@api.exception_handler(UserMessageError)
async def user_message_error_handler(request: Request, exc: UserMessageError):
    """Handle custom user message errors from resources"""
    LOGGER.exception(exc.server_msg)
    return JSONResponse(status_code=exc.response_code, content={"message": exc.user_msg})


@api.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle Pydantic validation errors"""
    return JSONResponse(status_code=400, content={"message": f"Validation error: {str(exc)}"})


@api.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors"""
    LOGGER.exception("Database integrity error:")
    return JSONResponse(status_code=400, content={"message": "Database integrity error"})


@api.exception_handler(DataError)
async def data_error_handler(request: Request, exc: DataError):
    """Handle database data errors"""
    LOGGER.exception("Database data error:")
    return JSONResponse(status_code=400, content={"message": "Invalid data format"})


@api.exception_handler(SchemaError)
async def schema_error_handler(request: Request, exc: SchemaError):
    """Handle schema validation errors"""
    return JSONResponse(status_code=400, content={"message": f"Schema validation error: {str(exc)}"})


@api.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    """Catch-all exception handler"""
    LOGGER.exception("Unhandled exception while processing request:")
    return JSONResponse(status_code=500, content={"message": "An unhandled error occurred while processing the request"})


@api.exception_handler(StarletteHTTPException)
async def http_exception_handler(request, exc: StarletteHTTPException):
    return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})


# Health check endpoints
@api.get("/health")
async def health_check():
    """Health check endpoint for load balancers"""
    return {"healthy": True}


@api.get("/api/v1/healthz")
async def healthz():
    """Health check endpoint for Kubernetes/Docker health checks"""
    return {"status": "ok"}


# Register routers
from routers import (
    assets,
    auth,
    batches,
    beers,
    beverages,
    dashboard,
    external_brew_tools,
    image_transitions,
    kegtron,
    locations,
    pages,
    plaato_keg,
    settings,
    tap_monitors,
    taps,
    users,
)

api.include_router(auth.router)
api.include_router(beers.router)
api.include_router(beverages.router)
api.include_router(batches.router, prefix="/api/v1/batches", tags=["batches"])
api.include_router(batches.router, prefix="/api/v1/locations/{location}/batches", tags=["location_batches"])
api.include_router(batches.router, prefix="/api/v1/beers/{beer_id}/batches", tags=["beer_batches"])
api.include_router(batches.router, prefix="/api/v1/beverages/{beverage_id}/batches", tags=["beverage_batches"])
api.include_router(locations.router)
api.include_router(kegtron.router)
api.include_router(plaato_keg.router)
api.include_router(tap_monitors.router, prefix="/api/v1/tap_monitors", tags=["tap_monitors"])
api.include_router(tap_monitors.router, prefix="/api/v1/locations/{location}/tap_monitors", tags=["location_tap_monitors"])
api.include_router(taps.router, prefix="/api/v1/taps", tags=["taps"])
api.include_router(taps.router, prefix="/api/v1/locations/{location}/taps", tags=["location_taps"])
api.include_router(users.router)
api.include_router(dashboard.router)
api.include_router(assets.router)
api.include_router(settings.router)
api.include_router(external_brew_tools.router)
api.include_router(image_transitions.router)

# Register pages router last (has catch-all routes)
api.include_router(pages.router)


# Mount static files (Angular SPA)
STATIC_DIR = os.path.join(os.getcwd(), "static")
if os.path.exists(STATIC_DIR):
    api.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# SPA routing - serve index.html for all unmatched routes
@api.get("/{full_path:path}", include_in_schema=False)
async def serve_spa(full_path: str):
    """
    Serve Angular SPA for all unmatched routes.
    This allows Angular to handle client-side routing.
    """
    # Check if it's a file in static directory
    static_file_path = os.path.join(STATIC_DIR, full_path)
    resolved = os.path.realpath(static_file_path)
    if resolved.startswith(os.path.realpath(STATIC_DIR) + os.sep) and os.path.isfile(resolved):
        return FileResponse(resolved)

    # Otherwise serve index.html (Angular will handle routing)
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)

    # If no static directory exists, return 404
    return JSONResponse(status_code=404, content={"message": "Not found"})
