"""PDF downloader module for automatic paper retrieval."""

from papervisor.web.services.download_service import DownloadService
from pathlib import Path
from typing import List, Any, Optional


class PDFDownloader:
    """
    Deprecated: Use DownloadService for all download operations.
    This class is now a thin wrapper for legacy compatibility.
    """

    def __init__(self, project_path: Path, delay_between_requests: float = 1.0):
        """Initialize the PDF downloader.

        Args:
            project_path: Path to the literature review project
            delay_between_requests: Delay in seconds between download requests (deprecated, unused)
        """
        self.project_path = project_path
        # Note: delay_between_requests parameter is deprecated and no longer used
        # Keeping for backward compatibility but ignoring value
        _ = delay_between_requests

        # Create required directory structure
        self._create_directories()

        # Initialize DownloadService
        self.service = DownloadService(None, str(project_path.parent))

    def download_query_pdfs(
        self, query_id: str, papers_df: Any, max_downloads: Optional[int] = None
    ) -> List[Any]:
        """Download PDFs for all papers in a query result.

        Args:
            query_id: Query identifier (e.g., 'q1', 'q2')
            papers_df: DataFrame with paper information
            max_downloads: Maximum number of papers to download (for testing)

        Returns:
            List of download results
        """
        return self.service.download_query_pdfs(
            self.project_path, query_id, papers_df, max_downloads
        )

    def download_project_pdfs(
        self,
        project_id: str,
        query_ids: Any,
        papers_data: Any,
        max_downloads: Optional[int] = None,
    ) -> dict[Any, Any]:
        """Download PDFs for all queries in a project.

        Args:
            project_id: Project identifier
            query_ids: List of query identifiers
            papers_data: Dictionary mapping query IDs to DataFrames
            max_downloads: Maximum number of downloads per query (for testing)

        Returns:
            Dictionary mapping query IDs to download results
        """
        return self.service.download_project_pdfs(
            self.project_path, project_id, query_ids, papers_data, max_downloads
        )

    def download_consolidated_pdfs(
        self, project_id: str, consolidated_df: Any, max_downloads: Optional[int] = None
    ) -> dict[Any, Any]:
        """
        Download PDFs using the consolidated CSV approach.

        This method processes the consolidated CSV that contains unique papers
        and their source queries, downloading them to a unified directory.

        Args:
            project_id: Project identifier
            consolidated_df: DataFrame with consolidated paper data
            max_downloads: Maximum number of downloads (for testing)

        Returns:
            Dictionary mapping query IDs to download results (for compatibility)
        """
        return self.service.download_consolidated_pdfs(
            self.project_path, project_id, consolidated_df, max_downloads
        )

    def _create_directories(self) -> None:
        """Create required directory structure."""
        (self.project_path / "pdfs" / "automatic").mkdir(parents=True, exist_ok=True)
        (self.project_path / "pdfs" / "manual").mkdir(parents=True, exist_ok=True)
        (self.project_path / "pdfs" / "automatic" / "reports").mkdir(
            parents=True, exist_ok=True
        )

    # Legacy methods removed - were unused in current implementation
