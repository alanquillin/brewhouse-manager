# NodeJS base
# ############################################################
FROM node:16-buster as node-base

RUN yarn global add @angular/cli
COPY ui/angular.json ui/tsconfig.app.json ui/tsconfig.json ui/package.json /ui/
WORKDIR /ui
RUN yarn install --non-interactive
COPY ui/src /ui/src

# Python base
# ############################################################
FROM python:3.9-buster as python-base

ARG build_for=prod
ENV RUN_ENV=${build_for}

RUN mkdir -p -m 0600 ~/.ssh && \
    ssh-keyscan github.com >> ~/.ssh/known_hosts

RUN pip install -U pip setuptools wheel && \
    pip install "poetry>=1.1.8"
RUN poetry config virtualenvs.in-project true
COPY pyproject.toml poetry.lock ./
RUN poetry run pip install --upgrade pip
RUN --mount=type=ssh poetry install --no-interaction --no-ansi --no-dev --no-root


# Angular build
# ############################################################
FROM node-base as node-build

ARG build_for=prod
RUN yarn run build:${build_for}

# Final build
# ############################################################
FROM python:3.9-slim-buster as final

ARG build_for=prod

ENV CONFIG_PATH=${CONFIG_PATH}
ENV PYTHONUNBUFFERED=1
ENV CONFIG_BASE_DIR=/brewhouse-manager/config
ENV RUN_ENV=${build_for}

RUN addgroup app --gid 10000 && \
    useradd --gid app \
            --shell /sbin/nologin \
            --no-create-home \
            --uid 10000 app
            
RUN pip install -U pip setuptools wheel
RUN pip install 'poetry>=1.1.8'
RUN poetry config virtualenvs.in-project true

COPY pyproject.toml poetry.lock .

COPY --from=python-base /.venv /.venv
COPY --from=node-build /ui/dist/brewhouse-manager /brewhouse-manager/api/static/

COPY config /brewhouse-manager/config
COPY api /brewhouse-manager/api
COPY entrypoint.sh /brewhouse-manager/api

WORKDIR /brewhouse-manager/api

USER 10000

EXPOSE 5000

ENTRYPOINT ["/bin/sh", "entrypoint.sh"]
