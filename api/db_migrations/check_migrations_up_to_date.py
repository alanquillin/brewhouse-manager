#! /usr/bin/env python3

# pylint: disable=wrong-import-position

import pathlib
import sys

from sqlalchemy.exc import ProgrammingError

sys.path.insert(0, str(pathlib.Path(__file__).absolute().parent.parent))

from db import *  # pylint: disable=unused-wildcard-import,wildcard-import
from lib.config import Config


# Currently only checks if all the columns match the models - it should probably also check for constraints and indexes.
def health_check_migrations():
    with session_scope(Config()) as session:
        for model in Base.metadata.sorted_tables:
            try:
                session.query(model).first()
            except ProgrammingError:
                print("{} model does not match migration state".format(model))
                sys.exit(1)
        return print("Migrations up to date with models")


health_check_migrations()
