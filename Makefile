#!make
ROOT_PY3 := python3

POETRY := $(shell which poetry)
POETRY_VARS :=
ifeq ($(shell uname -s),Darwin)
	HOMEBREW_OPENSSL_DIR := $(shell brew --prefix openssl)
	POETRY_VARS += CFLAGS="-I$(HOMEBREW_OPENSSL_DIR)/include"
	POETRY_VARS += LDFLAGS="-L$(HOMEBREW_OPENSSL_DIR)/lib"
endif

ifeq ($(shell uname -p),arm)
	POETRY_VARS += arch -arm64
endif

BLACK := $(POETRY) run black
ISORT := $(POETRY) run isort
PYLINT := $(POETRY) run pylint
PYTEST := $(POETRY) run pytest
PYTHON := $(POETRY) run python3

TAG_LATEST := false
DOCKER_IMAGE ?= brewhouse-manager
DOCKER_DB_SEED_IMAGE ?= brewhouse-manager-db-seed
DOCKER_IMAGE_TAG_DEV ?= dev
DOCKER_IMAGE_TAG_CI ?= ci
DOCKER := $(shell which docker)
IMAGE_REPOSITORY := alanquillin
REPOSITORY_IMAGE ?= $(DOCKER_IMAGE)
PLATFORMS ?= linux/amd64,linux/arm64

ifeq ($(POETRY),)
$(error Poetry is not installed and is required)
endif

ifeq ($(DOCKER),)
$(error Docker is not installed and is required)
endif

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

ifeq ("$(wildcard deploy/docker-local/uploads/img)","")
    $(shell mkdir -p deploy/docker-local/uploads/img/beer &&  mkdir -p deploy/docker-local/uploads/img/beverage &&  mkdir -p deploy/docker-local/uploads/img/user && chmod -R 777 deploy/docker-local/uploads)
endif


ifeq ($(TAG_LATEST),true)
override DOCKER_BUILD_ARGS += -t $(IMAGE_REPOSITORY)/$(REPOSITORY_IMAGE):latest
endif


.PHONY: build build-db-seed build-dev clean clean-all clean-image clean-images \
	clean-seed-image depends docker-build format-py format-ui lint-py lint-ui publish \
	rebuild-db-seed run-db-migrations run-dev run-web-local update-depends \
	clean-local-uploads test test-py test-unit test-unit-no-coverage test-api test-api-verbose \
	test-api-clean test-ui test-ui-unit test-ui-functional test-ui-functional-only \
	update-version ui-depends ci docker-snyk-check

# dependency targets

depends: 
	$(POETRY_VARS) $(POETRY) install --no-root

update-depends:
	$(POETRY_VARS) $(POETRY) update

# Targets for building containers

# prod
build: docker-build ## Build the Docker image for production

docker-build: ## Build the Docker image
ifeq ($(VERSION),)
	$(error Cannot build docker image(s), VERSION argument was not provided.  EX: make build -e VERSION=<version>)
endif
	$(DOCKER) buildx build --platform=$(PLATFORMS) $(DOCKER_BUILD_ARGS) --build-arg build_for=prod -t $(IMAGE_REPOSITORY)/$(REPOSITORY_IMAGE):$(VERSION) .

# dev

build-dev: ## Build the development Docker image
	$(DOCKER) build $(DOCKER_BUILD_ARGS) --build-arg build_for=dev -t $(DOCKER_IMAGE):$(DOCKER_IMAGE_TAG_DEV) .

build-ci: ## Build the development Docker image
	$(DOCKER) build $(DOCKER_BUILD_ARGS) --build-arg build_for=dev -t $(DOCKER_IMAGE):$(DOCKER_IMAGE_TAG_CI) .

build-db-seed:
	$(DOCKER) build $(DOCKER_BUILD_ARGS) -t $(DOCKER_DB_SEED_IMAGE):$(DOCKER_IMAGE_TAG_DEV) deploy/docker-local

rebuild-db-seed: 
	$(DOCKER) build $(DOCKER_BUILD_ARGS) -t $(DOCKER_DB_SEED_IMAGE):$(DOCKER_IMAGE_TAG_DEV) --no-cache deploy/docker-local

# Targets for publishing containers

publish: ## Build and publish the Docker images
	$(MAKE) build DOCKER_BUILD_ARGS+="--push"

