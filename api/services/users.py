import logging
from sqlalchemy.ext.asyncio import AsyncSession

from services.base import transform_dict_to_camel_case

class UserService():
    @staticmethod
    async def transform_response(user, current_user):
        data = user.to_dict()
        FILTERED_KEYS = ["password_hash", "google_oidc_id"]

        user_c = current_user
        if not user_c.admin and user_c.id != user.id:
            FILTERED_KEYS.append("api_key")

        data["password_enabled"] = False
        if data.get("password_hash"):
            data["password_enabled"] = True

        for key in FILTERED_KEYS:
            if key in data:
                del data[key]
        
        locations = []
        await user.awaitable_attrs.locations
        if user.locations:
            from services.locations import LocationService

            locations = [await LocationService.transform_response(l) for l in user.locations]
        data["locations"] = locations
        
        return transform_dict_to_camel_case(data)