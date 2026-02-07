# Functional Tests

This directory contains functional tests for the Brewhouse Manager API. These tests run against a real API instance in Docker containers, with the database starting from a consistent known state.

## Prerequisites

1. **Docker and Docker Compose**: Ensure Docker is installed and running on your machine.

2. **Build the application image**: Before running functional tests, you must build the Docker image:

   ```bash
   # From the repository root
   docker build -t brewhouse-manager:dev --build-arg build_for=dev .
   ```

## Running Functional Tests

### Run all functional tests

```bash
# From the api directory
pytest tests/functional/ -v
```

### Run specific test files

```bash
pytest tests/functional/test_locations.py -v
pytest tests/functional/test_beers.py -v
pytest tests/functional/test_taps.py -v
pytest tests/functional/test_tap_monitors.py -v
```

### Run with fresh database reset between tests

By default, tests share the same database state within a session. To reset the database for specific tests that require a clean state, use the `reset_database` fixture:

```python
def test_something_that_needs_clean_state(self, api_client, api_base_url, reset_database):
    # Database is fresh for this test
    ...
```

## Architecture

### Docker Compose Services

The functional tests use a dedicated `docker-compose.yml` with:

- **postgres**: PostgreSQL 17 database with tmpfs storage for fast tests
- **db-init**: Initializes and seeds the database with test data
- **web**: The Brewhouse Manager API service

### Test Data

Test data is defined in `seed_data.py` with fixed UUIDs, allowing predictable assertions:

- **3 Locations**: main-taproom, secondary-taproom, empty-taproom
- **4 Beers**: IPA, Stout, Lager, Wheat
- **2 Beverages**: Cold Brew, Soda
- **4 Tap Monitors**: Various monitor types
- **5 Batches**: Connected to beers/beverages
- **5 Taps**: With various configurations
- **2 Users**: Admin and regular user

### Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `docker_services` | session | Starts/stops Docker Compose services |
| `api_base_url` | session | Returns the API base URL |
| `api_client` | session | Unauthenticated requests.Session |
| `admin_api_client` | session | Authenticated admin requests.Session |
| `user_api_client` | session | Authenticated regular user requests.Session |
| `reset_database` | function | Resets DB to known state before the test |

## Writing New Tests

### Basic Test Structure

```python
from .seed_data import LOCATION_MAIN_ID, BEERS

class TestMyEndpoint:
    """Tests for the endpoint."""

    def test_basic_functionality(self, api_client, api_base_url):
        """Test description."""
        response = api_client.get(f"{api_base_url}/my_endpoint")

        assert response.status_code == 200
        data = response.json()
        # assertions...
```

### Using Seed Data IDs

Import the known IDs from `seed_data.py` for predictable assertions:

```python
from .seed_data import (
    BEER_IPA_ID,
    LOCATION_MAIN_ID,
    TAP_MONITOR_1_ID,
)

def test_get_specific_beer(self, api_client, api_base_url):
    response = api_client.get(f"{api_base_url}/beers/{BEER_IPA_ID}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test IPA"
```

### Test Isolation

For tests that modify data and need isolation:

```python
def test_that_modifies_data(self, api_client, api_base_url, reset_database):
    # Database is reset before this test runs
    # Changes made here won't affect other tests
    ...
```

## Configuration

### Environment Variables

The Docker Compose file sets these environment variables for the test environment:

- `ENV=test`
- `AUTH_ENABLED=false` - Disables auth for easier testing
- `TAP_MONITORS_PLAATO_KEG_ENABLED=false`
- `TAP_MONITORS_OPEN_PLAATO_KEG_ENABLED=true`
- `TAP_MONITORS_KEG_VOLUME_MONITORS_ENABLED=true`

### Ports

| Service | Host Port | Container Port |
|---------|-----------|----------------|
| API | 5050 | 5000 |
| API (Plaato) | 5051 | 5001 |
| PostgreSQL | 5433 | 5432 |

## Troubleshooting

### Tests hang during startup

Check if the Docker image is built:
```bash
docker images | grep brewhouse-manager
```

If not found, build it:
```bash
docker build -t brewhouse-manager:dev --build-arg build_for=dev .
```

### Database connection errors

Check if PostgreSQL is running:
```bash
docker compose -f tests/functional/docker-compose.yml ps
docker compose -f tests/functional/docker-compose.yml logs postgres
```

### API not responding

Check API logs:
```bash
docker compose -f tests/functional/docker-compose.yml logs web
```

### Clean up stuck containers

```bash
docker compose -f tests/functional/docker-compose.yml down -v --remove-orphans
```

## Manual Testing

You can also start the services manually for interactive testing:

```bash
# Start services
docker compose -f tests/functional/docker-compose.yml up -d

# Check status
docker compose -f tests/functional/docker-compose.yml ps

# View logs
docker compose -f tests/functional/docker-compose.yml logs -f web

# Stop services
docker compose -f tests/functional/docker-compose.yml down -v
```

Then access the API at `http://localhost:5050/api/v1/`.
