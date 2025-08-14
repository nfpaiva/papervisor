"""Shared pytest fixtures and configuration for papervisor tests."""

import sys
import tempfile
from pathlib import Path
from typing import Any, Generator

import pytest

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import after adding path
from papervisor import Papervisor  # noqa: E402
from papervisor.web_server import PapervisorWebServer  # noqa: E402


@pytest.fixture
def test_data_dir() -> Path:
    """Get the test data directory path."""
    return Path(__file__).parent / "data"


@pytest.fixture
def papervisor_instance(test_data_dir: Path) -> Papervisor:
    """Create a Papervisor instance with test data."""
    return Papervisor(str(test_data_dir))


@pytest.fixture
def demo_project_data_dir() -> Path:
    """Get the main data directory containing the demo project."""
    return Path(__file__).parent.parent / "data"


@pytest.fixture
def demo_papervisor(demo_project_data_dir: Path) -> Papervisor:
    """Create a Papervisor instance with the demo project data."""
    return Papervisor(str(demo_project_data_dir))


@pytest.fixture
def temp_data_dir() -> Generator[Path, None, None]:
    """Create a temporary data directory for isolated tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def web_client(demo_project_data_dir: Path) -> Generator[Any, None, None]:
    """Create a Flask test client with demo project data."""
    web_server = PapervisorWebServer(data_dir=str(demo_project_data_dir))
    web_server.app.config["TESTING"] = True
    with web_server.app.test_client() as client:
        yield client


@pytest.fixture
def isolated_web_client(test_data_dir: Path) -> Generator[Any, None, None]:
    """Create a Flask test client with isolated test data."""
    web_server = PapervisorWebServer(data_dir=str(test_data_dir))
    web_server.app.config["TESTING"] = True
    with web_server.app.test_client() as client:
        yield client
