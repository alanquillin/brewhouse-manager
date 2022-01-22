from flask_login import login_required

from resources import BaseResource, ResourceMixinBase, NotFoundError
from db import session_scope
from db.locations import Locations as LocationsDB

class LocationsResourceMixin(ResourceMixinBase):
    def get_request_data(self):
        return super().get_request_data(remove_key=["id"])

class Locations(BaseResource, LocationsResourceMixin):
    def get(self):
        with session_scope(self.config) as db_session:
            locations = LocationsDB.query(db_session)
            return [self.transform_response(l.to_dict()) for l in locations]

    @login_required
    def post(self):
        with session_scope(self.config) as db_session:
            data = self.get_request_data()
            l = LocationsDB.create(db_session, **data)
            
            return self.transform_response(l.to_dict())


class Location(BaseResource, LocationsResourceMixin):
    def get(self, location):
        with session_scope(self.config) as db_session:
            location_id = self.get_location_id(location, db_session)
            if not location_id:
                raise NotFoundError()
            l = LocationsDB.get_by_pkey(db_session, location_id)
            if not l:
                raise NotFoundError()
            return self.transform_response(l.to_dict())

    @login_required
    def patch(self, location):
        with session_scope(self.config) as db_session:
            location_id = self.get_location_id(location, db_session)
            if not location_id:
                raise NotFoundError()
            l = LocationsDB.get_by_pkey(db_session, location_id)
            if not l:
                raise NotFoundError()
            
            data = self.get_request_data()
            l = LocationsDB.update(db_session, location_id, **data)
            
            return self.transform_response(l.to_dict())
    
    @login_required
    def delete(self, location):
        with session_scope(self.config) as db_session:
            location_id = self.get_location_id(location, db_session)
            if not location_id:
                raise NotFoundError()
            l = LocationsDB.get_by_pkey(db_session, location_id)
            if not l:
                raise NotFoundError()
            
            LocationsDB.delete(db_session, location_id)
            
            return True
