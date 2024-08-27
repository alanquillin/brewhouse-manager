#! /usr/bin/env python3

# pylint: disable=wrong-import-position
if __name__ == "__main__":
    from gevent import monkey  # isort:skip

    monkey.patch_all()

    from psycogreen.gevent import patch_psycopg  # isort:skip

    patch_psycopg()

import argparse
import base64
import json as official_json
import os
import sys
import uuid
from datetime import timedelta

from flask import Flask, make_response, redirect, send_from_directory
from flask.logging import create_logger
from flask_cors import CORS
from flask_login import LoginManager
from flask_restful import Api
from gevent.pywsgi import LoggingLogAdapter, WSGIServer  # pylint:disable=ungrouped-imports
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.wrappers.base_response import BaseResponse

from db import session_scope
from db.users import Users as UsersDB
from lib import json, logging
from lib.config import Config
from resources.assets import UploadImage
from resources.auth import AuthUser, GoogleCallback, GoogleLogin, Login, Logout
from resources.batches import Batch, Batches
from resources.beers import Beer, Beers
from resources.beverage import Beverage, Beverages
from resources.external_brew_tools import ExternalBrewTool, ExternalBrewToolTypes, SearchExternalBrewTool
from resources.fermentation_ctrl import (
    FermentationController,
    FermentationControllerDeviceActions,
    FermentationControllerDeviceData,
    FermentationControllers,
    FermentationControllerStats,
)
from resources.image_transitions import ImageTransition
from resources.locations import Location, Locations
from resources.pages import GenericPageHandler, RestrictedGenericPageHandler, AdminRestrictedGenericPageHandler
from resources.sensors import Sensor, SensorData, Sensors, SensorTypes
from resources.settings import Settings
from resources.taps import Tap, Taps
from resources.users import CurrentUser, User, Users, UserAPIKey, UserLocations
from resources.dashboard import Dashboard, DashboardBeer, DashboardBeverage, DashboardLocations, DashboardTap, DashboardSensor


class IgnoringLogAdapter(LoggingLogAdapter):
    """
    Do not let k8s spam the logs:
    """

    IGNORED_LOGS = ['"GET /health HTTP/1.1" 200']

    def write(self, msg):
        for i in self.IGNORED_LOGS:
            if i in msg:
                return
        super().write(msg)


STATIC_URL_PATH = "static"

CONFIG = Config()

# Disable Location header autocorrect which prepends the HOST to the Location
BaseResponse.autocorrect_location_header = False

app = Flask(__name__)
api = Api(app)

app.json_encoder = json.CloudCommonJsonEncoder


@api.representation("application/json")
def _json(data, code, headers=None):
    resp = make_response(json.dumps(data), code)
    resp.headers.extend(headers or {})
    return resp


# Monkey-patch because there is apparently  yet another path to serialize responses in addition the the above
official_json.dumps = json.dumps


app_config = CONFIG
app_config.setup(config_files=["default.json"])

LOGGER = logging.getLogger(__name__)


@app.route("/health")
def health():
    return {"healthy": True}


login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    with session_scope(CONFIG) as db_session:
        print("refreshing user %s" % user_id)
        return AuthUser.from_user(UsersDB.get_by_pkey(db_session, user_id))


@login_manager.unauthorized_handler
def redirect_not_logged_in():
    return redirect("/login")


