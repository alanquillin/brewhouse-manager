from flask import request
from flask_login import login_required, current_user

from resources import BaseResource, ResourceMixinBase, NotFoundError, ForbiddenError, ClientError
from db import session_scope
from db.users import Users as UsersDB
from lib.external_brew_tools import get_tool as get_external_brewing_tool


class UserResourceMixin(ResourceMixinBase):
    def get_request_data(self):
        return super().get_request_data(remove_key=["password_hash", "id"])

    def transform_response(self, entity):
        FILTERED_KEYS = ["password_hash", "google_oidc_id"]
        
        entity["password_enabled"] = False
        if entity.get("password_hash"):
            entity["password_enabled"] = True

        for key in FILTERED_KEYS:
            if key in entity:
                del entity[key]

        return super().transform_response(entity)

class Users(BaseResource, UserResourceMixin):
    @login_required
    def get(self):
        with session_scope(self.config) as db_session:
            users = UsersDB.query(db_session)

            return [self.transform_response(a.to_dict() for a in users)]

    @login_required
    def post(self):
        user_c = current_user
        data = self.get_request_data("password_hash")

        with session_scope(self.config) as db_session:
            self.logger.debug("Creating user with data: %s", data)
            user = UsersDB.create(db_session, **data)
            return self.transform_response(user.to_dict())

class User(BaseResource, UserResourceMixin):
    @login_required
    def patch(self, user_id):
        user_c = current_user
        data = self.get_request_data()

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
            return self.transform_response(user.to_dict())

    @login_required
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


class CurrentUser(BaseResource, UserResourceMixin):
    @login_required
    def get(self):
        user_c = current_user

        with session_scope(self.config) as db_session:
            user = UsersDB.get_by_pkey(db_session, user_c.id)
            return self.transform_response(user.to_dict())