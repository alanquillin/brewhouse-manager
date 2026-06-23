# Brewhouse Manager

A homebrew tap management system with a FastAPI backend, Angular frontend, and PostgreSQL database.

## Agent Behavior Rules

**NEVER commit or push changes without explicit user instruction.** This applies to all tasks, including code reviews, lint fixes, refactors, and bug fixes. The user must review all changes before they are committed or pushed.

- Do not run `git commit` unless the user explicitly asks you to commit.
- Do not run `git push` unless the user explicitly asks you to push.
- Do not run `gh pr create` or any GitHub CLI command that publishes or modifies remote state unless the user explicitly asks.
- After making file edits, stop and let the user review the diff before taking any git actions.

## Tech Stack

- **Backend**: Python 3.11, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2
- **Frontend**: Angular 21, Angular Material, Bootstrap 5.3, RxJS
- **Database**: PostgreSQL 17, Alembic migrations
- **Tooling**: Poetry 2.x (Python deps), pnpm (UI deps), mise (runtime versions via `mise.toml`)
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
make ui-depends              # Install UI deps via pnpm (cd ui && pnpm install)

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
  - 80% coverage minimum enforced in `pyproject.toml` (exit code 1 from coverage miss is OK if all tests pass)
  - Run specific tests: `.venv/bin/python -m pytest api/tests/unit/path/to/test.py -v`
  - Helpers: `create_mock_request()`, `create_mock_auth_user()`, `create_mock_tap_monitor()`
  - Pattern: `run_async()` wrapper for testing async functions in sync test methods
  - Mock `AsyncClient` with `_make_mock_http_client()` / `_make_mock_response()` helpers
- **Python functional tests**: `make test-api` — requires Docker (builds image, runs compose)
  - Seed data in `api/tests/api/seed_data.py` with fixed UUIDs
  - `conftest.py` manages Docker Compose lifecycle automatically
- **UI unit tests**: `make test-ui-unit` — Karma + Jasmine with ChromeHeadless
- **UI functional tests**: `make test-ui-functional` — requires Docker compose running

### Mocking `awaitable_attrs` (SQLAlchemy async lazy loading)

Production code accesses async-loaded relationships via `await obj.awaitable_attrs.some_attr`. Mocking this requires a directly awaitable value — **not** a coroutine object and **not** an `AsyncMock` instance.

- **Coroutine objects** warn `RuntimeWarning: coroutine was never awaited` when the test doesn't exercise every mocked attribute.
- **`AsyncMock` instances** raise `TypeError: object AsyncMock can't be used in 'await' expression` — `AsyncMock` is an async *callable*, not an awaitable.

The correct pattern uses a small `_AwaitableValue` helper class (defined inline in each test file that needs it):

```python
class _AwaitableValue:
    __slots__ = ("_value",)

    def __init__(self, value):
        self._value = value

    def __await__(self):
        return self._coro().__await__()

    async def _coro(self):
        return self._value
```

Usage in mock helpers:
```python
mock_tap.awaitable_attrs = MagicMock()
mock_tap.awaitable_attrs.location = _AwaitableValue(location)
mock_tap.awaitable_attrs.on_tap = _AwaitableValue(on_tap)
```

This class is defined at the top of each affected test file (not shared via conftest — conftest is not importable from subdirectory test files because `api/tests/unit/` is not on `sys.path`).

### `run_async` helper

Sync test methods run async production code via:
```python
def run_async(coro):
    return asyncio.get_event_loop().run_until_complete(coro)
```
This is defined locally in each test file that uses it.

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

