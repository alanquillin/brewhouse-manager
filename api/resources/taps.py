from flask_login import login_required, current_user

from db import session_scope
from db.taps import _PKEY as taps_pk
from db.taps import Taps as TapsDB
from resources import BaseResource, ClientError, NotFoundError, ResourceMixinBase, NotAuthorizedError
from resources.beers import BeerResourceMixin
from resources.beverage import BeverageResourceMixin
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
        
        if tap.beverage:
            data["beverage"] = BeverageResourceMixin.transform_response(tap.beverage)

        if tap.location:
            data["location"] = LocationsResourceMixin.transform_response(tap.location)

        if tap.sensor:
            data["sensor"] = SensorResourceMixin.transform_response(tap.sensor)

        return data


class Taps(BaseResource, TapsResourceMixin):
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
            
            taps = TapsDB.query(db_session, **kwargs)
            return [self.transform_response(t, db_session=db_session) for t in taps]

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
            beverage_id = data.get("beverage_id")

            if beer_id and beverage_id:
                raise BeerOrBeverageOnlyError()

            tap = TapsDB.create(db_session, **data)

            return self.transform_response(tap, db_session=db_session)


class Tap(BaseResource, TapsResourceMixin):
    def _get_tap(self, db_session, tap_id, location=None):
        kwargs = {taps_pk: tap_id}
        if location:
            location_id = self.get_location_id(location, db_session)
            if not current_user.admin and not location_id in current_user.locations:
                raise NotAuthorizedError()
            kwargs["locations"] = [location_id]
        tap = TapsDB.query(db_session, **kwargs)

        if not tap:
            raise NotFoundError()

        tap = tap[0]
            
        if not current_user.admin and not tap.location_id in current_user.locations:
            raise NotAuthorizedError()
        return tap

    @login_required
    def get(self, tap_id, location=None):
        with session_scope(self.config) as db_session:
            tap = self._get_tap(db_session, tap_id, location=location)

            return self.transform_response(tap, db_session=db_session)

    @login_required
    def patch(self, tap_id, location=None):
        with session_scope(self.config) as db_session:
            tap = self._get_tap(db_session, tap_id, location=location)

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

            tap = TapsDB.update(db_session, tap.id, **data)

            return self.transform_response(tap, db_session=db_session)

    @login_required
    def delete(self, tap_id, location=None):
        with session_scope(self.config) as db_session:
            tap = self._get_tap(db_session, tap_id, location=location)

            TapsDB.delete(db_session, tap.id)

            return True
