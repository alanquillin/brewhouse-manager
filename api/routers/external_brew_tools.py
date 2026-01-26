"""External brew tools router for FastAPI"""

import logging
from typing import List

from fastapi import APIRouter, Depends

from dependencies.auth import AuthUser, require_user
from lib import external_brew_tools
from lib.util import snake_to_camel

router = APIRouter(prefix="/api/v1/external_brew_tools", tags=["external_brew_tools"])
LOGGER = logging.getLogger(__name__)


@router.get("/types", response_model=List[str])
async def list_external_brew_tool_types(
    current_user: AuthUser = Depends(require_user),
):
    """List available external brewing tool types"""
    return [t for t in external_brew_tools.get_types()]


@router.get("/{tool_name}/hello", response_model=dict)
async def get_external_brew_tool_hello(
    tool_name: str,
    current_user: AuthUser = Depends(require_user),
):
    """Get hello/info for a specific external brewing tool"""
    tool = external_brew_tools.get_tool(tool_name)
    return {"message": tool._say_hello()}


@router.get("/{tool_name}/search", response_model=List[dict])
async def search_external_brew_tool(
    tool_name: str,
    current_user: AuthUser = Depends(require_user),
):
    """Search recipes in an external brewing tool"""
    tool = external_brew_tools.get_tool(tool_name)
    results = tool.list()

    # Transform results to camelCase
    transformed = []
    for result in results:
        if isinstance(result, dict):
            transformed.append(snake_to_camel(result))
        else:
            transformed.append(result)

    return transformed
