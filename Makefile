#!make
ROOT_PY3 := python3

POETRY := $(shell which poetry)
POETRY_VARS :=
ifeq ($(shell uname -s),Darwin)
	HOMEBREW_OPENSSL_DIR := $(shell brew --prefix openssl)
	POETRY_VARS += CFLAGS="-I$(HOMEBREW_OPENSSL_DIR)/include"
	POETRY_VARS += LDFLAGS="-L$(HOMEBREW_OPENSSL_DIR)/lib"
endif

BANDIT := $(POETRY) run bandit
BLACK := $(POETRY) run black
ISORT := $(POETRY) run isort
PIP := $(POETRY) run pip
PYLINT := $(POETRY) run pylint
PYTEST := $(POETRY) run pytest
PYTHON := $(POETRY) run python3

TAG_LATEST := false
CONFIG_BASE_DIR ?= config
TESTS ?= tests/
DOCKER_BUILD_ARGS :=
PYTEST_ARGS += --disable-warnings --log-level DEBUG
DOCKER_IMAGE ?= brewhouse-manager
DOCKER_DB_SEED_IMAGE ?= brewhouse-manager-db-seed
DOCKER_IMAGE_TAG ?= latest
DOCKER_IMAGE_TAG_DEV ?= dev
DOCKER_SOURCE_IMAGE_TAG ?= $(DOCKER_IMAGE_TAG)
DOCKER := docker
IMAGE_REPOSITORY := alanquillin
REPOSITORY_IMAGE ?= brewhouse-manager

ifneq ("$(wildcard .env)","")
    include .env
	export $(shell sed 's/=.*//' .env)
endif

ifeq ("$(wildcard deploy/docker-local/.env)","")
    $(shell touch deploy/docker-local/.env)
endif

ifeq ("$(wildcard deploy/docker-local/my-config.json)","")
    $(shell echo '{}' >> deploy/docker-local/my-config.json)
endif


$(info Hello World)
ifeq ($(TAG_LATEST),true)
$(info Setting build args)
override DOCKER_BUILD_ARGS += -t $(IMAGE_REPOSITORY)/$(REPOSITORY_IMAGE):latest
endif


.PHONY: build build-dev docker-build test format-py test-py test-py-verbose test-py-cov-html \
	build-db-seed build-db-seed-fetch-tf depends test-depends un-dev clean clean-images clean-all

# dependency targets

depends: 
	$(POETRY_VARS) $(POETRY) install --no-dev --no-root

test-depends: 
	$(POETRY_VARS) $(POETRY) install --no-root

update-depends: test-depends
	$(POETRY_VARS) $(POETRY) update

# Targets for building containers

# prod
build: update-depends docker-build

docker-build:
ifeq ($(VERSION),)
	$(error VERSION was not provided)
endif
	$(DOCKER) buildx build --platform=linux/amd64,linux/arm64,linux/arm $(DOCKER_BUILD_ARGS) -t $(IMAGE_REPOSITORY)/$(REPOSITORY_IMAGE):$(VERSION) .

# dev

build-dev:
	$(DOCKER) build $(DOCKER_BUILD_ARGS) --build-arg build_for=dev -t $(DOCKER_IMAGE):$(DOCKER_IMAGE_TAG_DEV) .

build-db-seed:
	$(DOCKER) build $(DOCKER_BUILD_ARGS) -t $(DOCKER_DB_SEED_IMAGE):$(DOCKER_IMAGE_TAG_DEV) deploy/docker-local

rebuild-db-seed: 
	$(DOCKER) build $(DOCKER_BUILD_ARGS) -t $(DOCKER_DB_SEED_IMAGE):$(DOCKER_IMAGE_TAG_DEV) --no-cache deploy/docker-local

# Targets for publishing containers

publish:
	$(MAKE) build DOCKER_BUILD_ARGS+="--push"

# Targets for running the app

run-dev: build-dev build-db-seed
	docker-compose --project-directory deploy/docker-local up

run-web-local:
	pushd ./ui && ng serve --ssl --ssl-key ../deploy/docker-local/certs/localhost.decrypted.key --ssl-cert ../deploy/docker-local/certs/localhost.crt && popd

run-db-migrations:
	./migrate.sh upgrade head

# Testing and Syntax targets

lint-py:
	$(ISORT) --check-only api
	$(PYLINT) api
	$(BLACK) --check api

lint-ts:
	yarn run lint

format-py:
	$(ISORT) api tests deploy
	$(BLACK) api tests deploy

test: update-git-depends ci

test-py:
	CONFIG_PATH=pytest.json CONFIG_BASE_DIR=$(CONFIG_BASE_DIR) \
	$(PYTEST) ${PYTEST_ARGS} ${TESTS}

test-py-cov: PYTEST_ARGS += --cov=api/
test-py-cov: test-py

test-py-cov-html: PYTEST_ARGS += --cov=api api/ --cov-report html
test-py-cov-html: test-py

test-sec:
	$(BANDIT) -r api --exclude test

# Clean up targets

clean:
	docker-compose --project-directory deploy/docker-local down --volumes

clean-image:
	docker rmi $(DOCKER_IMAGE):$(DOCKER_IMAGE_TAG)

clean-seed-image:
	docker rmi $(DOCKER_DB_SEED_IMAGE):$(DOCKER_IMAGE_TAG)

clean-images: clean-image clean-seed-image

clean-all: clean clean-images
