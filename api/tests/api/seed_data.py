#!/usr/bin/env python3
"""
Seed data for functional tests.
Provides a consistent known state for all functional tests.

Can be run as a standalone script or imported as a module.
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# Set up config path before imports when running as a script
if __name__ == "__main__":
    _PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    os.environ.setdefault("CONFIG_BASE_DIR", os.path.join(_PROJECT_ROOT, "config"))

from sqlalchemy.exc import IntegrityError

from db import (
    async_session_scope,
    batches,
    batch_locations,
    beers,
    beverages,
    locations,
    on_tap,
    tap_monitors,
    taps,
    users,
    user_locations,
)
from lib.config import Config

logger = logging.getLogger(__name__)

# ============================================================================
# Test Data Definitions
# All IDs are fixed UUIDs to allow predictable test assertions
# ============================================================================

# Locations
LOCATION_MAIN_ID = "11111111-1111-1111-1111-111111111111"
LOCATION_SECONDARY_ID = "22222222-2222-2222-2222-222222222222"
LOCATION_EMPTY_ID = "33333333-3333-3333-3333-333333333333"

LOCATIONS = [
    {
        "id": LOCATION_MAIN_ID,
        "name": "main-taproom",
        "description": "Main Taproom - 3 Taps"
    },
    {
        "id": LOCATION_SECONDARY_ID,
        "name": "secondary-taproom",
        "description": "Secondary Taproom - 2 Taps"
    },
    {
        "id": LOCATION_EMPTY_ID,
        "name": "empty-taproom",
        "description": "Empty Taproom - No Taps"
    }
]

# Beers
BEER_IPA_ID = "aaaa1111-1111-1111-1111-111111111111"
BEER_STOUT_ID = "aaaa2222-2222-2222-2222-222222222222"
BEER_LAGER_ID = "aaaa3333-3333-3333-3333-333333333333"
BEER_WHEAT_ID = "aaaa4444-4444-4444-4444-444444444444"

BEERS = [
    {
        "id": BEER_IPA_ID,
        "name": "Test IPA",
        "description": "A hoppy test IPA",
        "style": "IPA",
        "abv": 6.5,
        "ibu": 65,
        "srm": 8.0
    },
    {
        "id": BEER_STOUT_ID,
        "name": "Test Stout",
        "description": "A rich test stout",
        "style": "Stout",
        "abv": 5.8,
        "ibu": 35,
        "srm": 40.0
    },
    {
        "id": BEER_LAGER_ID,
        "name": "Test Lager",
        "description": "A crisp test lager",
        "style": "Lager",
        "abv": 4.5,
        "ibu": 18,
        "srm": 4.0
    },
    {
        "id": BEER_WHEAT_ID,
        "name": "Test Wheat",
        "description": "A refreshing test wheat beer",
        "style": "Wheat",
        "abv": 5.0,
        "ibu": 12,
        "srm": 5.0
    }
]

# Beverages (non-beer)
BEVERAGE_COFFEE_ID = "bbbb1111-1111-1111-1111-111111111111"
BEVERAGE_SODA_ID = "bbbb2222-2222-2222-2222-222222222222"

BEVERAGES = [
    {
        "id": BEVERAGE_COFFEE_ID,
        "name": "Test Cold Brew",
        "description": "A smooth cold brew coffee",
        "brewery": "Test Coffee Co.",
        "type": "cold-brew",
        "flavor": "Medium Roast"
    },
    {
        "id": BEVERAGE_SODA_ID,
        "name": "Test Soda",
        "description": "A refreshing test soda",
        "brewery": "Test Soda Co.",
        "type": "soda",
        "flavor": "Cola"
    }
]

# Tap Monitors
TAP_MONITOR_1_ID = "cccc1111-1111-1111-1111-111111111111"
TAP_MONITOR_2_ID = "cccc2222-2222-2222-2222-222222222222"
TAP_MONITOR_3_ID = "cccc3333-3333-3333-3333-333333333333"
TAP_MONITOR_SECONDARY_ID = "cccc4444-4444-4444-4444-444444444444"

TAP_MONITORS = [
    {
        "id": TAP_MONITOR_1_ID,
        "name": "Monitor 1",
        "location_id": LOCATION_MAIN_ID,
        "monitor_type": "open-plaato-keg",
        "meta": {
            "device_id": "test-device-001",
            "empty_keg_weight": 4400,
            "empty_keg_weight_unit": "g",
            "max_keg_volume": 5,
            "max_keg_volume_unit": "gal"
        }
    },
    {
        "id": TAP_MONITOR_2_ID,
        "name": "Monitor 2",
        "location_id": LOCATION_MAIN_ID,
        "monitor_type": "open-plaato-keg",
        "meta": {
            "device_id": "test-device-002",
            "empty_keg_weight": 4400,
            "empty_keg_weight_unit": "g",
            "max_keg_volume": 5,
            "max_keg_volume_unit": "gal"
        }
    },
    {
        "id": TAP_MONITOR_3_ID,
        "name": "Monitor 3",
        "location_id": LOCATION_MAIN_ID,
        "monitor_type": "keg-volume-monitor-weight",
        "meta": {
            "device_id": "test-device-003"
        }
    },
    {
        "id": TAP_MONITOR_SECONDARY_ID,
        "name": "Secondary Monitor",
        "location_id": LOCATION_SECONDARY_ID,
        "monitor_type": "open-plaato-keg",
        "meta": {
            "device_id": "test-device-004",
            "empty_keg_weight": 4400,
            "empty_keg_weight_unit": "g",
            "max_keg_volume": 5,
            "max_keg_volume_unit": "gal"
        }
    }
]

# Batches
BATCH_IPA_ID = "dddd1111-1111-1111-1111-111111111111"
BATCH_STOUT_ID = "dddd2222-2222-2222-2222-222222222222"
BATCH_LAGER_ID = "dddd3333-3333-3333-3333-333333333333"
BATCH_COFFEE_ID = "dddd4444-4444-4444-4444-444444444444"
BATCH_WHEAT_ID = "dddd5555-5555-5555-5555-555555555555"

BATCHES = [
    {
        "id": BATCH_IPA_ID,
        "beer_id": BEER_IPA_ID,
        "brew_date": datetime(2025, 1, 1),
        "keg_date": datetime(2025, 1, 15),
        "abv": 6.7,
        "ibu": 68,
    },
    {
        "id": BATCH_STOUT_ID,
        "beer_id": BEER_STOUT_ID,
        "brew_date": datetime(2025, 1, 10),
        "keg_date": datetime(2025, 1, 24),
        "abv": 5.9,
        "ibu": 36,
    },
    {
        "id": BATCH_LAGER_ID,
        "beer_id": BEER_LAGER_ID,
        "brew_date": datetime(2025, 2, 1),
        "keg_date": datetime(2025, 2, 28),
        "abv": 4.6,
        "ibu": 17,
    },
    {
        "id": BATCH_COFFEE_ID,
        "beverage_id": BEVERAGE_COFFEE_ID,
        "brew_date": datetime(2025, 2, 15),
        "keg_date": datetime(2025, 2, 16),
    },
    {
        "id": BATCH_WHEAT_ID,
        "beer_id": BEER_WHEAT_ID,
        "brew_date": datetime(2025, 2, 10),
        "keg_date": datetime(2025, 2, 24),
        "abv": 5.1,
        "ibu": 13,
    }
]

# Batch Locations - which batches are available at which locations
BATCH_LOCATIONS = [
    {"batch_id": BATCH_IPA_ID, "location_id": LOCATION_MAIN_ID},
    {"batch_id": BATCH_STOUT_ID, "location_id": LOCATION_MAIN_ID},
    {"batch_id": BATCH_LAGER_ID, "location_id": LOCATION_MAIN_ID},
    {"batch_id": BATCH_COFFEE_ID, "location_id": LOCATION_MAIN_ID},
    {"batch_id": BATCH_WHEAT_ID, "location_id": LOCATION_SECONDARY_ID},
    {"batch_id": BATCH_IPA_ID, "location_id": LOCATION_SECONDARY_ID},
]

# On Tap records
ON_TAP_1_ID = "eeee1111-1111-1111-1111-111111111111"
ON_TAP_2_ID = "eeee2222-2222-2222-2222-222222222222"
ON_TAP_3_ID = "eeee3333-3333-3333-3333-333333333333"
ON_TAP_SECONDARY_ID = "eeee4444-4444-4444-4444-444444444444"

ON_TAP = [
    {"id": ON_TAP_1_ID, "batch_id": BATCH_IPA_ID},
    {"id": ON_TAP_2_ID, "batch_id": BATCH_STOUT_ID},
    {"id": ON_TAP_3_ID, "batch_id": BATCH_LAGER_ID},
    {"id": ON_TAP_SECONDARY_ID, "batch_id": BATCH_WHEAT_ID},
]

# Taps
TAP_1_ID = "ffff1111-1111-1111-1111-111111111111"
TAP_2_ID = "ffff2222-2222-2222-2222-222222222222"
TAP_3_ID = "ffff3333-3333-3333-3333-333333333333"
TAP_SECONDARY_1_ID = "ffff4444-4444-4444-4444-444444444444"
TAP_SECONDARY_2_ID = "ffff5555-5555-5555-5555-555555555555"

TAPS = [
    {
        "id": TAP_1_ID,
        "tap_number": 1,
        "description": "Tap 1 - IPA",
        "location_id": LOCATION_MAIN_ID,
        "on_tap_id": ON_TAP_1_ID,
        "tap_monitor_id": TAP_MONITOR_1_ID
    },
    {
        "id": TAP_2_ID,
        "tap_number": 2,
        "description": "Tap 2 - Stout",
        "location_id": LOCATION_MAIN_ID,
        "on_tap_id": ON_TAP_2_ID,
        "tap_monitor_id": TAP_MONITOR_2_ID
    },
    {
        "id": TAP_3_ID,
        "tap_number": 3,
        "description": "Tap 3 - Lager",
        "location_id": LOCATION_MAIN_ID,
        "on_tap_id": ON_TAP_3_ID,
        "tap_monitor_id": TAP_MONITOR_3_ID
    },
    {
        "id": TAP_SECONDARY_1_ID,
        "tap_number": 1,
        "description": "Tap 1 - Wheat",
        "location_id": LOCATION_SECONDARY_ID,
        "on_tap_id": ON_TAP_SECONDARY_ID,
        "tap_monitor_id": TAP_MONITOR_SECONDARY_ID
    },
    {
        "id": TAP_SECONDARY_2_ID,
        "tap_number": 2,
        "description": "Tap 2 - Empty",
        "location_id": LOCATION_SECONDARY_ID,
    }
]

# Users
USER_ADMIN_ID = "00001111-1111-1111-1111-111111111111"
USER_REGULAR_ID = "00002222-2222-2222-2222-222222222222"

USERS = [
    {
        "id": USER_ADMIN_ID,
        "email": "admin@test.local",
        "first_name": "Test",
        "last_name": "Admin",
        "admin": True,
        "api_key": "test-admin-api-key-12345",
        "password": "testpassword123"
    },
    {
        "id": USER_REGULAR_ID,
        "email": "user@test.local",
        "first_name": "Test",
        "last_name": "User",
        "admin": False,
        "api_key": "test-user-api-key-67890",
        "password": "testpassword456"
    }
]

# User Locations - which locations users have access to
USER_LOCATIONS = [
    {"user_id": USER_ADMIN_ID, "location_id": LOCATION_MAIN_ID},
    {"user_id": USER_ADMIN_ID, "location_id": LOCATION_SECONDARY_ID},
    {"user_id": USER_ADMIN_ID, "location_id": LOCATION_EMPTY_ID},
    {"user_id": USER_REGULAR_ID, "location_id": LOCATION_MAIN_ID},
]


# ============================================================================
# Seeding Functions
# ============================================================================

async def seed_table(config: Config, db_class, items: List[Dict[str, Any]], pk: str = "id", q_keys: Optional[List[str]] = None):
    """Seed a single table with items."""
    table_name = db_class.__name__

    for item in items:
        async with async_session_scope(config) as db_session:
            try:
                res = None
                if q_keys:
                    kwargs = {k: item[k] for k in q_keys}
                    res = await db_class.query(db_session, **kwargs)
                else:
                    res = await db_class.get_by_pkey(db_session, item.get(pk))

                if not res:
                    logger.debug(f"Creating {table_name}: {item.get(pk, item)}")
                    new_item = await db_class.create(db_session, **item)
                    if not new_item:
                        raise Exception(f"Failed to create item in {table_name}")
                else:
                    logger.debug(f"Item already exists in {table_name}: {item.get(pk, 'UNKNOWN')}")

            except IntegrityError as ex:
                logger.warning(f"Integrity error in {table_name}: {ex}")
                raise


async def seed_all(config: Config):
    """Seed all tables in the correct order (respecting foreign key constraints)."""
    logger.info("Starting database seeding...")

    # Seed in order of dependencies
    await seed_table(config, locations.Locations, LOCATIONS)
    await seed_table(config, beers.Beers, BEERS)
    await seed_table(config, beverages.Beverages, BEVERAGES)
    await seed_table(config, tap_monitors.TapMonitors, TAP_MONITORS)
    await seed_table(config, batches.Batches, BATCHES)
    await seed_table(config, batch_locations.BatchLocations, BATCH_LOCATIONS, q_keys=["batch_id", "location_id"])
    await seed_table(config, on_tap.OnTap, ON_TAP)
    await seed_table(config, taps.Taps, TAPS)
    await seed_table(config, users.Users, USERS)
    await seed_table(config, user_locations.UserLocations, USER_LOCATIONS, q_keys=["user_id", "location_id"])

    logger.info("Database seeding complete!")


# Export all IDs for use in tests
__all__ = [
    # Location IDs
    "LOCATION_MAIN_ID",
    "LOCATION_SECONDARY_ID",
    "LOCATION_EMPTY_ID",
    # Beer IDs
    "BEER_IPA_ID",
    "BEER_STOUT_ID",
    "BEER_LAGER_ID",
    "BEER_WHEAT_ID",
    # Beverage IDs
    "BEVERAGE_COFFEE_ID",
    "BEVERAGE_SODA_ID",
    # Tap Monitor IDs
    "TAP_MONITOR_1_ID",
    "TAP_MONITOR_2_ID",
    "TAP_MONITOR_3_ID",
    "TAP_MONITOR_SECONDARY_ID",
    # Batch IDs
    "BATCH_IPA_ID",
    "BATCH_STOUT_ID",
    "BATCH_LAGER_ID",
    "BATCH_COFFEE_ID",
    "BATCH_WHEAT_ID",
    # On Tap IDs
    "ON_TAP_1_ID",
    "ON_TAP_2_ID",
    "ON_TAP_3_ID",
    "ON_TAP_SECONDARY_ID",
    # Tap IDs
    "TAP_1_ID",
    "TAP_2_ID",
    "TAP_3_ID",
    "TAP_SECONDARY_1_ID",
    "TAP_SECONDARY_2_ID",
    # User IDs
    "USER_ADMIN_ID",
    "USER_REGULAR_ID",
    # Data lists
    "LOCATIONS",
    "BEERS",
    "BEVERAGES",
    "TAP_MONITORS",
    "BATCHES",
    "BATCH_LOCATIONS",
    "ON_TAP",
    "TAPS",
    "USERS",
    "USER_LOCATIONS",
    # Functions
    "seed_all",
]


# Allow running as a standalone script
if __name__ == "__main__":
    logging.basicConfig(
        level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper()),
        format="%(levelname)-8s: %(asctime)-15s [%(name)s]: %(message)s"
    )

    config = Config()
    config.setup(config_files=["default.json"])

    logger.info("Starting database seeding...")
    logger.debug(f"DB Host: {config.get('db.host')}")
    logger.debug(f"DB Name: {config.get('db.name')}")

    asyncio.run(seed_all(config))
