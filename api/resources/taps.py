from flask_login import login_required

from db import session_scope
from db.taps import _PKEY as taps_pk
from db.taps import Taps as TapsDB
from resources import BaseResource, ClientError, NotFoundError, ResourceMixinBase
from resources.beers import BeerResourceMixin
from resources.locations import LocationsResourceMixin
from resources.sensors import SensorResourceMixin


class BeerOrBeverageOnlyError(ClientError):
    def __init__(self, response_code=400, **kwargs):
        super().__init__(response_code, "You only associate a beer or a beverage to the selected tap, not both", **kwargs)


class TapsResourceMixin(ResourceMixinBase):
    @staticmethod
    def transform_response(tap, db_session=None):
        data = ResourceMixinBase.transform_response(tap.to_dict())

        if tap.beer:
            data["beer"] = BeerResourceMixin.transform_response(tap.beer, db_session=db_session, skip_meta_refresh=True)

        if tap.location:
            data["location"] = LocationsResourceMixin.transform_response(tap.location)

        if tap.sensor:
            data["sensor"] = SensorResourceMixin.transform_response(tap.sensor)

        return data


class Taps(BaseResource, TapsResourceMixin):
    def get(self, location=None):
        with session_scope(self.config) as db_session:
            if location:
                location_id = self.get_location_id(location, db_session)
                taps = TapsDB.get_by_location(db_session, location_id)
            else:
                taps = TapsDB.query(db_session)
            return [self.transform_response(t, db_session=db_session) for t in taps]

    @login_required
    def post(self, location=None):
        with session_scope(self.config) as db_session:
            data = self.get_request_data()

            if not "location_id" in data and location:
                data["location_id"] = self.get_location_id(location, db_session)

            beer_id = data.get("beer_id")
            beverage_id = data.get("beverage_id")

            if beer_id and beverage_id:
                raise BeerOrBeverageOnlyError()

            tap = TapsDB.create(db_session, **data)

            return self.transform_response(tap, db_session=db_session)


class Tap(BaseResource, TapsResourceMixin):
    def get(self, tap_id, location=None):
        with session_scope(self.config) as db_session:
            tap = None
            if location:
                query = {"location_id": self.get_location_id(location, db_session), taps_pk: tap_id}
                res = TapsDB.query(db_session, **query)
                if res:
                    tap = res[0]
            else:
                tap = TapsDB.get_by_pkey(db_session, tap_id)

            if not tap:
                raise NotFoundError()

            return self.transform_response(tap, db_session=db_session)

    @login_required
    def patch(self, tap_id, location=None):
        with session_scope(self.config) as db_session:
            if location:
                query = {"location_id": self.get_location_id(location, db_session), taps_pk: tap_id}
                resp = TapsDB.query(db_session, **query)
                if resp:
                    tap = resp[0]
            else:
                tap = TapsDB.get_by_pkey(db_session, tap_id)

            if not tap:
                raise NotFoundError()

            data = self.get_request_data()

            beer_id = data.get("beer_id")
            beverage_id = data.get("beverage_id")

            if beer_id and beverage_id:
                raise BeerOrBeverageOnlyError()

            # if the beer or beverage id come in as empty string, then null them out
            if beer_id == "":
                data["beer_id"] = None
            if beverage_id == "":
                data["beverage_id"] = None

            tap = TapsDB.update(db_session, tap_id, **data)

            return self.transform_response(tap, db_session=db_session)

    @login_required
    def delete(self, tap_id, location=None):
        with session_scope(self.config) as db_session:
            if location:
                query = {"location_id": self.get_location_id(location, db_session), taps_pk: tap_id}
                resp = TapsDB.query(db_session, **query)
                if resp:
                    tap = resp[0]
            else:
                tap = TapsDB.get_by_pkey(db_session, tap_id)

            if not tap:
                raise NotFoundError()

            TapsDB.delete(db_session, tap_id)

            return True
