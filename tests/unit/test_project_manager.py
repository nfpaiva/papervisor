"""Unit tests for project manager functionality."""

import tempfile
from pathlib import Path

from papervisor.project_manager import ProjectManager, LiteratureReviewProject


def test_project_manager_initialization() -> None:
    """Test project manager initialization."""
    with tempfile.TemporaryDirectory() as temp_dir:
        data_dir = Path(temp_dir)

        pm = ProjectManager(data_dir)

        # Should create projects index file
        assert (data_dir / "projects_index.yaml").exists()

        # Should start with empty projects list
        projects = pm.get_all_projects()
        assert len(projects) == 0


def test_project_manager_with_demo_data() -> None:
    """Test project manager with the demo project data."""
    # Use the main data directory which contains the demo project
    main_data_dir = Path(__file__).parent.parent.parent / "data"

    pm = ProjectManager(main_data_dir)

    # Should load existing projects
    projects = pm.get_all_projects()
    assert len(projects) > 0

    # Should find the demo project
    demo_project = pm.get_project_by_id("demo_contact_center_ai")
    assert demo_project is not None
    assert demo_project.title == "AI in Contact Centers - Demo Project"
    assert demo_project.status == "demo"
    assert demo_project.total_queries == 2


def test_project_manager_queries_loading() -> None:
    """Test loading queries from demo project."""
    # Use the main data directory which contains the demo project
    main_data_dir = Path(__file__).parent.parent.parent / "data"

    pm = ProjectManager(main_data_dir)

    # Load queries for demo project
    queries = pm.load_project_queries("demo_contact_center_ai")
    assert len(queries) >= 2

    # Check first query properties
    q1 = next((q for q in queries if q.id == "q1"), None)
    assert q1 is not None
    assert "Real-Time Decision Systems" in q1.topic
    assert q1.project_id == "demo_contact_center_ai"


def test_project_manager_filtering() -> None:
    """Test project filtering functionality."""
    # Use the main data directory which contains projects
    main_data_dir = Path(__file__).parent.parent.parent / "data"

    pm = ProjectManager(main_data_dir)

    # Test filtering by status
    demo_projects = pm.get_projects_by_status("demo")
    assert len(demo_projects) >= 1

    demo_project = demo_projects[0]
    assert demo_project.status == "demo"

    # Test filtering by researcher
    demo_researcher_projects = pm.get_projects_by_researcher("Papervisor Demo")
    assert len(demo_researcher_projects) >= 1


def test_project_manager_directories() -> None:
    """Test getting project directory paths."""
    # Use the main data directory which contains the demo project
    main_data_dir = Path(__file__).parent.parent.parent / "data"

    pm = ProjectManager(main_data_dir)

    # Test getting results directory
    results_dir = pm.get_project_results_directory("demo_contact_center_ai")
    assert results_dir.name == "results"
    assert "demo_contact_center_ai" in str(results_dir)

    # Test getting analysis directory
    analysis_dir = pm.get_project_analysis_directory("demo_contact_center_ai")
    assert analysis_dir.name == "analysis"
    assert "demo_contact_center_ai" in str(analysis_dir)


def test_literature_review_project_dataclass() -> None:
    """Test the LiteratureReviewProject dataclass."""
    from datetime import datetime

    project = LiteratureReviewProject(
        project_id="test_project",
        title="Test Project",
        description="A test project",
        created_date="2025-08-13",
        status="active",
        lead_researcher="Test Researcher",
        project_path="literature_reviews/test_project",
        search_queries_file="literature_reviews/test_project/search_queries.yaml",
        results_directory="literature_reviews/test_project/results",
        analysis_directory="literature_reviews/test_project/analysis",
        total_queries=3,
        tags=["test", "demo"],
    )

    # Test datetime conversion
    created_dt = project.created_datetime
    assert isinstance(created_dt, datetime)
    assert created_dt.year == 2025
    assert created_dt.month == 8
    assert created_dt.day == 13


if __name__ == "__main__":
    test_project_manager_initialization()
    test_project_manager_with_demo_data()
    test_project_manager_queries_loading()
    test_project_manager_filtering()
    test_project_manager_directories()
    test_literature_review_project_dataclass()
    print("All project manager unit tests passed!")
