"""Literature review project management for papervisor."""
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml  # type: ignore

from .search_query import SearchQuery


@dataclass
class LiteratureReviewProject:
    """Represents a literature review project with multiple search queries."""

    project_id: str
    title: str
    description: str
    created_date: str
    status: str
    lead_researcher: str
    project_path: str
    search_queries_file: str
    results_directory: str
    analysis_directory: str
    total_queries: int
    tags: List[str]

    @property
    def created_datetime(self) -> datetime:
        """Convert created_date string to datetime object."""
        return datetime.strptime(self.created_date, "%Y-%m-%d")


class ProjectManager:
    """Manages multiple literature review projects."""

    def __init__(self, data_dir: Path):
        """Initialize with path to data directory."""
        self.data_dir = Path(data_dir)
        self.projects_index_file = self.data_dir / "projects_index.yaml"
        self._projects: List[LiteratureReviewProject] = []
        self._load_projects()

    def _load_projects(self) -> None:
        """Load projects from the index file."""
        if not self.projects_index_file.exists():
            # Create empty index if it doesn't exist
            self._save_empty_index()
            return

        with open(self.projects_index_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self._projects = [
            LiteratureReviewProject(**project_data)
            for project_data in data.get("projects", [])
        ]

    def _save_empty_index(self) -> None:
        """Create an empty projects index file."""
        data: Dict[str, List[Any]] = {"projects": []}
        with open(self.projects_index_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, indent=2)

    def get_all_projects(self) -> List[LiteratureReviewProject]:
        """Get all literature review projects."""
        return self._projects.copy()

    def get_project_by_id(self, project_id: str) -> Optional[LiteratureReviewProject]:
        """Get a specific project by ID."""
        for project in self._projects:
            if project.project_id == project_id:
                return project
        return None

    def get_projects_by_status(self, status: str) -> List[LiteratureReviewProject]:
        """Get all projects with a specific status."""
        return [p for p in self._projects if p.status.lower() == status.lower()]

    def get_projects_by_researcher(
        self, researcher: str
    ) -> List[LiteratureReviewProject]:
        """Get all projects by a specific researcher."""
        return [
            p for p in self._projects if p.lead_researcher.lower() == researcher.lower()
        ]

    def load_project_queries(self, project_id: str) -> List[SearchQuery]:
        """Load search queries for a specific project."""
        project = self.get_project_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID '{project_id}' not found")

        queries_file = self.data_dir / project.search_queries_file
        if not queries_file.exists():
            raise FileNotFoundError(f"Search queries file not found: {queries_file}")

        with open(queries_file, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = yaml.safe_load(f)

        queries = []
        for query_data in data.get("search_queries", []):
            # Add project context to each query
            query_data["project_id"] = project_id
            queries.append(SearchQuery(**query_data))

        return queries

    def get_project_results_directory(self, project_id: str) -> Path:
        """Get the results directory path for a project."""
        project = self.get_project_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID '{project_id}' not found")

        return self.data_dir / project.results_directory

    def get_project_analysis_directory(self, project_id: str) -> Path:
        """Get the analysis directory path for a project."""
        project = self.get_project_by_id(project_id)
        if not project:
            raise ValueError(f"Project with ID '{project_id}' not found")

        return self.data_dir / project.analysis_directory
