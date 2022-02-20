# pylint: disable=unused-import,wrong-import-order,wrong-import-position,unused-wildcard-import,wildcard-import

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, text

config = context.config
fileConfig(config.config_file_name)

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).absolute().parent.parent))

from db import *
from db import Base
from lib.config import Config

target_metadata = Base.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True, dialect_opts={"paramstyle": "named"})

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    _config = Config()

    conf = config.get_section(config.config_ini_section)
    conf["sqlalchemy.url"] = (
        "postgresql://"
        f"{_config.get('db.username')}:{_config.get('db.password')}"
        f"@{_config.get('db.host')}:"
        f"{_config.get('db.port')}/{_config.get('db.name')}"
    )

    connectable = engine_from_config(conf, prefix="sqlalchemy.", poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        connection.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";'))
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
