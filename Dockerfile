# NodeJS base
# ############################################################
FROM node:18.20-bullseye AS node-base

RUN yarn config set network-timeout 1200000 -g
RUN yarn global add @angular/cli
COPY ui/angular.json ui/tsconfig.app.json ui/tsconfig.json ui/package.json ui/.browserslistrc /ui/
WORKDIR /ui
RUN yarn install --non-interactive

# Python base
# ############################################################
FROM python:3.11-slim-bullseye AS python-base

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential libpq-dev libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -U pip 
RUN pip install setuptools wheel
ENV CRYPTOGRAPHY_DONT_BUILD_RUST=1
RUN pip install "cryptography<3.5"
RUN pip install "poetry>=1.2.2"

RUN poetry config virtualenvs.in-project true
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi --only main --no-root
RUN poetry run pip install psycopg2-binary

RUN apt-get purge -y --auto-remove gcc build-essential libffi-dev libssl-dev


# Angular build
# ############################################################
FROM node-base AS node-build

ARG build_for=prod
COPY ui/src /ui/src
RUN yarn run build:${build_for}

# Final build
# ############################################################
FROM python-base AS final

ARG build_for=prod


ENV PYTHONUNBUFFERED=1
ENV CONFIG_BASE_DIR=/brewhouse-manager/config
ENV RUN_ENV=${build_for}

RUN addgroup app --gid 10000 && \
    useradd --gid app \
            --shell /sbin/nologin \
            --no-create-home \
            --uid 10000 app
            

COPY --from=node-build /ui/dist/brewhouse-manager /brewhouse-manager/api/static/

COPY config /brewhouse-manager/config
COPY api /brewhouse-manager/api
COPY entrypoint.sh /brewhouse-manager/api

WORKDIR /brewhouse-manager/api

USER 10000

EXPOSE 5000

ENTRYPOINT ["/bin/sh", "entrypoint.sh"]
