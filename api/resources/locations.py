import logging

from flask_login import login_required, current_user

from db import session_scope
from db.locations import Locations as LocationsDB
from resources import BaseResource, NotFoundError, ResourceMixinBase, requires_admin, NotAuthorizedError

LOGGER = logging.getLogger(__name__)


class LocationsResourceMixin(ResourceMixinBase):
    def get_request_data(self):
        return super().get_request_data(remove_key=["id"])

    @staticmethod
    def transform_response(location):
        data = location.to_dict()
        return ResourceMixinBase.transform_response(data)


class Locations(BaseResource, LocationsResourceMixin):
    @login_required
    def get(self):
        with session_scope(self.config) as db_session:
            kwargs = {}
            if not current_user.admin:
                kwargs["ids"] = current_user.locations
            locations = LocationsDB.query(db_session, **kwargs)
            return [self.transform_response(l) for l in locations]

    @login_required
    @requires_admin
    def post(self):
        with session_scope(self.config) as db_session:
            data = self.get_request_data()
            l = LocationsDB.create(db_session, **data)

            return self.transform_response(l)


class Location(BaseResource, LocationsResourceMixin):
    @login_required
    def get(self, location):
        with session_scope(self.config) as db_session:
            location_id = self.get_location_id(location, db_session)
            if not location_id:
                raise NotFoundError()
            l = LocationsDB.get_by_pkey(db_session, location_id)
            if not l:
                raise NotFoundError()
            if not current_user.admin and location_id not in current_user.locations:
                raise NotAuthorizedError()
            return self.transform_response(l)

    @login_required
    @requires_admin
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

            return self.transform_response(l)

    @login_required
    @requires_admin
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
