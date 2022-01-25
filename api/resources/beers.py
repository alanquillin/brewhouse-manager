from datetime import datetime, date
import logging

from flask import request
from flask_login import login_required

from resources import BaseResource, ResourceMixinBase, NotFoundError
from db import session_scope
from db.locations import Locations as LocationsDB
from db.beers import Beers as BeersDB, _PKEY as beers_pk
from lib.config import Config
from lib.external_brew_tools import get_tool as get_external_brewing_tool

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
    def transform_response(beer, db_session=None, skip_meta_refresh=False, **kwargs):
        if not beer:
            return beer

        data = beer.to_dict()
        G_LOGGER.debug(data)
        
        if not skip_meta_refresh:
            force_refresh = request.args.get("force_refresh", "false").lower() in ["true", "yes", "", "1"]

            tool_type = beer.external_brewing_tool
            if tool_type:
                refresh_data=False
                refresh_reason="UNKNOWN"
                meta = data.get("external_brewing_tool_meta", {})
                ex_details = None
                if meta:
                    ex_details = meta.get("details", {})

                if not ex_details:
                    refresh_data = True
                    refresh_reason = "No cached details exist in DB."
                elif ex_details.get("_refresh_on_next_check", False):
                    refresh_data = True
                    refresh_reason = ex_details.get("_refresh_reason", "The beer was marked by the external brewing tool for refresh, reason unknown.")
                elif force_refresh:
                    refresh_data = True
                    refresh_reason = "Forced refresh requested via query string parameter."

                if refresh_data:
                    G_LOGGER.info("Refreshing data from %s for %s.  Reason: %s", tool_type, beer.id, refresh_reason)
                    tool = get_external_brewing_tool(tool_type)
                    ex_details = tool.get_details(beer=beer)
                    if ex_details:
                        G_LOGGER.debug("Extended beer details: %s, updateing database", ex_details)
                        BeerResourceMixin.update(beer.id, {"external_brewing_tool_meta": {**meta, "details": ex_details}}, db_session=db_session)
                    else:
                        G_LOGGER.warning("There and error or no details from %s for %s", tool_type, {k:v for k,v in meta.items() if k != "details"})

        for k in ["brew_date", "keg_date"]:
            d = data.get(k)
            if k in data and isinstance(d, date):
                data[k] = datetime.timestamp(datetime.fromordinal(d.toordinal()))

        return ResourceMixinBase.transform_response(data, **kwargs)
    
    @staticmethod
    def get_request_data(remove_key=[]):
        data = ResourceMixinBase.get_request_data(remove_key=remove_key)

        for k in ["brew_date", "keg_date"]:
            if k in data and data.get(k):
                data[k] = datetime.fromtimestamp(data.get(k))
        
        return data

class Beers(BaseResource, BeerResourceMixin):
    def get(self, location=None):
        with session_scope(self.config) as db_session:
            if location:
                location_id = self.get_location_id(location, db_session)
                beers = BeersDB.get_by_location(db_session, location_id)
            else:
                beers = BeersDB.query(db_session)
            return [self.transform_response(b) for b in beers]
    
    @login_required
    def post(self):
        with session_scope(self.config) as db_session:
            data = self.get_request_data()
                       
            self.logger.debug("Creating beer with: %s", data)
            beer = BeersDB.create(db_session, **data)

            return self.transform_response(beer)


class Beer(BaseResource, BeerResourceMixin):
    def get(self, beer_id):
        with session_scope(self.config) as db_session:
            beer = BeersDB.get_by_pkey(db_session, beer_id)

            if not beer:
                raise NotFoundError()
                
            return self.transform_response(beer)
    
    @login_required
    def patch(self, beer_id):
        with session_scope(self.config) as db_session:
            beer = BeersDB.get_by_pkey(db_session, beer_id)

            if not beer:
                raise NotFoundError()

            data = self.get_request_data(remove_key=["id"])

            external_brewing_tool_meta = data.get("external_brewing_tool_meta", {})
            if external_brewing_tool_meta and beer.external_brewing_tool_meta:
                data["external_brewing_tool_meta"] = {**beer.external_brewing_tool_meta} | external_brewing_tool_meta

            beer = self.update(beer_id, data, db_session=db_session)

            return self.transform_response(beer)

    @login_required
    def delete(self, beer_id):
        with session_scope(self.config) as db_session:
            beer = BeersDB.get_by_pkey(db_session, beer_id)

            if not beer:
                raise NotFoundError()

            BeersDB.delete(db_session, beer_id) 
            return True
        