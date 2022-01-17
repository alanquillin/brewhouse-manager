import alembic.config  # isort:skip
import os
import sys

here = os.path.dirname(os.path.abspath(__file__))


def call_alembic(args):
    alembic.config.main(argv=["-c", os.path.join(here, "alembic.ini")] + args)


def main():
    call_alembic(sys.argv[1:])
