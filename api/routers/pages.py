"""
Page router for serving Angular SPA.
Handles UI routes and redirects.
"""

import os
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from dependencies.auth import require_user, require_admin, AuthUser

router = APIRouter(tags=["pages"])

STATIC_DIR = os.path.join(os.getcwd(), "static")


async def serve_spa():
    """Serve the Angular SPA index.html"""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"error": "Static files not found"}


# Public pages
@router.get("/")
@router.get("/login")
@router.get("/view/{location}")
@router.get("/tools/volume_calculator")
async def ui():
    return await serve_spa()


# Protected pages
@router.get("/manage")
@router.get("/manage/beers")
@router.get("/manage/beverages")
@router.get("/manage/sensors")
@router.get("/manage/taps")
async def auth_required(current_user: AuthUser = Depends(require_user)):
    return await serve_spa()


# Admin pages
@router.get("/manage/locations")
async def admin(current_user: AuthUser = Depends(require_admin)):
    return await serve_spa()
