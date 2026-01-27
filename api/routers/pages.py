"""
Page router for serving Angular SPA.
Handles UI routes and redirects.
"""

import os
from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, RedirectResponse

from dependencies.auth import get_optional_user, AuthUser

router = APIRouter(tags=["pages"], include_in_schema=False)

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
async def auth_required(current_user: AuthUser = Depends(get_optional_user)):
    if current_user and current_user.is_authenticated:
        return await serve_spa()
    return RedirectResponse(url="/login")


# Admin pages
@router.get("/manage/locations")
async def admin(current_user: AuthUser = Depends(get_optional_user)):
    if current_user and current_user.is_authenticated and current_user.admin:
        return await serve_spa()
    return RedirectResponse(url="/forbidden")