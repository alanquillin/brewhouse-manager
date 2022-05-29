import logging
from datetime import date, datetime, timedelta

from flask import request
from flask_login import login_required

from db import session_scope
from db.beverages import _PKEY as beverages_pk
from db.beverages import Beverages as BeveragesDB
from db.locations import Locations as LocationsDB
from lib.config import Config
from lib.external_brew_tools import get_tool as get_external_brewing_tool
from lib.time import parse_iso8601_utc, utcnow_aware
from resources import BaseResource, NotFoundError, ResourceMixinBase
from resources.locations import LocationsResourceMixin

G_LOGGER = logging.getLogger(__name__)
G_CONFIG = Config()


class BeverageResourceMixin(ResourceMixinBase):
    @staticmethod
    def transform_response(beverage):
        data = beverage.to_dict()

        for k in ["brew_date", "keg_date"]:
            d = data.get(k)
            if k in data and isinstance(d, date):
                data[k] = datetime.timestamp(datetime.fromordinal(d.toordinal()))

        return ResourceMixinBase.transform_response(data)

    @staticmethod
    def get_request_data(remove_key=[]):
        data = ResourceMixinBase.get_request_data(remove_key=remove_key)

        for k in ["brew_date", "keg_date"]:
            if k in data and data.get(k):
                data[k] = datetime.fromtimestamp(data.get(k))

        return data


class Beverages(BaseResource, BeverageResourceMixin):
    def get(self, location=None):
        with session_scope(self.config) as db_session:
            if location:
                location_id = self.get_location_id(location, db_session)
                beverages = BeveragesDB.get_by_location(db_session, location_id)
            else:
                beverages = BeveragesDB.query(db_session)
            return [self.transform_response(b) for b in beverages]

    @login_required
    def post(self):
        with session_scope(self.config) as db_session:
            data = self.get_request_data()

            self.logger.debug("Creating beverage with: %s", data)
            beverage = BeveragesDB.create(db_session, **data)

            return self.transform_response(beverage)


class Beverage(BaseResource, BeverageResourceMixin):
    def get(self, beverage_id):
        with session_scope(self.config) as db_session:
            beverage = BeveragesDB.get_by_pkey(db_session, beverage_id)

            if not beverage:
                raise NotFoundError()

            return self.transform_response(beverage)

    @login_required
    def patch(self, beverage_id):
        with session_scope(self.config) as db_session:
            beverage = BeveragesDB.get_by_pkey(db_session, beverage_id)

            if not beverage:
                raise NotFoundError()

            data = self.get_request_data(remove_key=["id"])

            beverage = BeveragesDB.update(db_session, beverage_id, **data)

            return self.transform_response(beverage)

    @login_required
    def delete(self, beverage_id):
        with session_scope(self.config) as db_session:
            beverage = BeveragesDB.get_by_pkey(db_session, beverage_id)

            if not beverage:
                raise NotFoundError()

            BeveragesDB.delete(db_session, beverage_id)
            return True
