#! /bin/bash

POETRY=$(which poetry)
ALEMBIC="${POETRY} run alembic"
PYTHON="${POETRY} run python"

ALEMBIC_ARGS="-c db_migrations/alembic.ini"

: "${ENV:=local}"
: "${DB_USERNAME:=postgres}"
: "${DB_PASSWORD:=postgres}"
: "${DB_HOST:=localhost}"
: "${DB_PORT:=5432}"
: "${DB_NAME:=postgres}"

while getopts ":hH:N:P:u:p:" opt; do
  case ${opt} in
    h )
      echo "Usage: migrate.sh [-h] [-H <DB host>] [-N <DB name>] [-P <DB port>] [-u <DB username>] [-p <DB password>] COMAND [alembic args...]"
      exit 0
      ;;
    H )
      DB_HOST=$OPTARG
      ;;
    N )
      DB_NAME=$OPTARG
      ;;
    P )
      DB_PORT=$OPTARG
      ;;
    p )
      DB_PASSWORD=$OPTARG
      ;;
    u )
      DB_USERNAME=$OPTARG
      ;;
    \? ) 
      echo "Invalid option: $OPTARG" 1>&2
      exit 1
      ;;
    : )
      echo "Invalid option: $OPTARG requires an argument"
      exit 1
      ;;
  esac
done
shift $((OPTIND -1))

export DB_COLUMN_ENCRYPTOIN_KEY_ID
export DB_USERNAME
export DB_PASSWORD
export DB_HOST
export DB_PORT
export DB_NAME

export CTR_NAME=brewhose-manager-migrations

start_container() {
    docker run -p "${DB_PORT}:5432" -e POSTGRES_PASSWORD="${DB_PASSWORD}" --name "${CTR_NAME}" -d postgres:12-alpine
    sleep 5
}

stop_container() {
    docker stop "${CTR_NAME}"
    docker rm "${CTR_NAME}"
}

create() {
    if [[ -z $1 ]]; then
        echo "Please add a short description for your migration."
        exit 1
    fi
    start_container
    ./migrate.sh upgrade head
    ${ALEMBIC} ${ALEMBIC_ARGS} revision --autogenerate -m "$1"
    stop_container
}

test_migrations() {
    start_container
    ./migrate.sh upgrade head
    ${PYTHON} db_migrations/check_migrations_up_to_date.py
    result=$?
    ./migrate.sh downgrade base
    stop_container
    return $result
}

case $1 in
create)
    shift
    create "$@"
    ;;
test)
    if [[ "${ENV}" != "local" ]]; then
        echo "You cannot test migrations against ${ENV}, only local deployments..."
        exit 1
    fi

    shift
    test_migrations "$@"
    ;;
*)
    echo "Running alembic command for ${ENV}"
    ${ALEMBIC} ${ALEMBIC_ARGS} "$@"
    ;;
esac
