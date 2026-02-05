"""Settings router for FastAPI"""

from fastapi import APIRouter

from lib import logging
from lib.config import Config

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])
LOGGER = logging.getLogger(__name__)

CONFIG = Config()


@router.get("", response_model=dict)
async def get_settings():
    """Get application settings (no auth required)"""
    data = {
        "googleSSOEnabled": CONFIG.get("auth.oidc.google.enabled"),
        "taps": {
            "refresh": {
                "baseSec": CONFIG.get("taps.refresh.base_sec"),
                "variable": CONFIG.get("taps.refresh.variable")
            }
        },
        "beverages": {
            "defaultType": CONFIG.get("beverages.default_type"),
            "supportedTypes": CONFIG.get("beverages.supported_types")
        },
        "dashboard": {
            "refreshSec": CONFIG.get("dashboard.refresh_sec")
        },
    }
    plaato_enabled = CONFIG.get("sensors.plaato_keg.enabled", False)
    plaato = {
        "enabled": plaato_enabled
    }
    if plaato_enabled:
        plaato["config"] = {
            "host": CONFIG.get("sensors.plaato_keg.device_config.host", "localhost"),
            "port": CONFIG.get("sensors.plaato_keg.device_config.port", 5001)
        }
    
    data["plaato_keg_devices"] = plaato

    return data
