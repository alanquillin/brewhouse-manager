"""Assets router for FastAPI"""

from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from dependencies.auth import AuthUser, require_user
from lib import logging
from lib.config import Config
from lib.assets.files import FileAssetManager
from lib.assets.s3 import S3AssetManager

router = APIRouter(prefix="/api/v1/uploads", tags=["assets"])
LOGGER = logging.getLogger(__name__)

CONFIG = Config()

ALLOWED_IMAGE_TYPES = ["beer", "user", "beverage"]


def get_asset_manager():
    """Get the configured asset manager (file or S3)"""
    storage_type = CONFIG.get("uploads.storage_type")
    if storage_type and storage_type.lower() == "s3":
        return S3AssetManager()
    return FileAssetManager()


def is_file_allowed(filename: str, manager) -> bool:
    """Check if file extension is allowed"""
    allowed_extensions = CONFIG.get("uploads.images.allowed_file_extensions")
    if not allowed_extensions:
        return False
    return "." in filename and manager.get_file_extension(filename) in [e.replace(".", "") for e in allowed_extensions]


@router.get("/images/{image_type}", response_model=List[str])
async def list_images(
    image_type: str,
    current_user: AuthUser = Depends(require_user),
):
    """List images of a specific type"""
    if image_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image type '{image_type}'. Must be either 'beer', 'beverage' or 'user'"
        )

    manager = get_asset_manager()
    return manager.list(image_type)


@router.post("/images/{image_type}", response_model=dict)
async def upload_image(
    image_type: str,
    file: UploadFile = File(...),
    current_user: AuthUser = Depends(require_user),
):
    """Upload an image"""
    if image_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image type '{image_type}'. Must be either 'beer', 'beverage' or 'user'"
        )

    if not file or not file.filename:
        raise HTTPException(status_code=400, detail="File is missing in the request.")

    manager = get_asset_manager()
    if not is_file_allowed(file.filename, manager):
        allowed_extensions = CONFIG.get("uploads.images.allowed_file_extensions")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Must be one of: {', '.join(allowed_extensions)}"
        )

    LOGGER.info("Saving uploaded file '%s'", file.filename)
    of, df, dp = manager.save(image_type, file)
    LOGGER.debug("Successfully saved file '%s' as '%s'", of, df)

    return {"sourceFilename": of, "destinationPath": dp}
