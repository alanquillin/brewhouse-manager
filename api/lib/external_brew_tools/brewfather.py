import base64

import httpx
from httpx import BasicAuth, AsyncClient, TimeoutException

from db import session_scope
from db.batches import Batches as BatchesDB
from db.beers import Beers as BeersDB
from lib.external_brew_tools import ExternalBrewToolBase
from lib.external_brew_tools.exceptions import ResourceNotFoundError

class Brewfather(ExternalBrewToolBase):
    async def get_batch_details(self, batch_id=None, batch=None, meta=None):
        if not batch_id and not batch and not meta:
            raise Exception("WTH!!")

        if not meta:
            if not batch:
                with session_scope as session:
                    batch = BatchesDB.get_by_pkey(session, batch_id)
            meta = batch.external_brewing_tool_meta

        fields = [
            "batchNo",
            "measuredAbv",
            "status",
            "estimatedIbu",
            "brewDate",
            "bottlingDate",
            "estimatedColor",
            "recipe.name",
            "recipe.img_url",
            "recipe.style.name",
            "recipe.style.type",
        ]
        batch = await self._get_batch(meta=meta, params={"include": ",".join(fields)})
        recipe = batch.get("recipe", {})
        status = batch.get("status")

        details = {
            "name": recipe.get("name"),
            "abv": batch.get("measuredAbv"),
            "img_url": recipe.get("img_url"),
            "status": status,
            "style": recipe.get("style", {}).get("name"),
            "ibu": batch.get("estimatedIbu"),
            "brew_date": batch.get("brewDate"),
            "keg_date": batch.get("bottlingDate"),
            "srm": batch.get("estimatedColor"),
            "batch_number": str(batch.get("batchNo")),
        }

        complete_statuses = self.config.get("external_brew_tools.brewfather.completed_statuses")
        if not status.lower() in [s.lower() for s in complete_statuses]:
            details["_refresh_on_next_check"] = True
            details["_refresh_reason"] = "The batch was not in a completed status: %s." % ", ".join(complete_statuses)

        return details
    
    async def get_recipe_details(self, beer_id=None, beer=None, meta=None):
        if not beer_id and not beer and not meta:
            raise Exception("WTH!!")

        if not meta:
            if not beer:
                with session_scope as session:
                    beer = BeersDB.get_by_pkey(session, beer_id)
            meta = beer.external_brewing_tool_meta

        fields = [
            "measuredAbv",
            "status",
            "ibu",
            "color",
            "name",
            "img_url",
            "style.name",
            "style.type",
            "abv"
        ]
        recipe = await self._get_recipe(meta=meta, params={"include": ",".join(fields)})

        details = {
            "name": recipe.get("name"),
            "abv": recipe.get("abv"),
            "img_url": recipe.get("img_url"),
            "style": recipe.get("style", {}).get("name"),
            "ibu": recipe.get("ibu"),
            "srm": recipe.get("color"),
        }

        return details

    async def search_batches(self, meta=None):
        return await self._get_batches(meta=meta)

    async def _get_batches(self, meta=None):
        data, _ = await self._get(f"v2/batches", meta)
        return data

    async def _get_batch(self, batch_id=None, meta=None, params=None):
        if not batch_id and not meta:
            raise Exception("WTH!!")

        if not batch_id:
            batch_id = meta.get("batch_id")
        data, status_code = await self._get(f"v2/batches/{batch_id}", meta, params=params)
        if status_code == 404:
            raise ResourceNotFoundError(batch_id)
        
        return data
    
    async def _get_recipes(self, meta=None):
        data, _ = await self._get(f"v2/recipes", meta)
        return data

    async def _get_recipe(self, recipe_id=None, meta=None, params=None):
        if not recipe_id and not meta:
            raise Exception("WTH!!")

        if not recipe_id:
            recipe_id = meta.get("recipe_id")
        data, status_code = await self._get(f"v2/recipes/{recipe_id}", meta, params=params)
        if status_code == 404:
            raise ResourceNotFoundError(recipe_id)
        
        return data
    
    async def _get(self, path, meta, params=None):
        url = f"https://api.brewfather.app/{path}"
        self.logger.debug("GET Request: %s, params: %s", url, params)
        async with AsyncClient() as client:
            try:
                kwargs = {}
                timeout = self.config.get("external_brew_tools.brewfather.timeout_sec")
                if timeout:
                    kwargs["timeout"] = timeout
                resp = await client.get(url, auth=self._get_auth(meta), params=params, **kwargs)
                self.logger.debug("GET response code: %s", resp.status_code)
                if resp.status_code == 200:
                    j = resp.json()
                    self.logger.debug("GET response JSON: %s", j)
                    return j, resp.status_code
                return None, resp.status_code
            except TimeoutException:
                self.logger.error(f"brewfather timeout calling {path}")
                raise

    def _get_auth(self, meta=None):
        if meta is None:
            meta = {}
        name = meta.get("name")
        config_prefix = f"external_brew_tools.brewfather{'' if not name or name == 'default' else '.' + name}"

        username = meta.get("username")
        api_key = meta.get("api_key")
        if not username:
            username = self.config.get(f"{config_prefix}.username")

        if not api_key:
            api_key = self.config.get(f"{config_prefix}.api_key")
        self.logger.debug("username: %s", username)
        self.logger.debug("api key: %s", api_key)
        return BasicAuth(username, api_key)

    def _say_hello(self):
        return "hello"
