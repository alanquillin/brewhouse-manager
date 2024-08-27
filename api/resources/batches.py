import logging
from datetime import date, datetime, timedelta


from flask import request
from flask_login import login_required, current_user

from db import session_scope
from db.batches import _PKEY as batches_pk
from db.batches import Batches as BatchesDB
from lib.config import Config
from lib.external_brew_tools import get_tool as get_external_brewing_tool
from lib.time import parse_iso8601_utc, utcnow_aware
from resources import BaseResource, ClientError, NotFoundError, ResourceMixinBase, NotAuthorizedError
# from resources.beers import BeerResourceMixin
# from resources.beverage import BeverageResourceMixin

G_LOGGER = logging.getLogger(__name__)
G_CONFIG = Config()

class BeerOrBeverageOnlyError(ClientError):
    def __init__(self, response_code=400, **kwargs):
        super().__init__(response_code, "You only associate a beer or a beverage to the selected batch, not both", **kwargs)


class BatchesResourceMixin(ResourceMixinBase):
    @staticmethod
    def update(batch_id, data, db_session=None):
        if not db_session:
            with session_scope(G_CONFIG) as db_session:
                return BatchesResourceMixin.update(batch_id, data, db_session=db_session)

        G_LOGGER.debug("Updating batch %s with: %s", batch_id, data)
        BatchesDB.update(db_session, batch_id, **data)

    @staticmethod
    def transform_response(batch, skip_meta_refresh=False, db_session=None):
        data = batch.to_dict()

        if not skip_meta_refresh:
            force_refresh = request.args.get("force_refresh", "false").lower() in ["true", "yes", "", "1"]

            tool_type = batch.external_brewing_tool
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
                    refresh_reason = ex_details.get("_refresh_reason", "The batch was marked by the external brewing tool for refresh, reason unknown.")

                if not refresh_data:
                    last_refresh = ex_details.get("_last_refreshed_on")
                    if last_refresh:
                        skip_until = parse_iso8601_utc(last_refresh) + timedelta(seconds=refresh_buffer)

                        G_LOGGER.debug("Checking is last refresh date '%s' > now '%s'", skip_until.isoformat(), now.isoformat())
                        if skip_until < now:
                            G_LOGGER.info("Refresh skip buffer exceeded, refreshing data.  Tool: %s, batch_id: %s, skip_until: %s", tool_type, batch.id, skip_until.isoformat())
                            refresh_data = True
                            refresh_reason = "Refresh skip buffer exceeded"
                    else:
                        refresh_data = True
                        refresh_reason = "No _last_refreshed_on date recorded, refreshing."

                if refresh_data:
                    G_LOGGER.info("Refreshing data from %s for %s.  Reason: %s", tool_type, batch.id, refresh_reason)
                    tool = get_external_brewing_tool(tool_type)
                    ex_details = tool.get_batch_details(batch=batch)
                    if ex_details:
                        ex_details["_last_refreshed_on"] = now.isoformat()
                        G_LOGGER.debug("Extended batch details: %s, updating database", ex_details)
                        BatchesResourceMixin.update(batch.id, {"external_brewing_tool_meta": {**meta, "details": ex_details}}, db_session=db_session)
                    else:
                        G_LOGGER.warning("There and error or no details from %s for %s", tool_type, {k: v for k, v in meta.items() if k != "details"})

        for k in ["brew_date", "keg_date"]:
            d = data.get(k)
            if d and isinstance(d, date):
                data[k] = datetime.timestamp(datetime.fromordinal(d.toordinal()))

        return ResourceMixinBase.transform_response(data)

    @staticmethod
    def get_request_data(remove_key=[]):
        data = ResourceMixinBase.get_request_data(remove_key=remove_key)

        for k in ["brew_date", "keg_date"]:
            if k in data and data.get(k):
                data[k] = datetime.fromtimestamp(data.get(k))

        return data

class Batches(BaseResource, BatchesResourceMixin):
    @login_required
    def get(self, beer_id=None, beverage_id=None):
        with session_scope(self.config) as db_session:
            kwargs = {}
            if beer_id:
                kwargs["beer_id"] = beverage_id
            if beverage_id:
                kwargs["beverage_id"] = beverage_id
            
            batches = BatchesDB.query(db_session, **kwargs)
            return [self.transform_response(b, db_session=db_session) for b in batches]

    @login_required
    def post(self, location=None):
        with session_scope(self.config) as db_session:
            data = self.get_request_data()
            if location:
                location_id = self.get_location_id(location, db_session)
                if not current_user.admin and not location_id in current_user.locations:
                    raise NotAuthorizedError()
                data["location_id"] = location_id

            if not current_user.admin and not data.get("location_id") in current_user.locations:
                raise NotAuthorizedError()

            beer_id = data.get("beer_id")
            if beer_id == "":
                beer_id = None
            beverage_id = data.get("beverage_id")
            if beverage_id == "":
                beverage_id = None

            if beer_id and beverage_id:
                raise BeerOrBeverageOnlyError()
            

            batch = BatchesDB.create(db_session, **data)

            return self.transform_response(batch, db_session=db_session)


class Batch(BaseResource, BatchesResourceMixin):
    def _get_batch(self, db_session, batch_id, beer_id=None, beverage_id=None):
        kwargs = {batches_pk: batch_id}
        if beer_id:
                kwargs["beer_id"] = beverage_id
        if beverage_id:
            kwargs["beverage_id"] = beverage_id
        
        batch = BatchesDB.query(db_session, **kwargs)

        if not batch:
            raise NotFoundError()

        batch = batch[0]
            
        if not current_user.admin and not batch.location_id in current_user.locations:
            raise NotAuthorizedError()
        return batch

    @login_required
    def get(self, batch_id, beer_id=None, beverage_id=None):
        with session_scope(self.config) as db_session:
            batch = self._get_batch(db_session, batch_id, beer_id=beer_id, beverage_id=beverage_id)

            return self.transform_response(batch, db_session=db_session)

    @login_required
    def patch(self, batch_id, beer_id=None, beverage_id=None):
        with session_scope(self.config) as db_session:
            batch = self._get_batch(db_session, batch_id, beer_id=beer_id, beverage_id=beverage_id)
            
            data = self.get_request_data()

            for k,v in data.items():
                if v == "":
                    data[k] = None
            
            external_brewing_tool_meta = data.get("external_brewing_tool_meta", {})
            if external_brewing_tool_meta and batch.external_brewing_tool_meta:
                data["external_brewing_tool_meta"] = {**batch.external_brewing_tool_meta} | external_brewing_tool_meta

            batch = BatchesDB.update(db_session, batch.id, **data)

            return self.transform_response(batch, db_session=db_session)

    @login_required
    def delete(self, batch_id, beer_id=None, beverage_id=None):
        with session_scope(self.config) as db_session:
            batch = self._get_batch(db_session, batch_id, beer_id=beer_id, beverage_id=beverage_id)

            BatchesDB.delete(db_session, batch.id)

            return True
