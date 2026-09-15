# Brewhouse Manager

A homebrew tap management system with a FastAPI backend, Angular frontend, and PostgreSQL database.

## Agent Behavior Rules

**NEVER commit or push changes without explicit user instruction.** This applies to all tasks, including code reviews, lint fixes, refactors, and bug fixes. The user must review all changes before they are committed or pushed.

- Do not run `git commit` unless the user explicitly asks you to commit.
- Do not run `git push` unless the user explicitly asks you to push.
- Do not run `gh pr create` or any GitHub CLI command that publishes or modifies remote state unless the user explicitly asks.
- After making file edits, stop and let the user review the diff before taking any git actions.

## Tech Stack

- **Backend**: Python 3.14, FastAPI, SQLAlchemy 2.0 (async), Pydantic v2
- **Frontend**: Angular 22, Angular Material, Bootstrap 5.3, RxJS
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

### Manual/visual UI verification against the local dev stack

There's no `chromium-cli`/Playwright installed in the sandbox, but a real Chrome exists at `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` (macOS). To actually see a UI change rendered (not just pass unit tests):

1. Rebuild the dev image and recreate the `web` container — this is fast (a few seconds) because Docker layer caching means only the changed `ui/src` → `pnpm run build:dev` layer and the final `COPY` layers re-run:
   ```bash
   docker build --build-arg build_for=dev -t brewhouse-manager:dev .
   docker compose --project-directory deploy/docker-local up -d --force-recreate web
   ```
   If other containers (postgres/nginx) aren't listed as `Up` afterward, run `docker compose --project-directory deploy/docker-local up -d` (no `--force-recreate`) once more to bring the rest of the stack back.
2. The stack serves over `https://localhost:8443` (self-signed cert) with nginx in front of the `web` container on port 5001.
3. The Postgres volume persists real accumulated data across sessions (not just `seed_data.py` fixtures) — location slugs `sample-2-tap-taproom`, `sample-3-tap-taproom`, `sample-4-tap-taproom` exist under routes `/view/<slug>` (public dashboard) and login is `alanquillin@gmail.com` / `foo` (from `deploy/docker-local/my-config.json`, `auth.initial_user`) for `/manage/*` admin pages.
4. Use `puppeteer-core` (install with `npm install puppeteer-core` in a scratch dir — no need to download a bundled Chromium) launched with `executablePath` pointed at the system Chrome and `--ignore-certificate-errors` in `args`. `page.setRequestInterception(true)` lets you mock/delay/force-fail specific API responses (e.g. the tap-monitor `/data` polling endpoint) to reach UI states — loading spinners, error banners — that aren't reproducible with whatever real data happens to be in the dev DB at the time.

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
    return asyncio.run(coro)
```
This is defined locally in each test file that uses it.

**Python 3.14 gotcha**: this helper used to be `asyncio.get_event_loop().run_until_complete(coro)`. As of Python 3.14, `asyncio.get_event_loop()` no longer implicitly creates an event loop when none exists in the current thread — it raises `RuntimeError: There is no current event loop in thread 'MainThread'` instead. All 39 `run_async` definitions across `api/tests/unit/` were switched to `asyncio.run(coro)` for the 3.14 upgrade. If a test needs to build a `Task`/`Future` (e.g. via `asyncio.ensure_future()`) before calling `run_async(...)`, that construction must happen *inside* a coroutine passed to `run_async`, not beforehand at the top level of the test — `ensure_future()` also requires a running loop and will hit the same `RuntimeError` otherwise (see `test_shutdown_cancels_tcp_task` in `api/tests/unit/test_app.py` for the pattern: wrap the setup + the `await app.shutdown()` call together in a local `async def` and pass that to `run_async`).

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

**Programmatic `matTooltip` toggle (hover-or-click)**: To make a tooltip open on both hover and click/tap (not just hover), grab a template reference to the directive and call `.toggle()`:
```html
<span
  tabindex="0"
  #myTooltip="matTooltip"
  matTooltip="..."
  (click)="myTooltip.toggle()"
  (keyup.enter)="myTooltip.toggle()"
