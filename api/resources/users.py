from flask import request
from flask_login import login_required, current_user

from resources import BaseResource, ResourceMixinBase, NotFoundError, ForbiddenError, ClientError
from db import session_scope
from db.users import Users as UsersDB
from lib.external_brew_tools import get_tool as get_external_brewing_tool


class UserResourceMixin(ResourceMixinBase):
    def get_request_data(self):
        return super().get_request_data(remove_key=["password_hash", "id"])

    @staticmethod
    def transform_response(user):
        data = user.to_dict()
        FILTERED_KEYS = ["password_hash", "google_oidc_id"]
        
        data["password_enabled"] = False
        if data.get("password_hash"):
            data["password_enabled"] = True

        for key in FILTERED_KEYS:
            if key in data:
                del data[key]

        return ResourceMixinBase.transform_response(data)

class Users(BaseResource, UserResourceMixin):
    @login_required
    def get(self):
        with session_scope(self.config) as db_session:
            users = UsersDB.query(db_session)

            return [self.transform_response(u) for u in users]

    @login_required
    def post(self):
        data = self.get_request_data()

        with session_scope(self.config) as db_session:
            self.logger.debug("Creating user with data: %s", data)
            user = UsersDB.create(db_session, **data)
            return self.transform_response(user)

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
            return self.transform_response(user)

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
            return self.transform_response(user)