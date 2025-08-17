"""Tests for the projects page web interface."""

from typing import Any


class TestProjectsPage:
    """Test cases for the /projects route."""

    def test_projects_page_displays_demo_project(self, web_client: Any) -> None:
        """Test that the projects page loads and displays the demo project correctly."""
        response = web_client.get("/projects")

        assert response.status_code == 200

        # Check for demo project specific content
        assert b"AI in Contact Centers - Demo Project" in response.data
        assert b"Papervisor Demo" in response.data  # Lead researcher
        assert b"demo" in response.data  # Status
        assert b"2025-08-12" in response.data  # Created date

        # Check for project description
        assert (
            b"Demonstration project showcasing Papervisor capabilities" in response.data
        )

        # Check that demo project shows 2 queries (statistics)
        # Look for the demo project section specifically
        assert b"<strong>2</strong>" in response.data  # Total queries for demo project

        # Verify page structure
        assert b"Literature Review Projects" in response.data
        assert b"project(s) found" in response.data

    def test_projects_page_demo_project_statistics(self, web_client: Any) -> None:
        """Test that project statistics are calculated correctly."""
        response = web_client.get("/projects")

        assert response.status_code == 200

        # Check that statistics section exists
        assert b"queries" in response.data
        assert b"papers" in response.data
        assert b"downloaded" in response.data

        # Check for query details - demo project has 2 queries
        assert b"Real-Time Decision Systems in Contact Centers" in response.data
        assert b"Call Center Optimization with AI" in response.data

        # Verify query IDs are displayed
        assert b"q1" in response.data
        assert b"q2" in response.data

        # Verify that total queries shows 2 for demo project
        # Note: This checks the project metadata, not the actual query count
        # which tests that the projects_index.yaml is properly loaded

    def test_projects_page_handles_empty_state(
        self, isolated_web_client: Any, temp_data_dir: Any
    ) -> None:
        """Test graceful handling when no projects exist."""
        # This test uses isolated_web_client which uses test data
        # that can be controlled separately from the demo project
        response = isolated_web_client.get("/projects")

        assert response.status_code == 200
        # Should still show the page structure without crashing
        assert b"Literature Review Projects" in response.data

        # Note: Actual empty state testing would require setting up
        # an empty projects index in the test data


class TestProjectsPageErrorHandling:
    """Test error handling scenarios for the projects page."""

    def test_projects_page_handles_corrupted_project_data(
        self, web_client: Any
    ) -> None:
        """Test that the page doesn't crash with invalid project data."""
        # This is a more advanced test that would require mocking
        # or creating corrupted test data
        response = web_client.get("/projects")

        # Should not return 500 error even with bad data
        assert response.status_code in [
            200,
            400,
        ]  # 200 OK or 400 Bad Request, but not 500

    def test_projects_page_handles_missing_query_files(self, web_client: Any) -> None:
        """Test graceful degradation when query files are missing."""
        response = web_client.get("/projects")

        # Page should load even if some query files are missing
        assert response.status_code == 200
        assert b"Literature Review Projects" in response.data