>...</span>
```
`tabindex="0"` + `(keyup.enter)` are required to satisfy `click-events-have-key-events` / `interactive-supports-focus` on the non-button element. Used throughout `location.component.html` for the tap online/offline/active/error status indicators and in `taps.component.html` for the tap-monitor warning icon.

**`mat-card-header` does not stretch its content to full width by default**: `mat-card-subtitle`'s wrapping `.mat-mdc-card-header-text` div is a flex item with no `flex-grow`, so a custom `display:flex; justify-content:space-between` row placed inside `mat-card-subtitle` will only span the width of its content, not the card. To right-justify something in the header, add a scoped override:
```scss
:host ::ng-deep .tap-card > mat-card-header .mat-mdc-card-header-text {
  flex: 1;
  width: 100%;
}
```
(see `location.component.scss`).

### Tap Monitor Integration

`TapMonitorBase` in `api/lib/tap_monitors/` is the base class for device integrations (Kegtron Pro, Kegtron Gen1, Plaato, etc.). Each implementation provides:
- `supports_discovery()`, `reports_online_status()` — static capability flags
- `get()`, `get_all()` — data retrieval
- `discover()` — device discovery
- `is_online()` — connectivity check
- Device-specific methods (e.g., `reset_volume()`)

Enabled/disabled via config: `tap_monitors.<type>.enabled`.

**`reports_online_status()` is a static per-type capability flag**, independent of any single poll's success/failure. UI code should never assume every tap monitor supports online/offline reporting — `getTapMonitorsForLocation` / `TapMonitor.reportsOnlineStatus` (mapped from `get_types()` in `lib/tap_monitors/__init__.py`) tells you whether to show real online/offline state or a generic "Active" state instead. `open-plaato-keg` and `keg-volume-monitor-weight` are examples of types that return `False` here.

**`lastUpdatedOn` (last-connected timestamp) is only implemented for `plaato-keg`**: its `get_all()` (`lib/tap_monitors/plaato_keg.py`) is the only adapter that populates the `lastUpdatedOn` field from a DB-cached device row. `kegtron.py`, `kegtron_gen1.py`, and `keg_volume_monitor.py` never set it, so their dashboard "last connected" tooltip will always be empty — this is a real gap, not a mapping bug, if a future task wants to add last-seen tracking for those types it needs new extraction logic in each adapter's `parse_resp()`/`get_all()`.

## Docker Build Notes

### Multi-stage layout

The build uses four stages:

| Stage | Base | Purpose |
|---|---|---|
| `node-base` | `node:26.5-trixie` | Install pnpm/Angular CLI, install UI deps |
| `python-build` | `python:3.14-slim-trixie` | Install Poetry + build tools, compile `.venv` |
| `node-build` | `node-base` | Compile Angular app |
| `final` | `python:3.14-slim-trixie` (clean) | Runtime image — copies `.venv` + app code only |

**Poetry is not present in the final image.** It lives only in `python-build`. The `.venv` directory (at `/.venv` in the container) is the only Python artifact copied into `final` via `COPY --from=python-build /.venv /.venv`. This keeps poetry, its transitive deps (e.g. msgpack), build tools, and compilers out of the shipped image.

Because poetry is absent at runtime, **all scripts that previously used `poetry run` must use the venv directly**:
- `entrypoint.sh` activates the venv with `. /.venv/bin/activate` before calling `migrate.sh` and `python app.py`.
- `api/migrate.sh` resolves `ALEMBIC` and `PYTHON` to `/.venv/bin/alembic` / `/.venv/bin/python` when those paths exist (i.e., inside the container), and falls back to bare commands for local dev where the venv is at a different path or already activated.
- `deploy/docker-local/Dockerfile` CMD uses `. /.venv/bin/activate && ...` for the seed container.

If a new script or service needs to run Python/alembic inside the container, use `/.venv/bin/python` or activate the venv — do not reinstall poetry.

### Removing perl (CVE remediation)

`python:3.14-slim-trixie` (the base for the `final` stage) ships with `perl` and `perl-base`. They are not needed at runtime and must be purged from the `final` stage:

```dockerfile
RUN apt-get purge -y --auto-remove --allow-remove-essential perl perl-base
```

`--allow-remove-essential` is required because apt marks `perl-base` essential in Debian. It is safe here because nothing in the runtime app (Python/FastAPI) depends on perl, and this is the only apt operation in `final`.

Do **not** attempt to purge perl from `node-base` — the non-slim Node image has many packages (e.g. `x11-common`, `ucf`) whose post-removal scripts are written in Perl; removing `perl-base` there causes `dpkg` errors during the build.

Purging perl from `python-build` is unnecessary because `python-build` is a build-only stage — its layers do not ship to the final image. Only the `final` stage needs the purge.

### `addgroup` vs `groupadd`

`addgroup` (from the Debian `adduser` package) is a **Perl script**. It is not available in `python:3.14-slim-trixie` (which does not ship perl). Calling `addgroup` in the `final` stage will fail with `addgroup: not found`.

Use `groupadd` instead — it is a C binary from the `shadow` package and does not require perl:

```dockerfile
# Correct (C binary, no perl dependency)
RUN groupadd --gid 10000 app && \
    useradd --gid app --shell /sbin/nologin --no-create-home --uid 10000 app

# Wrong after perl removal (Perl script)
RUN addgroup app --gid 10000 && useradd ...
```

### pip version floor

Both the `python-build` and `final` stages must pin pip to `>=25.3` to avoid CVEs in older pip releases. Each stage starts from `python:3.14-slim-trixie` independently, so each needs its own upgrade:

```dockerfile
# python-build stage
RUN pip install -U "pip>=25.3" setuptools wheel

