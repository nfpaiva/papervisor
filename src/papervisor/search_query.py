"""Search query management for papervisor."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import yaml


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
