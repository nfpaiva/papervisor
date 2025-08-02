"""Search query management for papervisor."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import yaml  # type: ignore


@dataclass
class SearchQuery:
    """Represents a search query executed in Publish or Perish."""

    id: str
    topic: str
    query: str
    executed_date: str
    extractor: str
    extractor_version: str
    databases: List[str]
    filters: Dict[str, str]
    results_file: str
    notes: Optional[str] = None
    project_id: Optional[str] = None  # Added for project context

    @property
    def executed_datetime(self) -> datetime:
        """Convert executed_date string to datetime object."""
        return datetime.strptime(self.executed_date, "%Y-%m-%d")


class SearchQueryManager:
    """Manages search queries for literature reviews."""

    def __init__(self, queries_file: Path):
        """Initialize with path to search queries YAML file."""
        self.queries_file = Path(queries_file)
        self._queries: List[SearchQuery] = []
        self._load_queries()

    def _load_queries(self) -> None:
        """Load search queries from YAML file."""
        if not self.queries_file.exists():
            raise FileNotFoundError(
                f"Search queries file not found: {self.queries_file}"
            )

        with open(self.queries_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        self._queries = [
            SearchQuery(**query_data) for query_data in data.get("search_queries", [])
        ]

    def get_all_queries(self) -> List[SearchQuery]:
        """Get all loaded search queries."""
        return self._queries.copy()

    def get_query_by_id(self, query_id: str) -> Optional[SearchQuery]:
        """Get a specific search query by ID."""
        for query in self._queries:
            if query.id == query_id:
                return query
        return None

    def get_queries_by_system(self, system: str) -> List[SearchQuery]:
        """Get all queries executed on a specific system."""
        return [q for q in self._queries if q.extractor.lower() == system.lower()]

    def add_query(self, query: SearchQuery) -> None:
        """Add a new search query."""
        # Check if ID already exists
        if self.get_query_by_id(query.id):
            raise ValueError(f"Query with ID '{query.id}' already exists")

        self._queries.append(query)

    def save_queries(self) -> None:
        """Save current queries back to YAML file."""
        data = {
            "search_queries": [
                {
                    "id": q.id,
                    "topic": q.topic,
                    "query": q.query,
                    "executed_date": q.executed_date,
                    "extractor": q.extractor,
                    "extractor_version": q.extractor_version,
                    "databases": q.databases,
                    "filters": q.filters,
                    "results_file": q.results_file,
                    "notes": q.notes,
                }
                for q in self._queries
            ]
        }

        with open(self.queries_file, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, indent=2)