# final stage (before any other pip or venv usage)
RUN pip install -U "pip>=25.3"
```

Do not rely on the `.venv` copy from `python-build` to carry the pip version into `final` — the system pip in `final` is separate from the venv pip and is the one used by bare `pip` calls in that stage.

### Runtime library assumptions in the final image

The `final` stage has no `apt-get install` — it starts from a clean `python:3.14-slim-trixie` and only receives the `.venv`. Any C extension in the venv that dynamically links to a system library not present in the base image will fail at runtime with a "shared library not found" error.

Currently safe because:
- `psycopg2-binary` bundles its own `libpq.so` (no system `libpq5` needed).
- `cryptography` downloads a manylinux wheel on Linux that statically bundles OpenSSL.
- `libssl3` and `libffi8` are present in the Python base image (Python itself needs them).

If a new dependency is added that links to a system library outside this set (e.g., `libpq5`, `libxml2`, `libcurl`), add the **runtime** package (not the `-dev` variant) to the `final` stage's `apt-get install`.

## CI

GitHub Actions workflow (`.github/workflows/ci.yml`) runs on PRs to `main`:
- Uses `mise` to install Python, Node, and Poetry from `mise.toml`
- Installs deps, builds dev Docker image, runs `make test` and `make lint`

**Action pinning convention**: every `uses:` is pinned to a full commit SHA with the human-readable tag as a trailing comment (`uses: owner/repo@<40-char-sha> # vX.Y.Z`), not a floating tag. To bump one, resolve the new tag to its commit SHA first (annotated tags need dereferencing — `gh api repos/<owner>/<repo>/git/refs/tags/<tag>` gives an object; if `.object.type` is `"tag"` (not `"commit"`), follow up with `gh api repos/<owner>/<repo>/git/tags/<that-sha>` to get the actual commit SHA it points to) rather than trusting a changelog/release page's stated SHA. As of the last check: `actions/checkout` v7.0.1, `jdx/mise-action` v4.3.0, `pnpm/action-setup` v6.1.0 — all confirmed to have no breaking changes affecting this workflow's usage (no `with:` inputs on checkout; `install: true` on mise-action; `version: 11` on pnpm/action-setup, which v6 added native support for).

---

## Dependency & Tooling Notes

### Package Manager (mise)

The project uses `mise.toml` (not `.tool-versions`) for runtime version pinning. Current pinned versions:
- Python 3.14.7
- Node 26.8.2
- Poetry 2.4.3
- Snyk 1.1307.2

Check for newer patch/minor releases with `mise latest <tool>` (compares against the tool's own upstream releases, unlike `mise outdated`, which only flags tools pinned to `"latest"` in the *global* `~/.config/mise/config.toml` — it ignores exact-pinned versions in the project's `mise.toml`).

**Upgrading Python or Node**: `pyproject.toml`'s `python = ">=3.12,<4.0"` constraint and Angular CLI 22's own `engines.node` (`^22.22.3 || ^24.15.0 || >=26.0.0`) already tolerate new major versions without a pin change there — the actual work is bumping `mise.toml` and the two `FROM` lines in `Dockerfile` (see Docker Build Notes table above), then `poetry lock` (Python) or `pnpm install` (Node) to refresh the lockfile. Also bump `@types/node` in `ui/package.json` to match the new Node major for accurate typings. Check for prebuilt wheels (`cp<version>` tags on PyPI) before assuming a pinned C-extension dependency (`cryptography`, `psycopg2-binary`, `asyncpg`, `uvloop`, `httptools`) will install cleanly on a very new Python — as of the 3.14 upgrade all of these already had wheels available.

**PATH doesn't refresh automatically after bumping `mise.toml` pins mid-session**: mise's shell integration updates `PATH` via a `chpwd`/`precmd` hook that fires on interactive directory changes — it does **not** re-fire inside a single non-interactive shell invocation (e.g. Claude Code's Bash tool re-sourcing the profile per command). After editing `mise.toml` and running `mise install`, a bare `which poetry`/`poetry --version` in the same session can still resolve the *old* installed version even though `mise current` correctly reports the new one. Force a refresh with `eval "$(mise activate bash)"` (ignore the harmless `no such hash table element` warnings it prints), or sidestep it entirely with `mise exec -- <cmd>`, before verifying or testing an upgraded tool.

### Dependency upgrade heuristic (Python/poetry, mise tools, GHA actions)

When asked to upgrade "what's safe": a bump is safe by default only if it stays within the *existing* version constraint (caret range in `pyproject.toml`, or same major version for exactly-pinned tools/actions) — run the test suite (and `make lint-py` for isort/pylint) after, not just before. Two extra cases:
- **Exactly-pinned packages/tools** (no `^`/`~`, e.g. `psycopg2-binary`, `cryptography` in `pyproject.toml`, or any `mise.toml` entry) never move via `poetry update` / `mise install` alone — the pin itself must be edited first.
- **Major version bumps** (`cryptography` 49→50, `isort` 8→9, `uvicorn` 0.52→0.53, or any GitHub Action's major tag) are not auto-applied even if the exact pin is edited and tests pass — check the changelog/release notes for breaking changes relevant to actual usage first (tests passing doesn't prove a removed/renamed CLI flag or changed default isn't lurking). If clean, upgrade and re-verify; if in doubt, leave pinned and report the option back.

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
