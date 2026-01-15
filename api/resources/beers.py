import logging
from datetime import date, datetime, timedelta

from flask import request
from flask_login import login_required, current_user

from db import session_scope
from db.beers import Beers as BeersDB
from lib.config import Config
from lib.external_brew_tools import get_tool as get_external_brewing_tool
from lib.time import parse_iso8601_utc, utcnow_aware
from resources import BaseResource, NotFoundError, ResourceMixinBase, ImageTransitionMixin, ImageTransitionResourceMixin
from resources.batches import BatchesResourceMixin

G_LOGGER = logging.getLogger(__name__)
G_CONFIG = Config()


class BeerResourceMixin(ResourceMixinBase):
    @staticmethod
    def update(beer_id, data, db_session=None):
        if not db_session:
            with session_scope(G_CONFIG) as db_session:
                return BeerResourceMixin.update(beer_id, data, db_session=db_session)

        G_LOGGER.debug("Updating beer %s with: %s", beer_id, data)
        BeersDB.update(db_session, beer_id, **data)

    @staticmethod
    def transform_response(beer, db_session=None, skip_meta_refresh=False, include_batches=True, image_transitions=None, include_location=True, **kwargs):
        if not beer:
            return beer

        data = beer.to_dict()
        
        if include_batches and beer.batches:
            data["batches"] = [BatchesResourceMixin.transform_response(b, skip_meta_refresh=skip_meta_refresh, db_session=db_session, include_location=include_location) for b in beer.batches]

        if not skip_meta_refresh:
            force_refresh = request.args.get("force_refresh", "false").lower() in ["true", "yes", "", "1"]

            tool_type = beer.external_brewing_tool
            meta = data.get("external_brewing_tool_meta", {})
            if tool_type and meta:
                refresh_data = False
                refresh_reason = "UNKNOWN"
                refresh_buffer = G_CONFIG.get(f"external_brew_tools.{tool_type}.refresh_buffer_sec.soft")
                now = utcnow_aware()
                
                ex_details = meta.get("details", {})

                if not ex_details:
                    refresh_data = True
                    refresh_reason = "No cached details exist in DB."
                elif force_refresh:
                    refresh_data = True
                    refresh_reason = "Forced refresh requested via query string parameter."
                elif ex_details.get("_refresh_on_next_check", False):
                    refresh_data = True
                    refresh_reason = ex_details.get("_refresh_reason", "The beer was marked by the external brewing tool for refresh, reason unknown.")

                if not refresh_data:
                    last_refresh = ex_details.get("_last_refreshed_on")
                    if last_refresh:
                        skip_until = parse_iso8601_utc(last_refresh) + timedelta(seconds=refresh_buffer)

                        G_LOGGER.debug("Checking is last refresh date '%s' > now '%s'", skip_until.isoformat(), now.isoformat())
                        if skip_until < now:
                            G_LOGGER.info("Refresh skip buffer exceeded, refreshing data.  Tool: %s, beer_id: %s, skip_until: %s", tool_type, beer.id, skip_until.isoformat())
                            refresh_data = True
                            refresh_reason = "Refresh skip buffer exceeded"
                    else:
                        refresh_data = True
                        refresh_reason = "No _last_refreshed_on date recorded, refreshing."

                if refresh_data:
                    G_LOGGER.info("Refreshing data from %s for %s.  Reason: %s", tool_type, beer.id, refresh_reason)
                    tool = get_external_brewing_tool(tool_type)
                    ex_details = tool.get_recipe_details(beer=beer)
                    if ex_details:
                        ex_details["_last_refreshed_on"] = now.isoformat()
                        G_LOGGER.debug("Extended recipe details: %s, updating database", ex_details)
                        BeerResourceMixin.update(beer.id, {"external_brewing_tool_meta": {**meta, "details": ex_details}}, db_session=db_session)
                    else:
                        G_LOGGER.warning("There and error or no details from %s for %s", tool_type, {k: v for k, v in meta.items() if k != "details"})

        return ImageTransitionResourceMixin.transform_response(data, image_transitions, db_session, beer_id=beer.id, **kwargs)

    @staticmethod
    def get_request_data(remove_key=[]):
        data = ResourceMixinBase.get_request_data(remove_key=remove_key)

        return data


class Beers(BaseResource, BeerResourceMixin, ImageTransitionMixin):
    @login_required
    def get(self):
        with session_scope(self.config) as db_session:
            beers = BeersDB.query(db_session)
            return [self.transform_response(b, db_session=db_session) for b in beers]

    @login_required
    def post(self):
        with session_scope(self.config) as db_session:
            data = self.get_request_data(remove_key=["id", "imageTransitions"])

            self.logger.debug("Creating beer with: %s", data)
            beer = BeersDB.create(db_session, **data)

            transitions = self.process_image_transitions(db_session, beer_id=beer.id)

            return self.transform_response(beer, image_transitions=transitions)


class Beer(BaseResource, BeerResourceMixin, ImageTransitionMixin):
    def _get_beer(self, db_session, beer_id):
        beer = BeersDB.get_by_pkey(db_session, beer_id)

        if not beer:
            raise NotFoundError()

        return beer

    @login_required
    def get(self, beer_id):
        with session_scope(self.config) as db_session:
            beer = self._get_beer(db_session, beer_id)

            return self.transform_response(beer, db_session=db_session)

    @login_required
    def patch(self, beer_id):
        with session_scope(self.config) as db_session:
            beer = self._get_beer(db_session, beer_id)
            data = self.get_request_data(remove_key=["id", "imageTransitions"])

            external_brewing_tool_meta = data.get("external_brewing_tool_meta", {})
            if external_brewing_tool_meta and beer.external_brewing_tool_meta:
                data["external_brewing_tool_meta"] = {**beer.external_brewing_tool_meta} | external_brewing_tool_meta

            self.logger.debug("Updating beer %s with data: %s", beer_id, data)

            if data:
                beer = self.update(beer_id, data, db_session=db_session)

            image_transitions = self.process_image_transitions(db_session, beer_id=beer_id)
            beer = BeersDB.get_by_pkey(db_session, beer_id)

            return self.transform_response(beer, db_session=db_session, image_transitions=image_transitions)

    @login_required
    def delete(self, beer_id):
        with session_scope(self.config) as db_session: 
            beer = self._get_beer(db_session, beer_id)

            BeersDB.delete(db_session, beer.id)
            return True
