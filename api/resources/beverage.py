import logging
from datetime import date, datetime

from flask import request
from flask_login import login_required, current_user

from db import session_scope
from db.beverages import Beverages as BeveragesDB
from lib.config import Config
from resources import BaseResource, NotFoundError, ResourceMixinBase, ImageTransitionMixin, ImageTransitionResourceMixin, NotAuthorizedError
from resources.batches import BatchesResourceMixin

G_LOGGER = logging.getLogger(__name__)
G_CONFIG = Config()


class BeverageResourceMixin(ResourceMixinBase):
    @staticmethod
    def transform_response(beverage, db_session=None, include_batches=True, image_transitions=None):
        data = beverage.to_dict()

        if include_batches and beverage.batches:
            data["batches"] = [BatchesResourceMixin.transform_response(b, db_session=db_session) for b in beverage.batches]

        return ImageTransitionResourceMixin.transform_response(data, image_transitions, db_session, beverage_id=beverage.id)

    @staticmethod
    def get_request_data(remove_key=[]):
        data = ResourceMixinBase.get_request_data(remove_key=remove_key)

        # for k in ["brew_date", "keg_date"]:
        #     if k in data and data.get(k):
        #         data[k] = datetime.fromtimestamp(data.get(k))

        return data


class Beverages(BaseResource, BeverageResourceMixin, ImageTransitionMixin):
    def get(self):
        with session_scope(self.config) as db_session:
            beverages = BeveragesDB.query(db_session)
            return [self.transform_response(b, db_session=db_session) for b in beverages]

    @login_required
    def post(self):
        with session_scope(self.config) as db_session:
            data = self.get_request_data(remove_key=["id", "imageTransitions"])

            self.logger.debug("Creating beverage with: %s", data)
            beverage = BeveragesDB.create(db_session, **data)
            transitions = self.process_image_transitions(db_session, beverage_id=beverage.id)

            return self.transform_response(beverage, db_session, transitions)


class Beverage(BaseResource, BeverageResourceMixin, ImageTransitionMixin):
    def _get_beverage(self, db_session, beverage_id):
        beverage = BeveragesDB.get_by_pkey(db_session, beverage_id)

        if not beverage:
            raise NotFoundError()

        return beverage

    def get(self, beverage_id):
        with session_scope(self.config) as db_session:
            beverage = self._get_beverage(db_session, beverage_id)

            return self.transform_response(beverage, db_session=db_session)

    @login_required
    def patch(self, beverage_id):
        with session_scope(self.config) as db_session:
            beverage = self._get_beverage(db_session, beverage_id)

            data = self.get_request_data(remove_key=["id", "imageTransitions"])

            if data:
                beverage = BeveragesDB.update(db_session, beverage.id, **data)
            
            image_transitions = self.process_image_transitions(db_session, beverage_id=beverage_id)
            beverage = BeveragesDB.get_by_pkey(db_session, beverage_id)
            return self.transform_response(beverage, db_session, image_transitions)

    @login_required
    def delete(self, beverage_id):
        with session_scope(self.config) as db_session:
            beverage = self._get_beverage(db_session, beverage_id)

            BeveragesDB.delete(db_session, beverage.id)
            return True
