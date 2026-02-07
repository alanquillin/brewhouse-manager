"""
Pytest configuration for functional tests.

This module provides fixtures for running functional tests against a real API
instance in Docker containers. The database starts from a consistent known state.
"""

import os
import subprocess
import sys
import time
from typing import Generator

import pytest
import requests

# Test configuration
DOCKER_COMPOSE_FILE = os.path.join(os.path.dirname(__file__), "docker-compose.yml")
API_BASE_URL = "http://localhost:5050/api/v1"
API_HEALTHZ_URL = f"{API_BASE_URL}/healthz"
STARTUP_TIMEOUT = 120  # seconds
HEALTH_CHECK_INTERVAL = 2  # seconds


class DockerComposeManager:
    """Manages Docker Compose lifecycle for functional tests."""

    def __init__(self, compose_file: str):
        self.compose_file = compose_file
        self._started = False

    def _run_compose(self, *args, check: bool = True) -> subprocess.CompletedProcess:
        """Run a docker-compose command."""
        cmd = ["docker", "compose", "-f", self.compose_file] + list(args)
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=check
        )

    def build(self):
        """Build the docker images if needed."""
        print("Checking if brewhouse-manager:dev image exists...")
        result = subprocess.run(
            ["docker", "images", "-q", "brewhouse-manager:dev"],
            capture_output=True,
            text=True
        )
        if not result.stdout.strip():
            print("Image not found. Please build the image first:")
            print("  docker build -t brewhouse-manager:dev --build-arg build_for=dev .")
            sys.exit(1)

    def up(self):
        """Start the docker-compose services."""
        if self._started:
            return

        print("Starting Docker Compose services...")
        result = self._run_compose("up", "-d", "--wait", check=False)

        if result.returncode != 0:
            print(f"Failed to start services:\n{result.stderr}")
            self.logs()
            raise RuntimeError("Failed to start Docker Compose services")

        self._started = True
        print("Docker Compose services started")

    def down(self):
        """Stop and remove the docker-compose services."""
        if not self._started:
            return

        print("Stopping Docker Compose services...")
        self._run_compose("down", "-v", "--remove-orphans", check=False)
        self._started = False
        print("Docker Compose services stopped")

    def logs(self, service: str = None):
        """Print logs from services."""
        args = ["logs", "--tail=100"]
        if service:
            args.append(service)
        result = self._run_compose(*args, check=False)
        print(result.stdout)
        if result.stderr:
            print(result.stderr)

    def restart_db_init(self):
        """Restart the db-init service to reset the database."""
        print("Resetting database...")
        # Stop web service first
        self._run_compose("stop", "web", check=False)

        # Restart db-init to reset data
        self._run_compose("rm", "-f", "db-init", check=False)
        result = self._run_compose("up", "-d", "db-init", check=False)
        if result.returncode != 0:
            print(f"Failed to restart db-init: {result.stderr}")
            return False

        # Wait for db-init to complete
        for _ in range(30):
            result = self._run_compose("ps", "-q", "db-init", check=False)
            if not result.stdout.strip():
                break
            time.sleep(1)

        # Start web service again
        self._run_compose("up", "-d", "web", check=False)
        return True


def wait_for_api_ready(timeout: int = STARTUP_TIMEOUT, interval: int = HEALTH_CHECK_INTERVAL) -> bool:
    """Wait for the API to be ready to accept requests."""
    print(f"Waiting for API to be ready at {API_HEALTHZ_URL}...")
    start_time = time.time()

    while time.time() - start_time < timeout:
        try:
            response = requests.get(API_HEALTHZ_URL, timeout=5)
            if response.status_code == 200:
                print("API is ready!")
                return True
        except requests.exceptions.RequestException:
            pass

        time.sleep(interval)

    print(f"API did not become ready within {timeout} seconds")
    return False


# Global docker manager instance
_docker_manager = None


def get_docker_manager() -> DockerComposeManager:
    """Get or create the global docker manager."""
    global _docker_manager
    if _docker_manager is None:
        _docker_manager = DockerComposeManager(DOCKER_COMPOSE_FILE)
    return _docker_manager


@pytest.fixture(scope="session")
def docker_services() -> Generator[DockerComposeManager, None, None]:
    """
    Session-scoped fixture that starts Docker Compose services.

    The services are started once per test session and stopped at the end.
    """
    manager = get_docker_manager()

    # Ensure image exists
    manager.build()

    # Start services
    manager.up()

    # Wait for API to be ready
    if not wait_for_api_ready():
        manager.logs()
        manager.down()
        pytest.fail("API did not start successfully")

    yield manager

    # Cleanup
    manager.down()


@pytest.fixture(scope="function")
def reset_database(docker_services: DockerComposeManager) -> Generator[None, None, None]:
    """
    Function-scoped fixture that resets the database before each test.

    Use this fixture when you need a completely fresh database state.
    """
    # Reset before test
    if not docker_services.restart_db_init():
        pytest.fail("Failed to reset database")

    if not wait_for_api_ready(timeout=60):
        docker_services.logs()
        pytest.fail("API did not restart successfully after database reset")

    yield

    # No cleanup needed - database is reset before each test that needs it


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Return the base URL for API requests."""
    return API_BASE_URL


@pytest.fixture(scope="session")
def api_client(docker_services: DockerComposeManager) -> requests.Session:
    """
    Session-scoped fixture that provides a requests session for API calls.

    The session is configured with common headers and uses admin authentication
    by default for convenience.
    """
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer test-admin-api-key-12345",  # From seed_data.py
    })
    return session


@pytest.fixture(scope="session")
def admin_api_client(docker_services: DockerComposeManager) -> requests.Session:
    """
    Session-scoped fixture that provides an authenticated admin API client.
    """
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-API-Key": "test-admin-api-key-12345",  # From seed_data.py
    })
    return session


@pytest.fixture(scope="session")
def user_api_client(docker_services: DockerComposeManager) -> requests.Session:
    """
    Session-scoped fixture that provides an authenticated regular user API client.
    """
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-API-Key": "test-user-api-key-67890",  # From seed_data.py
    })
    return session
