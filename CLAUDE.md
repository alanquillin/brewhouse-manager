# Brewhouse Manager

A homebrew tap management system with a FastAPI backend, Angular frontend, and PostgreSQL database.

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2
- **Frontend**: Angular 21, Angular Material, Bootstrap 5.3, RxJS
- **Database**: PostgreSQL 17, Alembic migrations
- **Tooling**: Poetry (Python deps), npm (UI deps), mise (runtime versions via `.tool-versions`)
- **Docker**: Multi-stage build (node + python), docker-compose for local dev

## Project Structure

```
api/                    # FastAPI backend
  api.py                # App entry point, middleware, router registration
  db/                   # SQLAlchemy models (one file per entity)
  db_migrations/        # Alembic migration scripts
  routers/              # FastAPI route handlers
  services/             # Business logic / response transformation
  schemas/              # Pydantic request/response models
  lib/                  # Shared libraries (config, logging, tap monitors, units)
  dependencies/         # FastAPI dependency injection (auth, db session)
  tests/
    unit/               # Unit tests (no Docker required)
    api/                # Functional tests (Docker required, has own docker-compose.yml)
config/                 # App configuration
  default.json          # Default config with type schema
ui/                     # Angular frontend
  src/app/
    _components/        # Shared components (header, footer, file-uploader)
    _dialogs/           # Material dialog components
    _services/          # Angular services (data, settings, auth)
    _directives/        # Custom directives
    _guards/            # Route guards
    models/             # TypeScript models
    manage/             # Admin management pages
    location/           # Location display page
deploy/                 # Docker compose files for local dev
```

## Common Commands

```bash
# Dependencies
make depends                 # Install Python deps via Poetry
cd ui && npm ci              # Install UI deps

# Running locally
make run-dev                 # Full Docker stack (builds images + docker-compose up)

# Testing
make test                    # All tests (Python unit + functional, UI unit + functional)
make test-unit               # Python unit tests only (fast, no Docker)
make test-api                # Python functional tests (needs Docker)
make test-ui-unit            # Angular unit tests
make test-ui-functional      # Angular functional tests (needs Docker)

# Formatting & Linting
make format                  # Run all formatters (isort, black, prettier, eslint --fix)
make lint                    # Run all linters (isort, pylint, black, eslint, prettier)

# Docker
make build-dev               # Build dev Docker image

# Database
make create-migration        # Create a new Alembic migration

# Clean up
make clean-all               # Stops running containers, cleans up all docker images, local uploads and database files
```

## Testing

- **Python unit tests**: `make test-unit` — runs `pytest` on `api/tests/unit/`
  - 80% coverage minimum enforced in `pyproject.toml`
  - Use `.venv/bin/python -m pytest api/tests/unit/path/to/test.py -v` to run specific tests
  - Helpers: `create_mock_request()`, `create_mock_auth_user()`, `create_mock_tap_monitor()`
  - Pattern: `run_async()` wrapper for testing async functions in sync test methods
  - Mock `AsyncClient` with `_make_mock_http_client()` / `_make_mock_response()` helpers
- **Python functional tests**: `make test-api` — requires Docker (builds image, runs compose)
  - Seed data in `api/tests/api/seed_data.py` with fixed UUIDs
  - `conftest.py` manages Docker Compose lifecycle automatically
- **UI unit tests**: `make test-ui-unit` — Karma + Jasmine with ChromeHeadless
- **UI functional tests**: `make test-ui-functional` — requires Docker compose running

## Code Style

- **Line length**: 160 characters (Python and TypeScript)
- **Python formatting**: `black` + `isort` (run via `make format-py`)
- **Python linting**: `pylint` (run via `make lint-py`)
- **TypeScript**: `prettier` + `eslint` (run via `make format-ui` / `make lint-ui`)
- Run `make format` before committing

## Architecture Patterns

### Backend

**Database models** inherit from `Base, DictifiableMixin, AuditedMixin, AsyncQueryMethodsMixin`:
- `DictifiableMixin`: `to_dict()` serialization
- `AuditedMixin`: Auto-managed `created_on`, `updated_on`, `created_user`, `updated_user` columns
- `AsyncQueryMethodsMixin`: `query()`, `get_by_pkey()`, `create()`, `update()`, `delete()`
- `@generate_audit_trail` decorator on model classes

**Routers** use FastAPI dependency injection:
- `current_user: AuthUser = Depends(require_user)` or `Depends(require_admin)`
- `db_session: AsyncSession = Depends(get_db_session)`
- Raise `HTTPException` for errors (400, 404, 502)

**Services** are classes with static async methods:
- `transform_response()` converts DB model → camelCase dict for API responses
- Business logic lives here, not in routers

**Schemas** extend `CamelCaseModel` (Pydantic BaseModel with automatic snake_case ↔ camelCase):
- Separate `Create`, `Update`, `Response` schema variants per entity
- `populate_by_name=True` accepts both casings

**Auth dependency chain**: `get_optional_user()` → `require_user()` (401) → `require_admin()` (403)

**Config**: `Config` singleton, reads `config/default.json` + env vars with type conversion schema. Access via `CONFIG.get("dotted.key.path")`.

### Frontend

**`EditableBase` pattern**: Models track `editValues` and `changes` separately from display values. Components use `enableEditing()` / `disableEditing()`.

**`_executeSave()` pattern**: Used in `taps.component.ts` and `tap-monitors.component.ts` to extract save logic from dialog callbacks.

**Destructive actions**: Use native `confirm()` dialog, not Material dialog.

**Data service**: `DataService` in `_services/data.service.ts` — all API calls go through here with `catchError` → `getError()` pattern.

### Tap Monitor Integration

`TapMonitorBase` in `api/lib/tap_monitors/` is the base class for device integrations (Kegtron Pro, Kegtron Gen1, Plaato, etc.). Each implementation provides:
- `supports_discovery()`, `reports_online_status()` — static capability flags
- `get()`, `get_all()` — data retrieval
- `discover()` — device discovery
- `is_online()` — connectivity check
- Device-specific methods (e.g., `reset_volume()`)

Enabled/disabled via config: `tap_monitors.<type>.enabled`.

## CI

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on PRs to `main`:
- Uses `mise` to install Python, Node, and Poetry from `.tool-versions`
- Installs deps, builds dev Docker image, runs `make test` and `make lint`