# API resources for UI:
api.add_resource(Beers, "/api/v1/beers", "/api/v1/locations/<location>/beers")
api.add_resource(Beer, "/api/v1/beers/<beer_id>", "/api/v1/locations/<location>/beers/<beer_id>")
api.add_resource(Beverages, "/api/v1/beverages", "/api/v1/locations/<location>/beverages")
api.add_resource(Beverage, "/api/v1/beverages/<beverage_id>", "/api/v1/locations/<location>/beverages/<beer_id>")
api.add_resource(Batches, "/api/v1/batches", "/api/v1/locations/<location>/beers/<beer_id>/batches", "/api/v1/locations/<location>/beverages/<beverage_id>/batches")
api.add_resource(Batch, "/api/v1/batches/<batch_id>", "/api/v1/locations/<location>/beers/<beer_id>/batches/<batch_id>", "/api/v1/locations/<location>/beverages/<beverage_id>/batches/<batch_id>")
api.add_resource(Locations, "/api/v1/locations")
api.add_resource(Location, "/api/v1/locations/<location>")
api.add_resource(Taps, "/api/v1/taps", "/api/v1/locations/<location>/taps")
api.add_resource(Tap, "/api/v1/taps/<tap_id>", "/api/v1/locations/<location>/taps/<tap_id>")
api.add_resource(Sensors, "/api/v1/sensors", "/api/v1/locations/<location>/sensors")
api.add_resource(Sensor, "/api/v1/sensors/<sensor_id>", "/api/v1/locations/<location>/sensors/<sensor_id>")
api.add_resource(SensorData, "/api/v1/sensors/<sensor_id>/<data_type>", "/api/v1/locations/<location>/sensors/<sensor_id>/<data_type>")
api.add_resource(SensorTypes, "/api/v1/sensors/types")
api.add_resource(ExternalBrewToolTypes, "/api/v1/external_brew_tools/types")
api.add_resource(ExternalBrewTool, "/api/v1/external_brew_tools/<tool_name>")
api.add_resource(SearchExternalBrewTool, "/api/v1/external_brew_tools/<tool_name>/search")
api.add_resource(Users, "/api/v1/users")
api.add_resource(User, "/api/v1/users/<user_id>")
api.add_resource(UserLocations, "/api/v1/users/<user_id>/locations")
api.add_resource(UserAPIKey, "/api/v1/users/<user_id>/api_key", endpoint="delete_user_api_key", methods=["GET", "DELETE"])
api.add_resource(UserAPIKey, "/api/v1/users/<user_id>/api_key/generate", endpoint="gen_user_api_key", methods=["POST"])
api.add_resource(CurrentUser, "/api/v1/users/current")
api.add_resource(Settings, "/api/v1/settings")
api.add_resource(UploadImage, "/api/v1/uploads/images/<image_type>")
api.add_resource(FermentationControllers, "/api/v1/fermentation/controllers", endpoint="fermentation_controllers")
api.add_resource(FermentationControllers, "/api/v1/fermentation/controllers/find", endpoint="find_fermentation_controllers", methods=["GET"])
api.add_resource(FermentationController, "/api/v1/fermentation/controllers/<fermentation_controller_id>")
api.add_resource(FermentationControllerStats, "/api/v1/fermentation/controllers/<fermentation_controller_id>/stats")
api.add_resource(
    FermentationControllerDeviceActions,
    "/api/v1/fermentation/controllers/<fermentation_controller_id>/actions",
    endpoint="fermentation_controllers_action_rpc",
    methods=["POST"],
)
api.add_resource(
    FermentationControllerDeviceActions,
    "/api/v1/fermentation/controllers/<fermentation_controller_id>/<action>",
    endpoint="fermentation_controllers_valueless_action",
    methods=["POST"],
)
api.add_resource(FermentationControllerDeviceActions, "/api/v1/fermentation/controllers/<fermentation_controller_id>/<action>/<value>", methods=["POST"])
api.add_resource(FermentationControllerDeviceData, "/api/v1/fermentation/controllers/<fermentation_controller_id>/<key>", methods=["GET"])
api.add_resource(ImageTransition, "/api/v1/image_transitions/<image_transition_id>", methods=["DELETE"])
api.add_resource(Dashboard, "/api/v1/dashboard/locations/<location_id>")
api.add_resource(DashboardLocations, "/api/v1/dashboard/locations")
api.add_resource(DashboardBeer, "/api/v1/dashboard/beers/<beer_id>")
api.add_resource(DashboardBeverage, "/api/v1/dashboard/beverages/<beverage_id>")
api.add_resource(DashboardTap, "/api/v1/dashboard/taps/<tap_id>")
api.add_resource(DashboardSensor, "/api/v1/dashboard/sensors/<sensor_id>")

# session management APIs
api.add_resource(GoogleLogin, "/login/google")
api.add_resource(GoogleCallback, "/login/google/callback")
api.add_resource(Logout, "/logout")
api.add_resource(Login, "/login", endpoint="submit_login", methods=["POST"])
api.add_resource(GenericPageHandler, "/login", endpoint="display_login", methods=["GET"])
api.add_resource(GenericPageHandler, "/", endpoint="home")
api.add_resource(GenericPageHandler, "/view/<location>", endpoint="location_view")

