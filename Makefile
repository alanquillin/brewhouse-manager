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

CONFIG_BASE_DIR ?= config
TESTS ?= tests/
PYTEST_ARGS += --disable-warnings --log-level DEBUG
DOCKER_IMAGE ?= brewhouse-manager
DOCKER_DB_SEED_IMAGE ?= brewhouse-manager-db-seed
DOCKER_IMAGE_TAG ?= latest
DOCKER := docker
override DOCKER_BUILD_ARGS += --ssh default
DOCKER_BUILD := $(DOCKER) build $(DOCKER_BUILD_ARGS)

NODE_CI_TARGETS := lint-ts
PYTHON_CI_TARGETS := lint-py test-py-cov-html test-sec test-deps
CI_TARGETS := $(NODE_CI_TARGETS) $(PYTHON_CI_TARGETS)

NODE_DOCKER_CI_TARGETS := $(addsuffix /docker,$(NODE_CI_TARGETS))
PYTHON_DOCKER_CI_TARGETS := $(addsuffix /docker,$(PYTHON_CI_TARGETS))
DOCKER_CI_TARGETS := $(NODE_DOCKER_CI_TARGETS) $(PYTHON_DOCKER_CI_TARGETS)

CI_IMAGES := node-ci python-ci
CI_IMAGE_TARGETS := $(addprefix docker-build/,$(CI_IMAGES))

include .env
export $(shell sed 's/=.*//' .env)


.PHONY: build build-dev docker-build \
	test ci ci/node ci/python ci/docker \
	$(CI_IMAGE_TARGETS) \
	$(CI_TARGETS) $(DOCKER_CI_TARGETS) \
	format-py test-py test-py-verbose test-py-cov-html \
	build-db-seed build-db-seed-fetch-tf \
	depends test-depends \
	run run-dev clean clean-images clean-all .env

depends: 
	$(POETRY_VARS) $(POETRY) install --no-dev --no-root

test-depends: 
	$(POETRY_VARS) $(POETRY) install --no-root

update-depends: test-depends
	$(POETRY_VARS) $(POETRY) update

update-git-depends:
	$(POETRY_VARS) $(POETRY) update flask-connect

build: update-git-depends docker-build
test: update-git-depends ci

docker-build:
	$(DOCKER_BUILD) -t $(DOCKER_IMAGE):$(DOCKER_IMAGE_TAG) .

build-dev:
	$(DOCKER_BUILD) --build-arg build_for=dev -t $(DOCKER_IMAGE):$(DOCKER_IMAGE_TAG) .

lint-py:
	$(ISORT) --check-only api
	$(PYLINT) api
	$(BLACK) --check api

lint-ts:
	yarn run lint

format-py:
	$(ISORT) api tests deploy
	$(BLACK) api tests deploy

test-py:
	CONFIG_PATH=pytest.json CONFIG_BASE_DIR=$(CONFIG_BASE_DIR) \
	$(PYTEST) ${PYTEST_ARGS} ${TESTS}

test-py-cov: PYTEST_ARGS += --cov=api/
test-py-cov: test-py

test-py-cov-html: PYTEST_ARGS += --cov=api api/ --cov-report html
test-py-cov-html: test-py

test-sec:
	$(BANDIT) -r api --exclude test

build-db-seed:
	$(DOCKER_BUILD) -t $(DOCKER_DB_SEED_IMAGE):$(DOCKER_IMAGE_TAG) deploy/docker-local

rebuild-db-seed: 
	$(DOCKER_BUILD) -t $(DOCKER_DB_SEED_IMAGE):$(DOCKER_IMAGE_TAG) --no-cache deploy/docker-local

run:
	-@$(DOCKER) run \
		--name brewhouse-manager \
		--env-file .env \
		$(RUN_ARGS) \
		-p 5000:5000 \
		brewhouse-manager

run-dev: build-dev build-db-seed
	docker-compose up

clean:
	docker-compose down --volumes

clean-image:
	docker rmi $(DOCKER_IMAGE):$(DOCKER_IMAGE_TAG)

clean-seed-image:
	docker rmi $(DOCKER_DB_SEED_IMAGE):$(DOCKER_IMAGE_TAG)

clean-images: clean-image clean-seed-image

clean-all: clean clean-images

run-db-migrations:
	./migrate.sh upgrade head
