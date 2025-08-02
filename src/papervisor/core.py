"""Main papervisor module for literature review processing."""
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd

from .search_query import SearchQuery
from .data_loader import PublishOrPerishLoader
from .project_manager import ProjectManager, LiteratureReviewProject


class Papervisor:
    """Main class for managing literature review data and search queries."""

    def __init__(self, data_dir: str = "data"):
        """
        Initialize Papervisor with data directory.

        Args:
            data_dir: Directory containing literature review projects
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)

        # Initialize components
        self.project_manager = ProjectManager(self.data_dir)
        self.csv_loader = PublishOrPerishLoader(self.data_dir)

        # Cache for loaded datasets
        self._dataset_cache: Dict[str, pd.DataFrame] = {}

    def list_projects(self) -> List[LiteratureReviewProject]:
        """List all literature review projects."""
        return self.project_manager.get_all_projects()

    def get_project(self, project_id: str) -> Optional[LiteratureReviewProject]:
        """Get a specific project by ID."""
        return self.project_manager.get_project_by_id(project_id)

    def list_project_queries(self, project_id: str) -> List[SearchQuery]:
        """List all search queries for a project."""
        return self.project_manager.load_project_queries(project_id)

    def get_search_query(self, project_id: str, query_id: str) -> Optional[SearchQuery]:
        """Get a specific search query by project and query ID."""
        queries = self.project_manager.load_project_queries(project_id)
        for query in queries:
            if query.id == query_id:
                return query
        return None

    def load_query_results(
        self, project_id: str, query_id: str, use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Load CSV results for a specific search query.

        Args:
            project_id: ID of the literature review project
            query_id: ID of the search query
            use_cache: Whether to use cached data if available

        Returns:
            DataFrame with the loaded results
        """
        cache_key = f"{project_id}_{query_id}"

        # Check cache first
        if use_cache and cache_key in self._dataset_cache:
            return self._dataset_cache[cache_key].copy()

        # Get the search query
        query = self.get_search_query(project_id, query_id)
        if not query:
            msg = f"Search query '{query_id}' not found in project '{project_id}'"
            raise ValueError(msg)

        # Get project results directory
        results_dir = self.project_manager.get_project_results_directory(project_id)

        # Load the CSV file
        file_path = results_dir / Path(query.results_file).name
        df = self.csv_loader.load_csv(file_path.name, normalize_columns=True)

        # Add metadata columns
        df["project_id"] = project_id
        df["query_id"] = query_id
        df["search_query"] = query.query
        df["topic"] = query.topic
        df["executed_date"] = query.executed_date
        df["extractor"] = query.extractor

        # Cache the result
        if use_cache:
            self._dataset_cache[cache_key] = df.copy()

        return df

    def load_project_results(
        self, project_id: str, use_cache: bool = True
    ) -> Dict[str, pd.DataFrame]:
        """
        Load CSV results for all queries in a project.

        Args:
            project_id: ID of the literature review project
            use_cache: Whether to use cached data if available

        Returns:
            Dictionary mapping query IDs to their DataFrames
        """
        results = {}
        queries = self.project_manager.load_project_queries(project_id)

        for query in queries:
            try:
                results[query.id] = self.load_query_results(
                    project_id, query.id, use_cache
                )
            except Exception as e:
                print(
                    f"Warning: Could not load results for query " f"'{query.id}': {e}"
                )

        return results

    def combine_project_results(
        self, project_id: str, query_ids: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Combine results from multiple search queries within a project.

        Args:
            project_id: ID of the literature review project
            query_ids: List of query IDs to combine. If None, combines all
                queries in project.

        Returns:
            Combined DataFrame with all results
        """
        if query_ids is None:
            queries = self.project_manager.load_project_queries(project_id)
            query_ids = [q.id for q in queries]

        combined_dfs = []
        for query_id in query_ids:
            try:
                df = self.load_query_results(project_id, query_id)
                combined_dfs.append(df)
            except Exception as e:
                print(f"Warning: Could not load results for query '{query_id}': {e}")

        if not combined_dfs:
            return pd.DataFrame()

        return pd.concat(combined_dfs, ignore_index=True)

    def get_query_statistics(self, project_id: str, query_id: str) -> dict:
        """Get basic statistics for a specific query's results."""
        df = self.load_query_results(project_id, query_id)
        stats = self.csv_loader.get_basic_stats(df)

        # Add query-specific information
        query = self.get_search_query(project_id, query_id)
        if query is None:
            raise ValueError(f"Query '{query_id}' not found in project '{project_id}'")

        stats["query_info"] = {
            "project_id": project_id,
            "query_id": query.id,
            "topic": query.topic,
            "query_string": query.query,
            "executed_date": query.executed_date,
            "extractor": query.extractor,
            "databases": query.databases,
            "notes": query.notes,
        }

        return stats

    def get_project_statistics(
        self, project_id: str, query_ids: Optional[List[str]] = None
    ) -> dict:
        """Get statistics for combined results from a project."""
        df = self.combine_project_results(project_id, query_ids)
        if df.empty:
            return {"error": "No data available"}

        stats = self.csv_loader.get_basic_stats(df)

        # Add project information
        project = self.project_manager.get_project_by_id(project_id)
        if project is None:
            raise ValueError(f"Project '{project_id}' not found")

        if query_ids is None:
            queries = self.project_manager.load_project_queries(project_id)
            query_ids = [q.id for q in queries]

        stats["project_info"] = {
            "project_id": project_id,
            "title": project.title,
            "description": project.description,
            "queries_included": query_ids,
            "total_queries": len(query_ids),
        }

        return stats

    def search_papers(
        self,
        df: pd.DataFrame,
        title_keywords: Optional[List[str]] = None,
        author_keywords: Optional[List[str]] = None,
        year_range: Optional[Tuple[int, int]] = None,
        min_citations: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Search papers in a DataFrame based on various criteria.

        Args:
            df: DataFrame to search in
            title_keywords: Keywords to search in titles
            author_keywords: Keywords to search in authors
            year_range: Tuple of (min_year, max_year)
            min_citations: Minimum number of citations

        Returns:
            Filtered DataFrame
        """
        filtered_df = df.copy()

        # Filter by title keywords
        if title_keywords:
            title_col = "title" if "title" in filtered_df.columns else "Title"
            if title_col in filtered_df.columns:
                pattern = "|".join(title_keywords)
                mask = filtered_df[title_col].str.contains(
                    pattern, case=False, na=False
                )
                filtered_df = filtered_df[mask]

        # Filter by author keywords
        if author_keywords:
            author_col = "authors" if "authors" in filtered_df.columns else "Authors"
            if author_col in filtered_df.columns:
                pattern = "|".join(author_keywords)
                mask = filtered_df[author_col].str.contains(
                    pattern, case=False, na=False
                )
                filtered_df = filtered_df[mask]

        # Filter by year range
        if year_range:
            year_col = "year" if "year" in filtered_df.columns else "Year"
            if year_col in filtered_df.columns:
                min_year, max_year = year_range
                mask = (filtered_df[year_col] >= min_year) & (
                    filtered_df[year_col] <= max_year
                )
                filtered_df = filtered_df[mask]

        # Filter by minimum citations
        if min_citations is not None:
            cites_col = "citations" if "citations" in filtered_df.columns else "Cites"
            if cites_col in filtered_df.columns:
                mask = filtered_df[cites_col] >= min_citations
                filtered_df = filtered_df[mask]

        return filtered_df
