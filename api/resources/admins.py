from flask import request
from flask_login import login_required, current_user

from resources import BaseResource, ResourceMixinBase, generate_filtered_keys, NotFoundError, ForbiddenError
from db import session_scope
from db.admins import Admins as AdminsDB
from lib.external_brew_tools import get_tool as get_external_brewing_tool


class AdminResourceMixin(ResourceMixinBase):
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

class Admins(BaseResource, AdminResourceMixin):
    @login_required
    def get(self):
        with session_scope(self.config) as db_session:
            admins = AdminsDB.query(db_session)

            return [self.transform_response(a.to_dict() for a in admins)]

    @login_required
    def post(self):
        user_c = current_user
        data = self.get_request_data("password_hash")

        with session_scope(self.config) as db_session:
            self.logger.debug("Creating admin with data: %s", data)
            admin = AdminsDB.create(db_session, **data)
            return self.transform_response(admin.to_dict())

class Admin(BaseResource, AdminResourceMixin):
    @login_required
    def patch(self, admin_id):
        user_c = current_user
        data = self.get_request_data()

        if "password" in data and user_c.id != admin_id:
            raise ForbiddenError("You are not authorized to change the password for another admin.")

        with session_scope(self.config) as db_session:
            admin = AdminsDB.get_by_pkey(db_session, admin_id)

            if not admin:
                raise NotFoundError()

            if "password" in data and data["password"] is None:
                del data["password"]
                self.logger.debug("Disabling password for admin '%s' (%s): %s", admin.email, admin_id)
                AdminsDB.disable_password(db_session, admin_id)

            self.logger.debug("Updating admin '%s' (%s) with data: %s", admin.email, admin_id, data)
            admin = AdminsDB.update(db_session, admin_id, **data)
            return self.transform_response(admin.to_dict())

    @login_required
    def delete(self, admin_id):
        with session_scope(self.config) as db_session:
            admin = AdminsDB.get_by_pkey(db_session, admin_id)

            if not admin:
                raise NotFoundError()

            self.logger.debug("Deleting admin '%s' (%s)", admin.email, admin_id)
            AdminsDB.delete(db_session, admin_id)
            return True


class CurrentUser(BaseResource, AdminResourceMixin):
    @login_required
    def get(self):
        user_c = current_user

        with session_scope(self.config) as db_session:
            admin = AdminsDB.get_by_pkey(db_session, user_c.id)
            return self.transform_response(admin.to_dict())