import logging

from db import session_scope, audit_column_names
from db.locations import Locations as LocationsDB
from db.taps import Taps as TapsDB
from db.beers import Beers as BeersDB
from db.beverages import Beverages as BeveragesDB
from db.sensors import Sensors as SensorsDB
from resources import BaseResource, ResourceMixinBase, NotFoundError
from resources.locations import LocationsResourceMixin
from resources.taps import TapsResourceMixin
from resources.beers import BeerResourceMixin
from resources.beverage import BeverageResourceMixin
from resources.sensors import SensorResourceMixin

LOGGER = logging.getLogger(__name__)


class DashboardResourceMixin(ResourceMixinBase):
    @staticmethod
    def transform_response(data):
        if isinstance(data, list):
            return [DashboardResourceMixin.transform_response(l) for l in data]

        if getattr(data, "to_dict", None):
            data = data.to_dict()

        return ResourceMixinBase.transform_response(data, remove_keys=audit_column_names)


class DashboardLocations(BaseResource, DashboardResourceMixin):
    def get(self):
        with session_scope(self.config) as db_session:
            locations = LocationsDB.query(db_session)
            return self.transform_response([LocationsResourceMixin.transform_response(l) for l in locations])

class DashboardTap(BaseResource, DashboardResourceMixin):
    def get(self, tap_id):
        with session_scope(self.config) as db_session:
            tap = TapsDB.get_by_pkey(db_session, tap_id)

            if not tap:
                raise NotFoundError()

            return self.transform_response(TapsResourceMixin.transform_response(tap))

class DashboardBeer(BaseResource, DashboardResourceMixin):
    def get(self, beer_id):
        with session_scope(self.config) as db_session:
            beer = BeersDB.get_by_pkey(db_session, beer_id)

            if not beer:
                raise NotFoundError()

            return self.transform_response(BeerResourceMixin.transform_response(beer))

class DashboardBeverage(BaseResource, DashboardResourceMixin):
    def get(self, beverage_id):
        with session_scope(self.config) as db_session:
            beverage = BeveragesDB.get_by_pkey(db_session, beverage_id)

            if not beverage:
                raise NotFoundError()

            return self.transform_response(BeverageResourceMixin.transform_response(beverage))

class DashboardSensor(BaseResource, DashboardResourceMixin):
    def get(self, sensor_id):
        with session_scope(self.config) as db_session:
            sensor = SensorsDB.get_by_pkey(db_session, sensor_id)

            if not sensor:
                raise NotFoundError()

            return self.transform_response(SensorResourceMixin.transform_response(sensor))


class Dashboard(BaseResource, DashboardResourceMixin):
    def get(self, location_id):
        with session_scope(self.config) as db_session:
            locations = LocationsDB.query(db_session)
            location_id = self.get_location_id(location_id, db_session)
            taps = TapsDB.get_by_location(db_session, location_id)

            location = None
            for l in locations:
                if l.id == location_id:
                    location = l
            
            if not locations:
                location = LocationsDB.get_by_pkey(db_session, location_id)

            return self.transform_response({
                "taps": [TapsResourceMixin.transform_response(t, db_session=db_session) for t in taps], 
                "locations": [LocationsResourceMixin.transform_response(l) for l in locations],
                "location": LocationsResourceMixin.transform_response(location)
            })