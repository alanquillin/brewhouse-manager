#!/usr/bin/env python3

import argparse
from datetime import datetime
import logging
import os
import sys
from time import sleep

from sqlalchemy.exc import IntegrityError, OperationalError

from db import Base, beers, beverages, locations, sensors, session_scope, taps, users, user_locations
from lib.config import Config

location1_id = "fb139af3-2905-4006-9196-62f54bb262ab"
location2_id = "e472c003-01b2-4281-8a64-0c03a7c98e7d"
LOCATIONS = [
    {
        "id": location1_id,
        "name": "my-sample-tap-room",
        "description": "My Sample Taproom"
    },
    {
        "id": location2_id,
        "name": "my-sample-tap-room-2",
        "description": "My Other Sample Taproom"
    }
]

beer_l1b1_id = "8e18732d-61bf-4d4d-b133-a96ad63b63e6"
beer_l1b2_id = "4237761e-95b8-4e6d-bbc3-864e6c80df6e"
beer_l1b3_id = "7627c611-32ac-473b-953f-9fb42efe97e2"
beer_l1b4_id = "bb751fe8-4a14-49a6-95e4-382ff0eaf76c"
beer_l2b1_id = "2988aded-f66d-4e48-8c84-26c5076a2fc2"
beer_l2b2_id = "94525492-6395-4295-91d4-3022258c8d2b"
BEERS = [
    {
        "id": beer_l1b1_id,
        "description": "An Irish Stout on Nitro",
        "external_brewing_tool": "brewfather",
        "external_brewing_tool_meta": {
            "batch_id": "OxLBTCdfmPN5Z5DbrNidISXo67NMN3"
        },
        "location_id": location1_id,
    },
    {
        "id": beer_l1b2_id,
        "name": "4th and Lager",
        "description": "An American Lager",
        "style": "Lager",
        "abv": 5.2,
        "ibu": 17,
        "srm": 4.1,
        "location_id": location1_id,
    },
    {
        "id": beer_l1b3_id,
        "external_brewing_tool": "brewfather",
        "external_brewing_tool_meta": {
            "batch_id": "k9MRi0BeqW3sFdltMhqy4CnHtSwDOG"
        },
        "style": "Christmas Ale",
        "location_id": location1_id,
    },
    {
        "id": beer_l1b4_id,
        "external_brewing_tool": "brewfather",
        "external_brewing_tool_meta": {
            "batch_id": "S0spuNZL8PcQM2f2ioCgAoR8A0tv2q"
        },
        "location_id": location2_id,
    }
]

sensor_l1s1_id = "8f3f0e12-70a7-4dba-9728-caafd6b8ec41"
sensor_l1s2_id = "8f3f0e12-70a7-4dba-9728-caafd6b8ec42"
sensor_l1s3_id = "8f3f0e12-70a7-4dba-9728-caafd6b8ec43"
sensor_l1s4_id = "8f3f0e12-70a7-4dba-9728-caafd6b8ec44"
sensor_l2s1_id = "cacfe989-cc88-4687-9a55-c8748de9f570"
SENSORS=[
    {
        "id": sensor_l1s1_id,
        "name": "Plaato Keg 1",
        "location_id": location1_id,
        "sensor_type": "plaato-keg",
        "meta": {
            "auth_token": os.environ.get("PLAATO_KEG_1_TOKEN", "unknown")
        }
    },
    {
        "id": sensor_l1s2_id,
        "name": "Plaato Keg 2",
        "location_id": location1_id,
        "sensor_type": "plaato-keg",
        "meta": {
            "auth_token": os.environ.get("PLAATO_KEG_2_TOKEN", "unknown")
        }
    },
    {
        "id": sensor_l1s3_id,
        "name": "Plaato Keg 3",
        "location_id": location1_id,
        "sensor_type": "plaato-keg",
        "meta": {
            "auth_token": os.environ.get("PLAATO_KEG_3_TOKEN", "unknown")
        }
    },
    {
        "id": sensor_l1s4_id,
        "name": "Plaato Keg 4",
        "location_id": location1_id,
        "sensor_type": "plaato-keg",
        "meta": {
            "auth_token": os.environ.get("PLAATO_KEG_4_TOKEN", "unknown")
        }
    },
    {
        "id": sensor_l2s1_id,
        "name": "Plaato Keg A",
        "location_id": location2_id,
        "sensor_type": "plaato-keg",
        "meta": {
            "auth_token": "unknown"
        }
    }
]

TAPS = [
    {
        "id": "13353ea9-bf7f-41d3-bd82-97262bf6a97a",
        "tap_number": 1,
        "description": "Tap 1",
        "location_id": location1_id,
        "beer_id": beer_l1b1_id,
        "sensor_id": sensor_l1s1_id
    },
    {
        "id": "c342d381-d913-46a1-83d0-6e6cda4475c6",
        "tap_number": 2,
        "description": "Tap 2",
        "location_id": location1_id,
        "beer_id": beer_l1b2_id,
        "sensor_id": sensor_l1s2_id
    },
    {
        "id": "e24fd19e-cfed-45e8-91c5-544ec5db4ad5",
        "tap_number": 3,
        "description": "Tap 3",
        "location_id": location1_id,
        "beer_id": beer_l1b3_id,
        "sensor_id": sensor_l1s3_id
    },
    {
        "id": "572dcdba-4d37-4061-9c5c-20225de45513",
        "tap_number": 4,
        "description": "Tap 4",
        "location_id": location1_id,
        "sensor_id": sensor_l1s4_id
    },
    {
        "id": "f92adea8-27f1-4d45-80f0-066a47ce496e",
        "tap_number": 1,
        "description": "Tap 1",
        "location_id": location2_id,
        "beer_id": beer_l1b4_id,
        "sensor_id": sensor_l2s1_id
    },
    {
        "id": "e0b83ea2-217b-440b-bad5-24548dc8bef1",
        "tap_number": 2,
        "description": "Tap 2",
        "location_id": location2_id,
    }
]

