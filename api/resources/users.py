from uuid import uuid4

from flask import request
from flask_login import current_user, login_required

from db import session_scope
from db.users import Users as UsersDB
from db.user_locations import UserLocations as UserLocationsDB
from resources import BaseResource, ClientError, ForbiddenError, NotAuthorizedError, NotFoundError, ResourceMixinBase, requires_admin
from resources.locations import LocationsResourceMixin


class UserResourceMixin(ResourceMixinBase):
    def get_request_data(self, remove_key=None):
        if not remove_key:
            remove_key = []
        remove_key.append("password_hash")
        remove_key.append("id")

        return super().get_request_data(remove_key=remove_key)

    @staticmethod
    def transform_response(user):
        data = user.to_dict()
        FILTERED_KEYS = ["password_hash", "google_oidc_id"]

        user_c = current_user
        if not user_c.admin and user_c.id == user.id:
            FILTERED_KEYS.append("api_key")

        data["password_enabled"] = False
        if data.get("password_hash"):
            data["password_enabled"] = True

        for key in FILTERED_KEYS:
            if key in data:
                del data[key]
        
        locations = []
        if user.locations:
            locations = [LocationsResourceMixin.transform_response(d) for d in user.locations]
        data["locations"] = locations
        
        return ResourceMixinBase.transform_response(data)


class Users(BaseResource, UserResourceMixin):
    @login_required
    @requires_admin
    def get(self):
        with session_scope(self.config) as db_session:
            users = UsersDB.query(db_session)

            return [self.transform_response(u) for u in users]

    @login_required
    @requires_admin
    def post(self):
        data = self.get_request_data(remove_key=["id", "apiKey", "locations"])

        with session_scope(self.config) as db_session:
            self.logger.debug("Creating user with data: %s", data)
            user = UsersDB.create(db_session, **data)
            return self.transform_response(user)


class User(BaseResource, UserResourceMixin):
    @login_required
    @requires_admin
    def patch(self, user_id):
        user_c = current_user
        data = self.get_request_data(remove_key=["id", "apiKey", "locations"])

        if "password" in data and user_c.id != user_id:
            raise ForbiddenError("You are not authorized to change the password for another user.")

        with session_scope(self.config) as db_session:
            user = UsersDB.get_by_pkey(db_session, user_id)

            if not user:
                raise NotFoundError()

            if "password" in data and data["password"] is None:
                del data["password"]
                self.logger.debug("Disabling password for user '%s' (%s): %s", user.email, user_id)
                UsersDB.disable_password(db_session, user_id)

            self.logger.debug("Updating user '%s' (%s) with data: %s", user.email, user_id, data)
            user = UsersDB.update(db_session, user_id, **data)
            return self.transform_response(user)

    @login_required
    @requires_admin
    def delete(self, user_id):
        with session_scope(self.config) as db_session:
            user = UsersDB.get_by_pkey(db_session, user_id)

            if not user:
                raise NotFoundError()

            if user_id == current_user.id:
                raise ClientError("You cannot delete your own user")

            self.logger.debug("Deleting user '%s' (%s)", user.email, user_id)
            UsersDB.delete(db_session, user_id)
            return True

class UserLocations(BaseResource, UserResourceMixin):
    @login_required
    @requires_admin
    def get(self, user_id):
        with session_scope(self.config) as db_session:
            user = UsersDB.get_by_pkey(db_session, user_id)

            if not user or user.locations is None:
                raise NotFoundError()

            return [LocationsResourceMixin.transform_response(d) for d in user.locations]

    @login_required
    @requires_admin
    def post(self, user_id):
        data = self.get_request_data()

        with session_scope(self.config) as db_session:
            self.logger.debug("Deleting user locations for user id: %s", user_id)
            UserLocationsDB.delete_by(db_session, user_id=user_id)

            location_ids = data.get("location_ids")
            for location_id in location_ids:
                self.logger.debug("Creating user location %s for user id: %s", location_id, user_id)
                UserLocationsDB.create(db_session, user_id=user_id, location_id=location_id)

            return True

class CurrentUser(BaseResource, UserResourceMixin):
    def get(self):
        user_c = current_user
        if not user_c:
            raise NotAuthorizedError()

        if not user_c.is_authenticated:
            raise NotAuthorizedError()

        with session_scope(self.config) as db_session:
            user = UsersDB.get_by_pkey(db_session, user_c.id)
            return self.transform_response(user)

class UserAPIKey(BaseResource, UserResourceMixin):
    @login_required
    def get(self, user_id):
        with session_scope(self.config) as db_session:
            user = UsersDB.get_by_pkey(db_session, user_id)

            if not user:
                raise NotFoundError()

            if user_id != current_user.id and not current_user.admin:
                raise ClientError("You cannot access the API key for another users")

            return user.api_key

    @login_required
    def post(self, user_id):
        with session_scope(self.config) as db_session:
            user = UsersDB.get_by_pkey(db_session, user_id)

            if not user:
                raise NotFoundError()

            if user_id != current_user.id and not current_user.admin:
                raise ClientError("You cannot generate and API key for another users")

            allow_regen = request.args.get("regen")
            if user.api_key and (not allow_regen or allow_regen.lower() not in ["", "1", "true", "yes"]):
                raise ClientError("API key already exists")

            self.logger.debug("Generating API key for user '%s' (%s)", user.email, user_id)
            api_key = str(uuid4())
            UsersDB.update(db_session, user_id, api_key=api_key)
            return api_key

    @login_required
    def delete(self, user_id):
        with session_scope(self.config) as db_session:
            user = UsersDB.get_by_pkey(db_session, user_id)

            if not user:
                raise NotFoundError()

            if user_id != current_user.id and not current_user.admin:
                raise ClientError("You cannot delete another users API Key")

            self.logger.debug("Deleting user '%s' (%s)s api key", user.email, user_id)
            UsersDB.update(db_session, user_id, api_key=None)
            return True
