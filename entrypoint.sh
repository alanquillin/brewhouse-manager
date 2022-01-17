#! /bin/sh

if [ "$RUN_ENV" = "dev" ]; then
    export FLASK_ENV="development"
fi

poetry run python api.py
