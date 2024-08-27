from flask_login import login_required, current_user
from datetime import datetime

from db import session_scope
from db.taps import _PKEY as taps_pk
from db.taps import Taps as TapsDB
from db.on_tap import OnTap as OnTapDB
from db.batches import Batches as BatchesDB
from resources import BaseResource, ClientError, NotFoundError, ResourceMixinBase, NotAuthorizedError
from resources.batches import BatchesResourceMixin
from resources.beers import BeerResourceMixin
from resources.beverage import BeverageResourceMixin
from resources.locations import LocationsResourceMixin
from resources.sensors import SensorResourceMixin


class TapsResourceMixin(ResourceMixinBase):
    @staticmethod
    def transform_response(tap, db_session=None):
        data = tap.to_dict()

        if tap.on_tap:
            data["batch"] = BatchesResourceMixin.transform_response(tap.on_tap.batch, db_session=db_session)
            data["batch_id"] = tap.on_tap.batch_id

            if tap.on_tap.batch.beer:
                data["beer"] = BeerResourceMixin.transform_response(tap.on_tap.batch.beer, include_batches=False, include_location=False, db_session=db_session)
                data["beer_id"] = tap.on_tap.batch.beer_id

            if tap.on_tap.batch.beverage:
                data["beverage"] = BeverageResourceMixin.transform_response(tap.on_tap.batch.beverage, include_batches=False, include_location=False, db_session=db_session)
                data["beverage_id"] = tap.on_tap.batch.beverage_id

        if tap.location:
            data["location"] = LocationsResourceMixin.transform_response(tap.location)

        if tap.sensor:
            data["sensor"] = SensorResourceMixin.transform_response(tap.sensor, include_location=False)

        return ResourceMixinBase.transform_response(data, remove_keys=["on_tap_id"])


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

            batch_id = data.get("batch_id")
            if batch_id == "":
                batch_id = None
            
            if batch_id:
                batch = BatchesDB.get_by_pkey(db_session, batch_id)
                on_tap = OnTapDB.create(db_session, beer_id=batch.beer_id, beverage_id=batch.beverage_id, tapped_on=datetime.utcnow())
                data["on_tap_id"] = on_tap.id

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

            current_batch_id = None
            if tap.on_tap:
                current_batch_id = tap.on_tap.batch_id
            
            data = self.get_request_data()

            batch_id = data.pop("batch_id", current_batch_id)
            if batch_id == "":
                batch_id = None

            # if the beer or beverage id come in as empty string, then null them out
            if batch_id != current_batch_id:
                if tap.on_tap_id:
                    OnTapDB.update(db_session, tap.on_tap_id, untapped_on=datetime.utcnow())
                
                data["on_tap_id"] = None
                
                if batch_id:
                    batch = BatchesDB.get_by_pkey(db_session, batch_id)
                    on_tap = OnTapDB.create(db_session, beer_id=batch.beer_id, beverage_id=batch.beverage_id, tapped_on=datetime.utcnow())
                    data["on_tap_id"] = on_tap.id

            tap = TapsDB.update(db_session, tap.id, **data)

            return self.transform_response(tap, db_session=db_session)

    @login_required
    def delete(self, tap_id, location=None):
        with session_scope(self.config) as db_session:
            tap = self._get_tap(db_session, tap_id, location=location)

            TapsDB.delete(db_session, tap.id)

            return True
