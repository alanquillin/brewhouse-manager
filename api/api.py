#! /usr/bin/env python3

# pylint: disable=wrong-import-position
if __name__ == "__main__":
    from gevent import monkey  # isort:skip

    monkey.patch_all()

    from psycogreen.gevent import patch_psycopg  # isort:skip

    patch_psycopg()

import argparse
import json as official_json
import uuid
from datetime import timedelta
from urllib.parse import urljoin
import os

from flask import Flask, make_response, send_from_directory
from flask.logging import create_logger
from flask_cors import CORS
from flask_restful import Api
from gevent.pywsgi import LoggingLogAdapter, WSGIServer  # pylint:disable=ungrouped-imports
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.wrappers.base_response import BaseResponse

from lib.config import Config
from lib import json, logging
from resources.beers import Beers, Beer
from resources.locations import Location, Locations
from resources.taps import Tap, Taps
from resources.sensors import Sensor, Sensors, SensorData
from resources.external_brew_tools import ExternalBrewTool, ExternalBrewToolTypes, SearchExternalBrewTool


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


app_config = Config()
app_config.setup(config_files=["default.json"])


@app.route("/health")
def health():
    return "healthy 👍"


# API resources for UI:
api.add_resource(Beers, "/api/v1/beers", "/api/v1/locations/<location>/beers")
api.add_resource(Beer, "/api/v1/beers/<beer_id>", "/api/v1/locations/<location>/beers/<beer_id>")
api.add_resource(Locations, "/api/v1/locations")
api.add_resource(Location, "/api/v1/locations/<location>")
api.add_resource(Taps, "/api/v1/taps", "/api/v1/locations/<location>/taps")
api.add_resource(Tap, "/api/v1/taps/<tap_id>", "/api/v1/locations/<location>/taps/<tap_id>")
api.add_resource(Sensors, "/api/v1/sensors", "/api/v1/locations/<location>/sensors")
api.add_resource(Sensor, "/api/v1/sensors/<sensor_id>", "/api/v1/locations/<location>/sensors/<sensor_id>")
api.add_resource(SensorData, "/api/v1/sensors/<sensor_id>/<data_type>", "/api/v1/locations/<location>/sensors/<sensor_id>/<data_type>")
api.add_resource(ExternalBrewToolTypes, "/api/v1/external_brew_tools/types")
api.add_resource(ExternalBrewTool, "/api/v1/external_brew_tools/<tool_name>")
api.add_resource(SearchExternalBrewTool, "/api/v1/external_brew_tools/<tool_name>/search")

# UI resources
#api.add_resource(AWSOrder, "/aws/order")

app.wsgi_app = ProxyFix(app.wsgi_app)
app.secret_key = os.environ.get("APP_SECRET_KEY", str(uuid.uuid4()))


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

    http_server = WSGIServer(("", port), app, log=IgnoringLogAdapter(app.logger, log_level))
    logger.debug("app.config: %s", app.config)
    logger.debug("config: %s", app_config.data_flat)
    logger.info("Serving on port %s", port)

    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        logger.info("User interrupted - Goodbye")
