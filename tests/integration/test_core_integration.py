"""Core integration tests for papervisor functionality."""

import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Import after path setup
from papervisor import Papervisor  # noqa: E402


def test_core_integration_with_demo_project() -> None:
    """Test core papervisor functionality using the demo project."""
    # Use the main data directory which contains the demo project
    main_data_dir = Path(__file__).parent.parent.parent / "data"

    # Initialize papervisor with main data directory
    papervisor = Papervisor(str(main_data_dir))

    # Test listing projects - should include demo project
    projects = papervisor.list_projects()
    print(f"Found {len(projects)} projects")
    assert len(projects) > 0, "No projects found"

    # Find the demo project
    demo_project = None
    for project in projects:
        if project.project_id == "demo_contact_center_ai":
            demo_project = project
            break

    assert demo_project is not None, "Demo project not found"
    print(f"Using demo project: {demo_project.title}")

    # Test listing queries in the demo project
    queries = papervisor.list_project_queries(demo_project.project_id)
    print(f"Found {len(queries)} queries")
    assert len(queries) >= 2, "Expected at least 2 demo queries"

    # Test loading a specific query (should be q1)
    first_query = queries[0]
    df = papervisor.load_query_results(demo_project.project_id, first_query.id)
    print(f"Loaded {len(df)} papers for query '{first_query.id}'")
    assert len(df) > 0, "No papers loaded"

    # Test getting statistics
    stats = papervisor.get_query_statistics(demo_project.project_id, first_query.id)
    total_citations = stats["citation_stats"]["total_citations"]
    print(
        f"Statistics: {stats['total_papers']} papers, "
        f"{total_citations} total citations"
    )
    assert stats["total_papers"] > 0, "No papers in statistics"

    # Test searching papers with a lower threshold for demo data
    filtered_df = papervisor.search_papers(df, min_citations=5)
    print(f"Found {len(filtered_df)} papers with >5 citations")

    print("✅ All core integration tests passed!")


def test_legacy_test_project_fallback() -> None:
    """Test with legacy test project if it exists, otherwise skip."""
    # Use dedicated test data directory (legacy)
    test_data_dir = Path(__file__).parent.parent / "data"

    if not test_data_dir.exists():
        print("⚠️  Legacy test data directory not found, skipping legacy tests")
        return

    # Initialize papervisor with test data
    papervisor = Papervisor(str(test_data_dir))

    # Test listing projects first
    projects = papervisor.list_projects()
    print(f"Found {len(projects)} projects in legacy test data")

    if len(projects) == 0:
        print("⚠️  No legacy test projects found, skipping legacy tests")
        return

    # Verify we have a test project
    test_project = None
    for project in projects:
        if "test" in project.project_id.lower():
            test_project = project
            break

    if test_project is None:
        print("⚠️  No legacy test project found, skipping legacy tests")
        return

    print(f"Using legacy test project: {test_project.title}")

    # Test listing queries in the test project
    queries = papervisor.list_project_queries(test_project.project_id)
    print(f"Found {len(queries)} queries in legacy project")

    if len(queries) == 0:
        print("⚠️  No queries in legacy test project")
        return

    # Test loading a specific query
    first_query = queries[0]
    df = papervisor.load_query_results(test_project.project_id, first_query.id)
    print(f"Loaded {len(df)} papers for legacy query '{first_query.id}'")

    print("✅ Legacy integration tests completed!")


if __name__ == "__main__":
    test_core_integration_with_demo_project()
    test_legacy_test_project_fallback()
