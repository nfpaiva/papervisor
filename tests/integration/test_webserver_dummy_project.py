import pytest
import os
from pathlib import Path

try:
    from papervisor.web_server import create_app
except ImportError:
    create_app = None

# This integration test depends on the real demo project in the repository's data directory.
# If the demo project is missing or changed, these tests may fail.


@pytest.fixture
def client():
    if create_app is None:
        pytest.skip("papervisor.web_server.create_app not available")
    # Find the absolute path to the repo's data directory
    repo_root = Path(__file__).parent.parent.parent.resolve()
    data_dir = repo_root / "data"
    print(f"[DEBUG] Using data_dir: {data_dir}")
    demo_project_dir = data_dir / "literature_reviews" / "demo_contact_center_ai"
    print(f"[DEBUG] demo_project_dir: {demo_project_dir}")
    if demo_project_dir.exists():
        print(f"[DEBUG] demo_project_dir contents: {list(demo_project_dir.iterdir())}")
    else:
        print("[DEBUG] demo_project_dir does not exist!")
    os.environ["PAPERVISOR_DATA_DIR"] = str(data_dir)
    app = create_app(project_id="demo_contact_center_ai", data_dir=str(data_dir))
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_landing_page_lists_demo_project(client):
    """Check that the landing page loads and lists the demo project."""
    resp = client.get("/", follow_redirects=True)
    print(
        f"[DEBUG] Landing page response (full):\n{resp.data.decode(errors='replace')}\n---END---"
    )
    assert resp.status_code == 200
    assert b"demo_contact_center_ai" in resp.data


def test_projects_listing(client):
    """Try /projects endpoint to see if it lists the demo project and what links are present."""
    resp = client.get("/projects", follow_redirects=True)
    print(
        f"[DEBUG] /projects response (full):\n{resp.data.decode(errors='replace')}\n---END---"
    )
    assert resp.status_code == 200
    assert b"demo_contact_center_ai" in resp.data


def test_search_queries_displayed(client):
    """Check the project review page for search queries for the demo project."""
    resp = client.get("/project/demo_contact_center_ai/review", follow_redirects=True)
    print(
        f"[DEBUG] /project/demo_contact_center_ai/review response: {resp.status_code}\n{resp.data[:500]}\n---END---"
    )
    assert resp.status_code == 200
    assert b"Search Queries" in resp.data or b"search" in resp.data.lower()


def test_project_downloads_page(client):
    """Check the downloads page for the demo project."""
    resp = client.get(
        "/project/demo_contact_center_ai/downloads", follow_redirects=True
    )
    print(
        f"[DEBUG] /project/demo_contact_center_ai/downloads response: {resp.status_code}\n{resp.data[:500]}\n---END---"
    )
    assert resp.status_code == 200
    assert b"download" in resp.data.lower() or b"pdf" in resp.data.lower()


def test_text_extraction_page(client):
    """Check the text extraction page for the demo project."""
    resp = client.get(
        "/text_extraction?project_id=demo_contact_center_ai", follow_redirects=True
    )
    print(
        f"[DEBUG] /text_extraction?project_id=demo_contact_center_ai response: {resp.status_code}\n{resp.data[:500]}\n---END---"
    )
    assert resp.status_code == 200
    assert b"extract" in resp.data.lower() or b"text" in resp.data.lower()


def test_screening_page(client):
    """Check the screening page for the demo project."""
    resp = client.get(
        "/project/demo_contact_center_ai/screening", follow_redirects=True
    )
    print(
        f"[DEBUG] /project/demo_contact_center_ai/screening response: {resp.status_code}\n{resp.data[:500]}\n---END---"
    )
    assert resp.status_code == 200
    assert b"screen" in resp.data.lower() or b"llm" in resp.data.lower()


# Note: Deduplication and extraction endpoints are POST or require specific context/files.
# You can add POST tests with appropriate payloads if needed, or test downloads/review pages.
