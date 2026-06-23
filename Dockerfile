# NodeJS base
# ############################################################
FROM node:24.15-trixie AS node-base

RUN npm install -g pnpm@11 @angular/cli
COPY ui/angular.json ui/tsconfig.app.json ui/tsconfig.json ui/package.json ui/pnpm-lock.yaml ui/pnpm-workspace.yaml ui/.browserslistrc /ui/
WORKDIR /ui
RUN pnpm install --frozen-lockfile

# Python build
# ############################################################
FROM python:3.12-slim-trixie AS python-build

RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc build-essential libpq-dev libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install -U pip setuptools wheel
RUN pip install "poetry>=2.4.1"

RUN poetry config virtualenvs.in-project true
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi --only main --no-root
RUN poetry run pip install psycopg2-binary


# Angular build
# ############################################################
FROM node-base AS node-build

ARG build_for=prod
COPY ui/src /ui/src
RUN pnpm run build:${build_for}

# Final image — no poetry, no build tools, no compiler
# ############################################################
FROM python:3.12-slim-trixie AS final

ARG build_for=prod

ENV PYTHONUNBUFFERED=1
ENV CONFIG_BASE_DIR=/brewhouse-manager/config
ENV RUN_ENV=${build_for}

RUN groupadd --gid 10000 app && \
    useradd --gid app \
            --shell /sbin/nologin \
            --no-create-home \
            --uid 10000 app

COPY --from=python-build /.venv /.venv
COPY --from=node-build /ui/dist/brewhouse-manager/browser /brewhouse-manager/api/static/

COPY config /brewhouse-manager/config
COPY api /brewhouse-manager/api
COPY entrypoint.sh /brewhouse-manager/api

WORKDIR /brewhouse-manager/api

USER 10000

EXPOSE 5000

ENTRYPOINT ["/bin/sh", "entrypoint.sh"]
