#!/usr/bin/env python3
"""
Database reset script for functional tests.
This script drops all tables, recreates the schema, and seeds with test data.
"""

import asyncio
import logging
import os
import sys
from time import sleep
from urllib.parse import quote

from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql import text

# Set up config path before imports
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("CONFIG_BASE_DIR", os.path.join(_PROJECT_ROOT, "config"))

from db import Base, async_session_scope
from lib.config import Config


def import_all_models():
    """Import all model modules to register them with Base.metadata.

    This is done inside a function to avoid circular import issues.
    """
    # These imports register the models with SQLAlchemy's Base.metadata
    from db import (  # noqa: F401
        audit,
        batches,
        batch_locations,
        batch_overrides,
        beers,
        beverages,
        image_transitions,
        locations,
        on_tap,
        plaato_data,
        tap_monitors,
        taps,
        user_locations,
        users,
    )

logging.basicConfig(
    level=getattr(logging, os.environ.get("LOG_LEVEL", "INFO").upper()),
    format="%(levelname)-8s: %(asctime)-15s [%(name)s]: %(message)s"
)
logger = logging.getLogger(__name__)


def get_async_engine(config: Config):
    """Create an async database engine."""
    password = config.get("db.password")
    if not password:
        raise ValueError("Password required for database connections")

    return create_async_engine(
        (
            "postgresql+asyncpg://"
            f"{quote(config.get('db.username'))}:{quote(password)}@{quote(config.get('db.host'))}:"
            f"{config.get('db.port')}/{quote(config.get('db.name'))}"
        ),
    )


async def wait_for_db(config: Config, max_retries: int = 30, retry_interval: int = 2):
    """Wait for database to be ready."""
    for attempt in range(max_retries):
        try:
            async with async_session_scope(config) as db_session:
                await db_session.execute(text("SELECT 1"))
                logger.info("Database is ready!")
                return True
        except OperationalError:
            logger.debug(f"Waiting for database... (attempt {attempt + 1}/{max_retries})")
            sleep(retry_interval)

    logger.error("Database not ready after maximum retries")
    return False


async def drop_all_tables(config: Config):
    """Drop all tables in the database."""
    logger.info("Dropping all tables...")

    # Import models to register them with metadata
    import_all_models()

    engine = get_async_engine(config)
    async with engine.begin() as conn:
        # Drop all tables using CASCADE to handle foreign key constraints
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

    logger.info("All tables dropped successfully")


async def create_all_tables(config: Config):
    """Create all tables in the database."""
    logger.info("Creating all tables...")

    # Import models to register them with metadata
    import_all_models()

    engine = get_async_engine(config)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

    logger.info("All tables created successfully")


async def seed_database(config: Config):
    """Seed the database with test data."""
    logger.info("Seeding database with test data...")

    # Import seed data
    from seed_data import seed_all

    await seed_all(config)

    logger.info("Database seeding complete!")


async def reset_database(config: Config):
    """Full database reset: drop, create, and seed."""
    # Wait for database to be ready
    if not await wait_for_db(config):
        sys.exit(1)

    # Drop all tables
    await drop_all_tables(config)

    # Create all tables
    await create_all_tables(config)

    # Seed with test data
    await seed_database(config)

    logger.info("Database reset complete!")


if __name__ == "__main__":
    config = Config()
    config.setup(config_files=["default.json"])

    logger.info("Starting database reset...")
    logger.debug(f"DB Host: {config.get('db.host')}")
    logger.debug(f"DB Name: {config.get('db.name')}")

    asyncio.run(reset_database(config))
