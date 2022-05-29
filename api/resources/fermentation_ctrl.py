from datetime import datetime, timezone

from flask import request
from flask_login import login_required
from flask_restful import reqparse

from db import session_scope
from db.fermentation_ctrl import FermentationController as FermentationControllerDB
from db.fermentation_ctrl_stats import FermentationControllerStats as FermentationControllerStatsDB
from lib import devices as devicesLib
from resources import BaseResource, ClientError, NotFoundError, ResourceMixinBase


class FermentationControllerResourceMixin(ResourceMixinBase):
    def __init__(self):
        super().__init__()

    def get_status(self, device):
        status = "unsupported"
        if devicesLib.supports_status_check(device):
            status = devicesLib.ping(device)
        return status

    def transform_response(self, device, include_status=False, **kwargs):
        data = device.to_dict()

        data["supports_status_check"] = devicesLib.supports_status_check(device)

        include_status = request.args.get("include_status", "false").lower() in ["true", "yes", "", "1"]
        if include_status:
            data["status"] = self.get_status(device)

        include_extended_details = request.args.get("include_extended_details", "false").lower() in ["true", "yes", "", "1"]
        if include_extended_details:
            extended_details = devicesLib.get_details(device)
            if extended_details:
                data["extended_details"] = extended_details

        return super().transform_response(data, **kwargs)

    def clean_program(self, program):
        return program.lower().replace(" ", "_").replace("-", "_")

    def is_program_valid(program):
        return program in ["off", "normal", "cool_only", "heat_only"]


class FermentationControllers(BaseResource, FermentationControllerResourceMixin):
    def __init__(self):
        super().__init__()

    def get(self):
        with session_scope(self.config) as db_session:
            qs = request.args.to_dict()
            self.logger.debug("query params: %s", qs)

            search = {}

            def _get_search_params(_key):
                _val = qs.get(_key)
                if _val:
                    search[_key] = _val

            for k in ["manufacturer", "manufacturer_id", "model"]:
                _get_search_params(k)

            if search:
                self.logger.debug("searching for devices with: %s", search)
            devices = FermentationControllerDB.query(db_session, **search)
            return [self.transform_response(d) for d in devices]

    def post(self):
        with session_scope(self.config) as db_session:
            data = self.get_request_data()

            self.logger.debug("Data: %s", data)

            # TODO: Check for logged in user, and if no user is logged in, then make sure the device belongs to expected particle account.

            self.logger.debug("Creating device with: %s", data)
            device = FermentationControllerDB.create(db_session, **data)

            if "description" not in data:
                self.logger.debug("no name/description provided... attempting to retrieve it...")
                description = devicesLib.get_description(device)

                if description:
                    self.logger.debug("Yay!  Name/description was able to be retrieved for device %s, updating DB.  value= %s", device.id, description)
                    device = FermentationControllerDB.update(db_session, device.id, description=description)
                else:
                    self.logger.debug(":( unable to retrieve name/descritpion for device %s", device.id)

            return self.transform_response(device)


class FermentationController(BaseResource, FermentationControllerResourceMixin):
    def __init__(self):
        super().__init__()

    def get(self, fermentation_controller_id):
        with session_scope(self.config) as db_session:
            device = FermentationControllerDB.get_by_pkey(db_session, fermentation_controller_id)

            return self.transform_response(device)

    def patch(self, fermentation_controller_id):
        with session_scope(self.config) as db_session:
            data = self.get_request_data()
            qs = request.args.to_dict()

            self.logger.debug("Data: %s", data)

            # TODO: Check for logged in user, and if no user is logged in, then make sure the device belongs to expected particle account.

            if data.get("id"):
                data.pop("id")

            if data.get("program"):
                program = self.clean_program(data.get("program"))
                if not self.is_program_valid(program):
                    raise ClientError(user_msg="invalid program.  Must be one of: off, normal, cool_only, heat_only")
                data["program"] = program

            self.logger.debug("Updating device %s with: %s", fermentation_controller_id, data)
            FermentationControllerDB.update(db_session, fermentation_controller_id, **data)
            device = FermentationControllerDB.get_by_pkey(db_session, fermentation_controller_id)

            if qs.get("source", "").lower() != "device":
                devicesLib.refresh_config(device)

            return self.transform_response(device)

    @login_required
    def delete(self, fermentation_controller_id):
        with session_scope(self.config) as db_session:
            FermentationControllerDB.delete(db_session, fermentation_controller_id)

            return


class FermentationControllerDeviceActions(BaseResource, FermentationControllerResourceMixin):
    def __init__(self):
        super().__init__()

    def post(self, fermentation_controller_id, action=None, value=None):
        if not action and not value:
            data = self.get_request_data()
            action = data.get("action")
            value = data.get("data")

        if action in ["program", "target_temp"]:
            action = f"set_{action}"

        if action == "target_temperature":
            action = "set_target_temp"

        with session_scope(self.config) as db_session:
            device = FermentationControllerDB.get_by_pkey(db_session, fermentation_controller_id)
            if not device:
                raise NotFoundError(user_msg="Device not found")

            if action == "set_program":
                if not value:
                    raise ClientError(user_msg="a value is required to up update the program but was not provided")
                value = self.clean_program(value)
                if not self.is_program_valid(value):
                    raise ClientError(user_msg="invalid program.  Must be one of: off, normal, cool_only, heat_only")
                FermentationControllerDB.update(db_session, fermentation_controller_id, program=value)

            if action == "set_target_temp":
                if not value:
                    raise ClientError(user_msg="a value is required to up update the target temperature but was not provided")
                try:
                    value = float(value)
                except ValueError:
                    raise ClientError(user_msg=f"Invalid temperature value '{value}'.")
                FermentationControllerDB.update(db_session, fermentation_controller_id, target_temperature=float(value))

            args = ()
            if value:
                args = args + (value,)
            self.logger.debug("Executing device action %s with data: %s", action, args)
            return devicesLib.run(device, action, *args)


class FermentationControllerDeviceData(BaseResource, FermentationControllerResourceMixin):
    def __init__(self):
        super().__init__()

    def get(self, fermentation_controller_id, key):
        with session_scope(self.config) as db_session:
            device = FermentationControllerDB.get_by_pkey(db_session, fermentation_controller_id)
            if not device:
                raise NotFoundError(user_msg="Device not found")

            self.logger.debug("Retrieving device data for key: %s", key)
            return devicesLib.get(device, key)


class FermentationControllerStatsResourceMixin(ResourceMixinBase):
    def __init__(self):
        super().__init__()

    def transform_response(self, stat, **kwargs):
        data = stat.to_dict()

        return super().transform_response(data, **kwargs)


class FermentationControllerStats(BaseResource, FermentationControllerStatsResourceMixin):
    def __init__(self):
        super().__init__()

    def get(self, fermentation_controller_id):
        with session_scope(self.config) as db_session:
            stats = FermentationControllerStatsDB.get_by_fermentation_controller_id(db_session, fermentation_controller_id)

            return [self.transform_response(s) for s in stats]

    def post(self, fermentation_controller_id):
        with session_scope(self.config) as db_session:
            data = request.get_json()

            self.logger.debug("Data: %s", data)

            if not isinstance(data, list):
                data = [data]

            for d in data:
                if d.get("t"):
                    d["temperature"] = d.pop("t")

                if d.get("ts"):
                    timestamp = d.pop("ts")
                    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                    d["event_time"] = dt

                self.logger.debug("Inserting stats for device %s with: %s", fermentation_controller_id, d)
                d["fermentation_controller_id"] = fermentation_controller_id
                FermentationControllerStatsDB.create(db_session, **d)

            return True
