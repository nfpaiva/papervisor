"""Basic test for papervisor functionality."""

import sys
from pathlib import Path

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import after path setup
from papervisor import Papervisor  # noqa: E402


def test_basic_functionality() -> None:
    """Test basic papervisor functionality."""
    # Use dedicated test data directory
    test_data_dir = Path(__file__).parent / "data"

    # Initialize papervisor with test data
    papervisor = Papervisor(str(test_data_dir))

    # Test listing projects first
    projects = papervisor.list_projects()
    print(f"Found {len(projects)} projects")
    assert len(projects) > 0, "No projects found"

    # Verify we have the test project
    test_project = None
    for project in projects:
        if project.project_id == "test_project":
            test_project = project
            break

    assert test_project is not None, "Test project not found"
    print(f"Using test project: {test_project.title}")

    # Test listing queries in the test project
    queries = papervisor.list_project_queries(test_project.project_id)
    print(f"Found {len(queries)} queries")
    assert len(queries) >= 2, "Expected at least 2 test queries"

    # Test loading a specific query
    first_query = queries[0]
    df = papervisor.load_query_results(test_project.project_id, first_query.id)
    print(f"Loaded {len(df)} papers for query '{first_query.id}'")
    assert len(df) > 0, "No papers loaded"

    # Test getting statistics
    stats = papervisor.get_query_statistics(test_project.project_id, first_query.id)
    total_citations = stats["citation_stats"]["total_citations"]
    print(
        f"Statistics: {stats['total_papers']} papers, "
        f"{total_citations} total citations"
    )
    assert stats["total_papers"] > 0, "No papers in statistics"

    # Test searching papers
    filtered_df = papervisor.search_papers(df, min_citations=100)
    print(f"Found {len(filtered_df)} papers with >100 citations")

    print("✅ All tests passed!")


if __name__ == "__main__":
    test_basic_functionality()
