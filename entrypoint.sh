#! /bin/sh

if [ "$RUN_ENV" = "dev" ]; then
    export FLASK_ENV="development"
fi

. /.venv/bin/activate
./migrate.sh upgrade head
python app.py