**Beer/beverage delete cascade pattern**: Deleting a beer or beverage requires a specific multi-step manual cascade (database FKs have no `ON DELETE CASCADE` at the DB level — it's all application-enforced). The correct order, all with `autocommit=False` until the final step:

1. Check for active batches (`archived_on IS NULL`) — raise 409 if any exist
2. For each archived batch: `TapService.clear_on_tap_references_for_batch(session, batch.id, autocommit=False)` — nulls `taps.on_tap_id` before on_tap rows are deleted
3. `BatchLocationsDB.delete_by(session, batch_id=..., autocommit=False)`
4. `OnTapDB.delete_by(session, batch_id=..., autocommit=False)`
5. `BatchOverridesDB.delete_by(session, batch_id=..., autocommit=False)`
6. `BatchesDB.delete_by(session, beer_id=..., autocommit=False)` (or `beverage_id=...`)
7. `ImageTransitionsDB.delete_by(session, beer_id=..., autocommit=False)`
8. `BeersDB.delete(session, beer.id)` — default `autocommit=True` commits the whole transaction

`TapService.clear_on_tap_references_for_batch` is in `api/services/taps.py`.

**Config**: `Config` singleton, reads `config/default.json` + env vars with type conversion schema. Access via `CONFIG.get("dotted.key.path")`.

### Frontend

**`EditableBase` pattern**: Models track `editValues` and `changes` separately from display values. Components use `enableEditing()` / `disableEditing()`.

**`_executeSave()` pattern**: Used in `taps.component.ts` and `tap-monitors.component.ts` to extract save logic from dialog callbacks.

**Destructive actions**: Use native `confirm()` dialog, not Material dialog.

**Data service**: `DataService` in `_services/data.service.ts` — all API calls go through here with `catchError` → `getError()` pattern.

**Dependency injection**: Use `inject()` function, not constructor parameter injection. This is enforced by `@angular-eslint/prefer-inject`. Example:
```typescript
// Correct
readonly dataService = inject(DataService);

// Wrong — triggers lint warning
constructor(private dataService: DataService) {}
```

**Template control flow**: Use Angular's built-in `@if` / `@for` / `@switch` blocks, not structural directives (`*ngIf`, `*ngFor`). Enforced by `@angular-eslint/template/prefer-control-flow`.

**Clickable non-button elements**: Any element with `(click)` that is not a `<button>` or `<a href="...">` must also have `tabindex="0"` and a `(keyup.enter)` handler. Enforced by `@angular-eslint/template/click-events-have-key-events` and `@angular-eslint/template/interactive-supports-focus`.

**Empty lifecycle methods**: Remove empty `ngOnInit()`, `ngOnDestroy()` etc. rather than leaving them as no-ops. Also remove `implements OnInit` and the corresponding import. If a spec file tests for the method's existence, remove those test cases too.

**Creating fresh service instances in specs** (after `inject()` migration): `new MyService(dep)` no longer compiles since there are no constructor parameters. Use `TestBed.runInInjectionContext(() => new MyService())` to create a fresh instance within the active injector:
```typescript
const freshService = TestBed.runInInjectionContext(() => new MyService());
```

**Delete beer/beverage UI pattern**: `deleteBeer` / `deleteBeverage` check local `beerBatches[beer.id]` / `beverageBatches[beverage.id]` data *before* calling the API. If any batch has no `archivedOn` (active), call `displayError()` and return without hitting the API. If all batches are archived, include the count in the `confirm()` message. The backend also enforces the same rule (returns 409), so the UI check is a fast-fail UX convenience, not the only guard.

**`beverageBatches` / `beerBatches` lookup gotcha**: These maps only contain entries for existing (already-saved) entities. When the add flow is active, `modifyBeverage.id` / `modifyBeer.id` is `undefined`, so `beverageBatches[undefined]` is `undefined` — accessing `.length` on it will throw. Always guard template lookups with optional chaining:
```html
@if ((beverageBatches[modifyBeverage.id]?.length ?? 0) > 0 && !loadingBatches) {
```

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
- Uses `mise` to install Python, Node, and Poetry from `mise.toml`
- Installs deps, builds dev Docker image, runs `make test` and `make lint`

---

## Dependency & Tooling Notes

### Package Manager (mise)

The project uses `mise.toml` (not `.tool-versions`) for runtime version pinning. Current pinned versions:
- Python 3.11.13
- Node 24.15.0
- Poetry 2.4.1
- Snyk 1.1304.2

### pnpm (UI package manager)

The UI uses pnpm (v11). The lockfile is `ui/pnpm-lock.yaml`; `yarn.lock` and `package-lock.json` are gone.

**pnpm v11 build script approval**: pnpm v11 requires explicit per-package approval to run postinstall scripts. Native packages (`esbuild`, `@parcel/watcher`, `lmdb`, `msgpackr-extract`) are approved in `ui/pnpm-workspace.yaml` via `allowBuilds`. Do not remove that file — without it, `pnpm install` exits 1 in Docker and CI. If new native packages are added that need build scripts, add them to `allowBuilds` in `ui/pnpm-workspace.yaml` as well. Also, `ui/pnpm-workspace.yaml` must be copied into the Docker image (it is in the `COPY` list in `Dockerfile`).

Yarn references in `pnpm-lock.yaml` (e.g. `engines: { yarn: ... }` and `@yarnpkg/lockfile`) are upstream package metadata — not a sign that yarn is being used.

### Poetry 2.x

The project is on Poetry 2.x. Dev dependencies are declared under `[tool.poetry.group.dev.dependencies]` (not the old `[tool.poetry.dev-dependencies]`). The lock file format changed between Poetry 1.x and 2.x — regenerate with `rm poetry.lock && poetry install` after any upgrade.

---

## SQLAlchemy Relationship Patterns

### `backref` vs `back_populates`

**Do not use `backref=backref("Name", ...)` alongside an explicit reverse relationship.** This creates two relationships pointing at the same FK and triggers `SAWarning: relationship '...' will copy column ... which conflicts with relationship(s)`.

The correct pattern is explicit `back_populates` on both sides, with `cascade` on the parent:

```python
# Parent (e.g. beverages.py)
batches = relationship("Batches", back_populates="beverage", cascade="all, delete")

# Child (e.g. batches.py)
beverage = relationship(beverages.Beverages, back_populates="batches")
```

This has been applied to: `Beers.batches` ↔ `Batches.beer`, `Beverages.batches` ↔ `Batches.beverage`.

### Circular import: `db.batches` must be imported before `db.batch_locations`

`batches.py` accesses `batch_locations.BatchLocations.__table__` at class-definition time (inside the `locations` secondary `relationship`). If any router imports `db.batch_locations` *before* `db.batches`, Python raises `AttributeError: partially initialized module 'db.batch_locations' has no attribute 'BatchLocations'`.

Fix: guard the import order with `# isort: off/on` in any router that imports both:

```python
# isort: off
# fmt: off
from db.batches import Batches as BatchesDB  # pylint: disable=wrong-import-position
from db.batch_locations import BatchLocations as BatchLocationsDB
from db.batch_overrides import BatchOverrides as BatchOverridesDB
# isort: on
# fmt: on
```

This pattern already appears in `routers/batches.py` and was added to `routers/beers.py` and `routers/beverages.py`. Isort would otherwise sort `batch_locations` before `batches` alphabetically.

### Secondary (many-to-many) + direct FK relationships on the same table

When a model has both a secondary many-to-many relationship (e.g. `Batches.locations` through `batch_locations`) AND the join-table model (`BatchLocations`) has direct FK relationships with `backref`, SQLAlchemy will warn about overlapping writes. Fix: add `overlaps="BatchLocations,batch,location"` to the secondary relationship:

```python
# batches.py
locations = relationship(
    locations.Locations,
    secondary=batch_locations.BatchLocations.__table__,
    overlaps="BatchLocations,batch,location",
)
```

---

## FastAPI / Starlette Compatibility (0.137.x / Starlette 1.3.x)

### `app.routes` now contains `_IncludedRouter` objects

In FastAPI 0.137+ / Starlette 1.3+, `app.include_router(...)` no longer flattens routes into `app.routes`. Instead, each `include_router` call produces an `_IncludedRouter` object (no `path` attribute). Direct routes (health check, OpenAPI endpoints, catch-all) still have `path`.

To collect all registered paths (e.g. in tests), walk `effective_route_contexts()`:

```python
def _collect_route_paths(app):
    paths = []
    for route in app.routes:
        if hasattr(route, "effective_route_contexts"):
            for ctx in route.effective_route_contexts():
                if hasattr(ctx, "path"):
                    paths.append(ctx.path)
        elif hasattr(route, "path"):
            paths.append(route.path)
    return paths
```

This is implemented in `api/tests/unit/test_api.py`.
