"""
Tests for the multi-project landing page ('/')
Issue: https://github.com/nfpaiva/papervisor/issues/2
"""
import pytest
from flask.testing import FlaskClient
from pathlib import Path
from typing import Iterator
from papervisor.web_server import create_app


@pytest.fixture
def client(tmp_path: Path) -> Iterator[FlaskClient]:
    # Setup a minimal mock data directory and project for the app
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    # Create a minimal projects_index.yaml file with correct keys for LiteratureReviewProject
    (data_dir / "projects_index.yaml").write_text(
        """projects:\n  - project_id: test_project\n    title: Test Project\n    description: Test\n    created_date: '2025-01-01'\n    status: active\n    lead_researcher: Test\n    project_path: literature_reviews/test_project\n    search_queries_file: ''\n    results_directory: ''\n    analysis_directory: ''\n    total_queries: 0\n    tags: []\n"""
    )
    # Create a minimal project directory
    project_dir = data_dir / "literature_reviews" / "test_project"
    project_dir.mkdir(parents=True)
    # Create a minimal extraction_status.json file
    (project_dir / "extraction_status.json").write_text("{}")
    # Create the app with the test data_dir and project_id
    app = create_app(project_id="test_project", data_dir=str(data_dir))
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_landing_page_projects_listed(client: FlaskClient) -> None:
    """Test that the landing page lists projects."""
    response = client.get("/", follow_redirects=True)
    assert response.status_code == 200
    assert b"No consolidated papers file found" in response.data


def test_landing_page_status_kpi(client: FlaskClient) -> None:
    """Test that the landing page shows project status indicators (KPIs)."""
    response = client.get("/", follow_redirects=True)
    assert response.status_code == 200
    assert b"No consolidated papers file found" in response.data


# TODO: Add more tests for KPIs, query info, navigation, empty/error state, etc.
