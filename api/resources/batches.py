import logging
from datetime import date, datetime

from flask_login import login_required, current_user

from db import session_scope
from db.batches import _PKEY as batches_pk
from db.batches import Batches as BatchesDB
from lib.config import Config
from resources import BaseResource, ClientError, NotFoundError, ResourceMixinBase, NotAuthorizedError
from resources.beers import BeerResourceMixin
from resources.beverage import BeverageResourceMixin

G_LOGGER = logging.getLogger(__name__)
G_CONFIG = Config()

class BeerOrBeverageOnlyError(ClientError):
    def __init__(self, response_code=400, **kwargs):
        super().__init__(response_code, "You only associate a beer or a beverage to the selected batch, not both", **kwargs)


class BatchesResourceMixin(ResourceMixinBase):
    @staticmethod
    def transform_response(batch, db_session=None):
        data = ResourceMixinBase.transform_response(batch.to_dict())

        if db_session:
            if batch.beer:
                data["beer"] = BeerResourceMixin.transform_response(batch.beer, db_session=db_session, skip_meta_refresh=True)
                data["beerId"] = data["beer"].get("id")
            
            if batch.beverage:
                data["beverage"] = BeverageResourceMixin.transform_response(batch.beverage)
                data["beverageId"] = data["beverage"].get("id")

        for k in ["brew_date", "keg_date"]:
            d = data.get(k)
            if k in data and isinstance(d, date):
                data[k] = datetime.timestamp(datetime.fromordinal(d.toordinal()))

        return data

    @staticmethod
    def get_request_data(remove_key=[]):
        data = ResourceMixinBase.get_request_data(remove_key=remove_key)

        for k in ["brew_date", "keg_date"]:
            if k in data and data.get(k):
                data[k] = datetime.fromtimestamp(data.get(k))

        return data

class Batches(BaseResource, BatchesResourceMixin):
    @login_required
    def get(self, location=None):
        with session_scope(self.config) as db_session:
            kwargs = {}
            if location:
                location_id = self.get_location_id(location, db_session)
                if not current_user.admin and not location_id in current_user.locations:
                    raise NotAuthorizedError()
                kwargs["locations"] = [location_id]
            elif not current_user.admin:
                kwargs["locations"] = current_user.locations
            
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
    def _get_batch(self, db_session, batch_id, location=None):
        kwargs = {batches_pk: batch_id}
        if location:
            location_id = self.get_location_id(location, db_session)
            if not current_user.admin and not location_id in current_user.locations:
                raise NotAuthorizedError()
            kwargs["locations"] = [location_id]
        batch = BatchesDB.query(db_session, **kwargs)

        if not batch:
            raise NotFoundError()

        batch = batch[0]
            
        if not current_user.admin and not batch.location_id in current_user.locations:
            raise NotAuthorizedError()
        return batch

    @login_required
    def get(self, batch_id, location=None):
        with session_scope(self.config) as db_session:
            batch = self._get_batch(db_session, batch_id, location=location)

            return self.transform_response(batch, db_session=db_session)

    @login_required
    def patch(self, batch_id, location=None):
        with session_scope(self.config) as db_session:
            batch = self._get_batch(db_session, batch_id, location=location)
            
            data = self.get_request_data()

            for k,v in data.items():
                if v == "":
                    data[k] = None

            batch = BatchesDB.update(db_session, batch.id, **data)

            return self.transform_response(batch, db_session=db_session)

    @login_required
    def delete(self, batch_id, location=None):
        with session_scope(self.config) as db_session:
            batch = self._get_batch(db_session, batch_id, location=location)

            BatchesDB.delete(db_session, batch.id)

            return True