# UI resources
api.add_resource(RestrictedGenericPageHandler, "/manage", endpoint="management_dashboard")
api.add_resource(RestrictedGenericPageHandler, "/manage/beers", endpoint="manage_beers")
api.add_resource(RestrictedGenericPageHandler, "/manage/beverages", endpoint="manage_beverages")
api.add_resource(AdminRestrictedGenericPageHandler, "/manage/locations", endpoint="manage_locations")
api.add_resource(RestrictedGenericPageHandler, "/manage/sensors", endpoint="manage_sensors")
api.add_resource(RestrictedGenericPageHandler, "/manage/taps", endpoint="manage_taps")
api.add_resource(AdminRestrictedGenericPageHandler, "/manage/users", endpoint="manage_users")
api.add_resource(RestrictedGenericPageHandler, "/me", endpoint="profile")
api.add_resource(GenericPageHandler, "/tools/volume_calculator", endpoint="volume_calculator")

app.wsgi_app = ProxyFix(app.wsgi_app)
app.secret_key = CONFIG.get("app.secret_key", str(uuid.uuid4()))

app.config.update(
    {
        "app_config": app_config,
        "SESSION_COOKIE_SECURE": app_config.get("secure_cookies", True),
        "SESSION_COOKIE_HTTPONLY": True,
        "SESSION_COOKIE_SAMESITE": "Lax",
    }
)
port = app_config.get("api.port")

# serve static content:
@app.route("/404")
@app.route("/<path:path>")
@app.route("/error")
def index(path="index.html", **_):
    dir_path = os.path.join(os.getcwd(), STATIC_URL_PATH)
    return send_from_directory(dir_path, path)


@app.errorhandler(404)
def send_404(_):
    return index(), 404

@login_manager.request_loader
def load_user_from_request(request):

    # first, try to login using the api_key url arg
    api_key = request.args.get('api_key')

    if not api_key:
        # next, try to login using Basic Auth
        api_key = request.headers.get('Authorization')
        if api_key:
            api_key = api_key.replace('Bearer ', '', 1).strip()
            try:
                api_key = base64.b64decode(api_key).decode('ascii')
            except TypeError as e:
                pass

    if api_key:
        with session_scope(app_config) as db_session:
            user = UsersDB.get_by_api_key(db_session, api_key)
            if user:
                return AuthUser.from_user(user)

    # finally, return None if both methods did not login the user
    return None


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    # parse logging level arg:
    parser.add_argument(
        "-l",
        "--log",
        dest="loglevel",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default=os.environ.get("LOG_LEVEL", "INFO").upper(),
        help="Set the logging level",
    )
    args = parser.parse_args()
    log_level = getattr(logging, args.loglevel)

    logging.init(fmt=logging.DEFAULT_LOG_FMT)

    logger = create_logger(app)

    if app.config.get("ENV") == "development":
        logger.debug("Setting up development environment")
        CORS(app)
    else:
        CORS(
            app,
            resources={
                "/user": {
                    "origins": app_config.get("api.registration_allow_origins"),
                    "methods": ["PUT", "OPTIONS"],
                }
            },
            expose_headers=["Content-Type"],
            max_age=3000,
            vary_header=True,
        )

    with session_scope(app_config) as db_session:
        users = UsersDB.query(db_session)

        if not users:
            init_user_email = app_config.get("auth.initial_user.email")
            set_init_user_pass = app_config.get("auth.initial_user.set_password")
            init_user_fname = app_config.get("auth.initial_user.first_name")
            init_user_lname = app_config.get("auth.initial_user.last_name")
            google_sso_enabled = app_config.get("auth.oidc.google.enabled")

            if not google_sso_enabled and not set_init_user_pass:
                logger.error("Can create an initial user!  auth.initial_user.set_pass and google authentication is disabled!")
                sys.exit(1)

            data = {"email": init_user_email, "admin": True}
            if init_user_fname:
                data["first_name"] = init_user_fname
            if init_user_lname:
                data["last_name"] = init_user_lname

            logger.info("No users exist, creating initial user: %s", data)
            if set_init_user_pass:
                data["password"] = app_config.get("auth.initial_user.password")
                logger.warning("Creating initial user with password: %s", data["password"])
                logger.warning("PLEASE REMEMBER TO LOG IN AND CHANGE IT ASAP!!")
            UsersDB.create(db_session, **data)

    http_server = WSGIServer(("", port), app, log=IgnoringLogAdapter(app.logger, log_level))
    logger.debug("app.config: %s", app.config)
    logger.debug("config: %s", app_config.data_flat)
    logger.info("Serving on port %s", port)

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        logger.info("User interrupted - Goodbye")
        sys.exit()