BEVERAGES = [
    {
        "id": "9c517bc0-6c21-42f7-834a-2d4adb3b7041",
        "name": "Test Cold Brew",
        "description": "This is a test cold brew",
        "brewery": "My Brewing Co.",
        "type": "cold-brew",
        "flavor": "Medium Roast",
        "brew_date": datetime(2022, 1, 1),
        "keg_date": datetime(2022, 1, 4),
        "location_id": location1_id,
        
    },
    {
        "id": "6742d48e-2470-4762-856e-d01f33682579",
        "name": "Test Soda",
        "description": "This is a test soda",
        "brewery": "My Soda Co.",
        "type": "soda",
        "flavor": "Cherry",
        "brew_date": datetime(2022, 2, 19),
        "keg_date": datetime(2022, 2, 21),
        "location_id": location1_id,
        
    },
    {
        "id": "82b47f65-b176-4ff9-94d6-81044e0b6b7f",
        "name": "Test Kombucha",
        "description": "This is a test kombucha",
        "brewery": "My Kombucha Co.",
        "type": "kombucha",
        "flavor": "Orange",
        "brew_date": datetime(2022, 3, 2),
        "keg_date": datetime(2022, 3, 8),
        "location_id": location1_id,
        
    }
]

user1_id = "022041b5-89af-45ee-87ef-135f68c25f3f"
USERS = [{
    "id": user1_id,
    "email": "user1@foo.bar",
    "first_name": "That",
    "last_name": "Guy",
    "profile_pic": None,
    "google_oidc_id": None,
    "admin": False,
    "api_key": "e86842d3-ef54-4db4-af74-278da4f3dda6",
    "password": "foobar"
}]

USER_LOCATIONS = [{
    "id": "fd430679-ba57-455f-99b4-9240480a0cde",
    "user_id": user1_id,
    "location_id": location1_id
}]

def seed_db(db_session, db, items, pk="id"):
    for item in items:
        logger.info(item)
        try:
            if not db.get_by_pkey(db_session, item.get(pk)):
                logger.info("Seeding %s: %s", db.__name__, item)
                db.create(db_session, **item)
            else:
                logger.info("Item %s already exists in %s.", item[pk], db.__name__)
        except IntegrityError as ex:
                logger.debug("Item already exists or a constraint was violated: %s", ex)


def get_initial_user(db_session):
    init_user_email = config.get("auth.initial_user.email")
    set_init_user_pass = config.get("auth.initial_user.set_password")
    init_user_fname = config.get("auth.initial_user.first_name")
    init_user_lname = config.get("auth.initial_user.last_name")
    google_sso_enabled = config.get("auth.oidc.google.enabled")

    if not google_sso_enabled and not set_init_user_pass:
        logger.error("Can create an initial user!  auth.initial_user.set_pass and google authentication is disabled!")
        raise Exception()

    data = {"email": init_user_email, "admin": True}
    if init_user_fname:
        data["first_name"] = init_user_fname
    if init_user_lname:
        data["last_name"] = init_user_lname

    logger.info("No users exist, creating initial user: %s", data)
    if set_init_user_pass:
        data["password"] = app_config.get("auth.initial_user.password")

    user = users.Users.query(db_session, email=init_user_email)
    if user:
        data["id"] = user[0].id

    return data

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
    logging.basicConfig(level=log_level, format="%(levelname)-8s: %(asctime)-15s [%(name)s]: %(message)s")
    logger = logging.getLogger()

    config = Config()
    config.setup(config_files=["default.json"])

    skip_db_seed = config.get("db.seed.skip")
    if skip_db_seed:
        logger.info("Skipping DB Seeding")
        sys.exit()

    logger.debug("config: %s", config.data_flat)
    logger.debug("db host: %s", config.get("db.host"))
    logger.debug("db username: %s", config.get("db.username"))
    logger.debug("db port: %s", config.get("db.port"))
    logger.debug("db name: %s", config.get("db.name"))
    logger.debug("db password: %s", config.get("db.password"))


    with session_scope(config) as db_session:
        while True:
            try:
                db_session.execute("select 1")
                logger.debug("Database ready!")
                break
            except OperationalError:
                logger.debug("Waiting for database readiness")
                sleep(3)

        logger.debug("Creating database schema and seeding with data")

        seed_db(db_session, locations.Locations, LOCATIONS)
        seed_db(db_session, beers.Beers, BEERS)
        seed_db(db_session, beverages.Beverages, BEVERAGES)
        seed_db(db_session, sensors.Sensors, SENSORS)
        seed_db(db_session, taps.Taps, TAPS)
        initial_user_data = get_initial_user(db_session)
        if initial_user_data:
            USERS.append(initial_user_data)
        seed_db(db_session, users.Users, USERS)
        if initial_user_data:
            initial_user = users.Users.query(db_session, email=initial_user_data["email"])
            if initial_user:
                for l in LOCATIONS:
                    ulm = user_locations.UserLocations.query(db_session, user_id=initial_user[0].id, location_id=l["id"])
                    if not ulm:
                        USER_LOCATIONS.append({"user_id": initial_user[0].id ,"location_id": l["id"]})
        seed_db(db_session, user_locations.UserLocations, USER_LOCATIONS)
            
