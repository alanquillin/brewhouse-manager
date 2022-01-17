
#from flask_connect import login_required

from resources import BaseResource, ResourceMixinBase
from db import session_scope
from db.locations import Locations as LocationsDB

class Locations(BaseResource, ResourceMixinBase):
    def get(self):
        with session_scope(self.config) as db_session:
            locations = LocationsDB.query(db_session)
            return [self.transform_response(l.to_dict()) for l in locations]

class Location(BaseResource, ResourceMixinBase):
    def get(self, location=None):
        with session_scope(self.config) as db_session:
            location_id = self.get_location_id(location, db_session)
            l = LocationsDB.get_by_pkey(db_session, location_id)
            return self.transform_response(l.to_dict())
