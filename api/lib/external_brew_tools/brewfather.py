import base64

import requests
from requests.auth import HTTPBasicAuth

from db import session_scope
from db.batches import Batches as BatchesDB
from db.beers import Beers as BeersDB
from lib.external_brew_tools import ExternalBrewToolBase

class Brewfather(ExternalBrewToolBase):
    def get_batch_details(self, batch_id=None, batch=None, meta=None):
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
        batch = self._get_batch(meta=meta, params={"include": ",".join(fields)})
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
    
    def get_recipe_details(self, beer_id=None, beer=None, meta=None):
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
        recipe = self._get_recipe(meta=meta, params={"include": ",".join(fields)})

        details = {
            "name": recipe.get("name"),
            "abv": recipe.get("abv"),
            "img_url": recipe.get("img_url"),
            "style": recipe.get("style", {}).get("name"),
            "ibu": recipe.get("ibu"),
            "srm": recipe.get("color"),
        }

        return details

    def search_batches(self, meta=None):
        return self._get_batches(meta=meta)

    def _get_batches(self, meta=None):
        return self._get(f"v2/batches", meta)

    def _get_batch(self, batch_id=None, meta=None, params=None):
        if not batch_id and not meta:
            raise Exception("WTH!!")

        if not batch_id:
            batch_id = meta.get("batch_id")
        return self._get(f"v2/batches/{batch_id}", meta, params=params)
    
    def _get_recipes(self, meta=None):
        return self._get(f"v2/recipes", meta)

    def _get_recipe(self, recipe_id=None, meta=None, params=None):
        if not recipe_id and not meta:
            raise Exception("WTH!!")

        if not recipe_id:
            recipe_id = meta.get("recipe_id")
        return self._get(f"v2/recipes/{recipe_id}", meta, params=params)

    def _get(self, path, meta, params=None):
        url = f"https://api.brewfather.app/{path}"
        self.logger.debug("GET Request: %s, params: %s", url, params)
        resp = requests.get(url, auth=self._get_auth(meta), params=params)
        self.logger.debug("GET response code: %s", resp.status_code)
        j = resp.json()
        self.logger.debug("GET response JSON: %s", j)
        return j

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
        return HTTPBasicAuth(username, api_key)

    def _say_hello(self):
        return "hello"
