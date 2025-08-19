"""Main papervisor module for literature review processing."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd

from .search_query import SearchQuery
from .data_loader import PublishOrPerishLoader
from .project_manager import ProjectManager, LiteratureReviewProject
from .pdf_downloader import PDFDownloader, PaperDownloadResult


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

        # PDF downloader cache
        self._pdf_downloaders: Dict[str, PDFDownloader] = {}

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
        df = self.csv_loader.load_csv(str(file_path.absolute()), normalize_columns=True)

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

    def consolidate_project_csvs(self, project_id: str) -> Path:
        """
        Consolidate all query CSVs into a single CSV file with source query tracking.

        This method merges all query results, removes duplicates based on paper
        identity, and creates a new column 'source_queries' that tracks which
        queries each paper came from.

        Args:
            project_id: ID of the literature review project

        Returns:
            Path to the consolidated CSV file
        """
        queries = self.project_manager.load_project_queries(project_id)
        if not queries:
            raise ValueError(f"No queries found for project '{project_id}'")

        # Load all query results
        all_papers = []
        for query in queries:
            try:
                df = self.load_query_results(project_id, query.id, use_cache=False)
                # Add the source query ID to each row
                df["source_query"] = query.id
                all_papers.append(df)
                print(f"Loaded {len(df)} papers from query '{query.id}'")
            except Exception as e:
                print(f"Warning: Could not load results for query '{query.id}': {e}")

        if not all_papers:
            raise ValueError(
                f"No query data could be loaded for project '{project_id}'"
            )

        # Combine all papers
        combined_df = pd.concat(all_papers, ignore_index=True)
        print(f"Combined total: {len(combined_df)} papers")

        # NO automatic deduplication - present ALL papers to the user for manual review
        # Just convert source_query to source_queries for consistency
        combined_df["source_queries"] = combined_df["source_query"]
        combined_df = combined_df.drop("source_query", axis=1)

        print(
            f"All {len(combined_df)} papers will be presented for manual "
            "duplicate review"
        )

        # Create the consolidated CSV path
        pdf_dir = self.data_dir / "literature_reviews" / project_id / "pdfs"
        pdf_dir.mkdir(parents=True, exist_ok=True)

        consolidated_path = pdf_dir / "consolidated_papers.csv"

        # Save the consolidated CSV
        combined_df.to_csv(consolidated_path, index=False)
        print(f"Consolidated CSV saved to: {consolidated_path}")

        return consolidated_path

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

    def get_pdf_directory(
        self, project_id: str, query_id: Optional[str] = None
    ) -> Path:
        """
        Get the PDF directory path for a project.

        Note: With the new consolidated approach, query_id is ignored as all PDFs
        are stored in a unified pdfs/automatic directory.

        Args:
            project_id: The project identifier
            query_id: Optional query identifier (ignored in consolidated approach)

        Returns:
            Path to the PDF directory

        Raises:
            ValueError: If project doesn't exist
        """
        project = self.get_project(project_id)
        if project is None:
            raise ValueError(f"Project '{project_id}' not found")

        pdf_dir = (
            self.data_dir / "literature_reviews" / project_id / "pdfs" / "automatic"
        )

        # Create directory if it doesn't exist
        pdf_dir.mkdir(parents=True, exist_ok=True)

        return pdf_dir

    def list_downloaded_pdfs(
        self, project_id: str, query_id: Optional[str] = None
    ) -> List[Path]:
        """
        List all downloaded PDF files for a project.

        Note: With the consolidated approach, query_id is ignored as all PDFs
        are in a single directory.

        Args:
            project_id: The project identifier
            query_id: Optional query identifier (ignored in consolidated approach)

        Returns:
            List of PDF file paths
        """
        pdf_dir = self.get_pdf_directory(project_id)

        # List all PDFs in the unified directory
        return list(pdf_dir.glob("*.pdf"))

    def get_pdf_download_stats(self, project_id: str) -> Dict[str, int]:
        """
        Get statistics about downloaded PDFs for a project.

        Args:
            project_id: The project identifier

        Returns:
            Dictionary with download statistics
        """
        stats = {}
        pdf_dir = self.get_pdf_directory(project_id)

        total_pdfs = len(list(pdf_dir.glob("*.pdf")))
        stats["total"] = total_pdfs
        return stats

    def get_pdf_downloader(self, project_id: str) -> PDFDownloader:
        """
        Get or create a PDF downloader for a project.

        Args:
            project_id: The project identifier

        Returns:
            PDFDownloader instance for the project
        """
        if project_id not in self._pdf_downloaders:
            project = self.project_manager.get_project_by_id(project_id)
            if not project:
                raise ValueError(f"Project with ID '{project_id}' not found")
            project_path = self.project_manager.data_dir / project.project_path
            self._pdf_downloaders[project_id] = PDFDownloader(project_path)

        return self._pdf_downloaders[project_id]

    def download_query_pdfs(
        self,
        project_id: str,
        query_id: str,
        max_downloads: Optional[int] = None,
    ) -> List[PaperDownloadResult]:
        """
        Download PDFs for all papers in a query result.

        Args:
            project_id: The project identifier
            query_id: The query identifier
            max_downloads: Maximum number of papers to download (for testing)

        Returns:
            List of download results
        """
        # Load the query results
        papers_df = self.load_query_results(project_id, query_id)

        # Get the PDF downloader
        downloader = self.get_pdf_downloader(project_id)

        # Start the download process
        return downloader.download_query_pdfs(query_id, papers_df, max_downloads)

    def download_project_pdfs(
        self,
        project_id: str,
        query_ids: Optional[List[str]] = None,
        max_downloads: Optional[int] = None,
    ) -> Dict[str, List[PaperDownloadResult]]:
        """
        Download PDFs for all queries in a project using consolidated CSV approach.

        Args:
            project_id: The project identifier
            query_ids: List of query IDs to download. If None, downloads all queries
            max_downloads: Maximum total downloads across all queries (for testing)

        Returns:
            Dictionary mapping query IDs to their download results
        """
        # First, consolidate the project CSVs
        print(f"📊 Consolidating query CSVs for project '{project_id}'...")
        consolidated_csv_path = self.consolidate_project_csvs(project_id)

        # Load the consolidated CSV
        consolidated_df = pd.read_csv(consolidated_csv_path)
        print(f"📄 Loaded consolidated CSV with {len(consolidated_df)} unique papers")

        # Get the PDF downloader and perform download using consolidated data
        downloader = self.get_pdf_downloader(project_id)

        return downloader.download_consolidated_pdfs(
            project_id, consolidated_df, max_downloads
        )

    def get_download_statistics(
        self, project_id: str, query_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get PDF download statistics for a project or specific query.

        Args:
            project_id: The project identifier
            query_id: Optional query identifier

        Returns:
            Dictionary with download statistics
        """
        downloader = self.get_pdf_downloader(project_id)
        return downloader.get_download_statistics(query_id)

    def list_manual_download_candidates(
        self, project_id: str, query_id: Optional[str] = None
    ) -> pd.DataFrame:
        """
        List papers that require manual download.

        Args:
            project_id: The project identifier
            query_id: Optional query identifier

        Returns:
            DataFrame with papers requiring manual download
        """
        downloader = self.get_pdf_downloader(project_id)

        if query_id:
            # Get failed downloads for specific query
            downloader.get_download_statistics(query_id)
            # This would need to be implemented in the downloader to return
            # actual paper details. For now, return empty DataFrame
            return pd.DataFrame()
        else:
            # Get failed downloads for all queries
            # This would need to be implemented to aggregate across all
            # queries
            return pd.DataFrame()