# Targets for running the app

run-dev: build-dev build-db-seed run-dev-no-build ## Run the development environment

run-dev-no-build: ## Run the development environment without building the Docker image
	docker compose --project-directory deploy/docker-local up

run-web-local:
	pushd ./ui && ng serve --ssl --ssl-key ../deploy/docker-local/certs/localhost.decrypted.key --ssl-cert ../deploy/docker-local/certs/localhost.crt && popd

run-db-migrations:
	./migrate.sh upgrade head

# Testing and Syntax targets

ci: lint test docker-snyk-check ## Run CI pipeline

lint-py: ## Run Python linting
	$(ISORT) --check-only api
	$(PYLINT) --output-format=colorized api
	$(BLACK) --check api

lint-ui: ## Run UI linting
	cd ui && npm run lint && npm run format:check

lint: lint-py lint-ui

format-py: ## Run Python formatters
	$(ISORT) api
	$(BLACK) api

format-ui: ## Run UI formatters
	cd ui && npm run format && npm run lint:fix

format: format-py format-ui ## Run all formatters

ui-depends: ## Install UI dependencies
	cd ui && yarn install

# Unit tests

test: test-py test-ui ## Run all tests

test-py: test-unit test-api ## Run Python tests

test-unit: ## Run python unit tests
	$(PYTEST)

test-no-coverage: ## Run python unit tests without coverage
	$(PYTEST) --no-cov

# UI tests (Angular/Karma)
test-ui: test-ui-unit test-ui-functional ## Run all UI tests

test-ui-unit: ## Run UI unit tests
	cd ui && npm run test:ci

test-ui-functional: build-dev ## Run UI functional tests
	$(DOCKER) compose -f api/tests/api/docker-compose.yml up -d --wait
	-cd ui && npm run test:functional
	$(DOCKER) compose -f api/tests/api/docker-compose.yml down -v --remove-orphans

test-ui-functional-only:
	cd ui && npm run test:functional


# Functional API tests (requires Docker)

test-api: build-dev ## Run API integration tests
	cd api/tests/api && $(PYTEST) -v

test-api-verbose: build-dev ## Run API integration tests with verbose output
	cd api/tests/api && $(PYTEST) -v -s --log-cli-level=INFO

test-api-clean: ## Clean up API integration tests
	$(DOCKER) compose -f api/tests/api/docker-compose.yml down -v --remove-orphans

# Snyk tests

docker-snyk-check: build-ci ## Run Snyk container test (requires SNYK_TOKEN, snyk on PATH)
	snyk container test $(DOCKER_IMAGE):$(DOCKER_IMAGE_TAG_CI) \
		--severity-threshold=high \
		--project-name=brewhouse-manager:main \
		--file=./Dockerfile \
		--platform=$$($(DOCKER) inspect $(DOCKER_IMAGE):$(DOCKER_IMAGE_TAG_CI) --format='{{.Os}}/{{.Architecture}}') \
		--exclude-base-image-vulns

# Migrations

create-migration: ## Create a new migration
	pushd ./api && ./migrate.sh create $@ && popd

# Version management

update-version: ## Update the version number
ifeq ($(VERSION),)
	$(error VERSION argument is required. Usage: make update-version VERSION=x.y.z)
endif
	./scripts/update-version.sh $(VERSION)

# Clean up targets

clean: ## Stop and remove the Docker containers
	docker compose --project-directory deploy/docker-local down --volumes

clean-image: ## Remove the Docker image
	docker rmi $(DOCKER_IMAGE):$(DOCKER_IMAGE_TAG_DEV)
	docker rmi $(DOCKER_IMAGE):$(DOCKER_IMAGE_TAG_CI)

clean-seed-image: ## Remove the seed Docker image
	docker rmi $(DOCKER_DB_SEED_IMAGE):$(DOCKER_IMAGE_TAG_DEV)

clean-images: clean-image clean-seed-image ## Remove all Docker images

clean-local-uploads: ## Remove the local uploads directory
	rm -r ./deploy/docker-local/uploads/*

clean-db: ## Remove the database file
	rm -rf ./deploy/docker-local/data

clean-all: clean clean-images clean-local-uploads clean-db ## Remove all Docker images, local uploads and database file


help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}'

.DEFAULT_GOAL := help