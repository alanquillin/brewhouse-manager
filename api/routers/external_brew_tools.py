"""External brew tools router for FastAPI"""

from typing import List

from fastapi import APIRouter, Depends

from fastapi import HTTPException

from dependencies.auth import AuthUser, require_user
from lib import external_brew_tools, logging
from services.base import transform_dict_to_camel_case

router = APIRouter(prefix="/api/v1/external_brew_tools", tags=["external_brew_tools"])
LOGGER = logging.getLogger(__name__)


@router.get("/types", response_model=List[str])
async def list_external_brew_tool_types(
    current_user: AuthUser = Depends(require_user),
):
    """List available external brewing tool types"""
    return list(external_brew_tools.get_types())


@router.get("/{tool_name}/hello", response_model=dict)
async def get_external_brew_tool_hello(
    tool_name: str,
    current_user: AuthUser = Depends(require_user),
):
    """Get hello/info for a specific external brewing tool"""
    tool = external_brew_tools.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"External brew tool '{tool_name}' not found")
    return {"message": tool.say_hello()}


@router.get("/{tool_name}/search", response_model=List[dict])
async def search_external_brew_tool(
    tool_name: str,
    current_user: AuthUser = Depends(require_user),
):
    """Search recipes in an external brewing tool"""
    tool = external_brew_tools.get_tool(tool_name)
    if not tool:
        raise HTTPException(status_code=404, detail=f"External brew tool '{tool_name}' not found")
    results = await tool.search_batches()

    return [transform_dict_to_camel_case(r) if isinstance(r, dict) else r for r in results]
