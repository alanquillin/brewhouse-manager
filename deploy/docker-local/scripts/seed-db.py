#!/usr/bin/env python3

import argparse
import logging
import os
from datetime import datetime, timedelta
from time import sleep
from uuid import uuid4

from lib.config import Config
from db import (
    locations,
    session_scope,
    Base,
    taps,
    beers,
    sensors,
    admins
)
from sqlalchemy.exc import OperationalError, IntegrityError

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
        }
    },
    {
        "id": beer_l1b2_id,
        "name": "4th and Lager",
        "description": "An American Lager",
        "style": "Lager",
        "abv": 5.2,
        "ibu": 17,
        "srm": 4.1
    },
    {
        "id": beer_l1b3_id,
        "external_brewing_tool": "brewfather",
        "external_brewing_tool_meta": {
            "batch_id": "k9MRi0BeqW3sFdltMhqy4CnHtSwDOG"
        },
        "style": "Christmas Ale"
    },
    {
        "id": beer_l1b4_id,
        "external_brewing_tool": "brewfather",
        "external_brewing_tool_meta": {
            "batch_id": "S0spuNZL8PcQM2f2ioCgAoR8A0tv2q"
        }
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
        "tap_type": "beer",
        "beer_id": beer_l1b1_id,
        "sensor_id": sensor_l1s1_id
    },
    {
        "id": "c342d381-d913-46a1-83d0-6e6cda4475c6",
        "tap_number": 2,
        "description": "Tap 2",
        "location_id": location1_id,
        "tap_type": "beer",
        "beer_id": beer_l1b2_id,
        "sensor_id": sensor_l1s2_id
    },
    {
        "id": "e24fd19e-cfed-45e8-91c5-544ec5db4ad5",
        "tap_number": 3,
        "description": "Tap 3",
        "location_id": location1_id,
        "tap_type": "beer",
        "beer_id": beer_l1b3_id,
        "sensor_id": sensor_l1s3_id
    },
    {
        "id": "572dcdba-4d37-4061-9c5c-20225de45513",
        "tap_number": 4,
        "description": "Tap 4",
        "location_id": location1_id,
        "tap_type": "beer",
        "beer_id": beer_l1b4_id,
        "sensor_id": sensor_l1s4_id
    },
    {
        "id": "f92adea8-27f1-4d45-80f0-066a47ce496e",
        "tap_number": 1,
        "description": "Tap 1",
        "location_id": location2_id,
        "tap_type": "beer",
        "sensor_id": sensor_l2s1_id
    },
    {
        "id": "e0b83ea2-217b-440b-bad5-24548dc8bef1",
        "tap_number": 2,
        "description": "Tap 2",
        "location_id": location2_id,
        "tap_type": "beer"
    }
]

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
        Base.metadata.create_all(db_session.get_bind())

        seed_db(db_session, locations.Locations, LOCATIONS)
        seed_db(db_session, beers.Beers, BEERS)
        seed_db(db_session, sensors.Sensors, SENSORS)
        seed_db(db_session, taps.Taps, TAPS)
            
