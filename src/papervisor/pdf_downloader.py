"""PDF downloader module for automatic paper retrieval."""

import json
import logging
import os
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class DownloadStatus:
    """Download status constants."""

    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    ALREADY_EXISTED = "already_existed"
    MANUAL_REQUIRED = "manual_required"
    NOT_FOUND = "not_found"


class PaperDownloadResult:
    """Result of a paper download attempt."""

    def __init__(
        self,
        paper_id: str,
        title: str,
        status: str,
        file_path: Optional[Path] = None,
        error_message: Optional[str] = None,
        download_source: Optional[str] = None,
        file_size: Optional[int] = None,
    ):
        self.paper_id = paper_id
        self.title = title
        self.status = status
        self.file_path = file_path
        self.error_message = error_message
        self.download_source = download_source
        self.file_size = file_size
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "status": self.status,
            "file_path": str(self.file_path) if self.file_path else None,
            "error_message": self.error_message,
            "download_source": self.download_source,
            "file_size": self.file_size,
            "timestamp": self.timestamp,
        }


class PDFDownloader:
    """Handles automatic PDF downloading for research papers."""

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for download operations."""
        print(f"Setting up logger for reports path: {self.reports_path}")
        print(f"Reports directory exists: {self.reports_path.exists()}")

        # Create unique logger name to avoid conflicts
        logger_name = f"pdf_downloader_{id(self)}"
        logger = logging.getLogger(logger_name)

        # Clear any existing handlers
        logger.handlers.clear()
        logger.setLevel(logging.INFO)

        # Create file handler
        log_file = self.reports_path / "download_log.txt"
        print(f"Log file path: {log_file}")

        try:
            handler = logging.FileHandler(log_file, mode="a")  # Append mode
            handler.setLevel(logging.INFO)

            # Create formatter
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)

            # Add handler to logger
            logger.addHandler(handler)

            # Test the logger
            logger.info("=== PDF Downloader Logger Initialized ===")
            logger.info(f"Log file path: {log_file}")
            logger.info(f"Reports directory exists: {self.reports_path.exists()}")
            writable = self.reports_path.is_dir() and os.access(
                self.reports_path, os.W_OK
            )
            logger.info(f"Reports directory writable: {writable}")

            print(f"Logger successfully set up with handler: {handler}")

        except Exception as e:
            print(f"Error setting up file handler: {e}")
            # Fallback to console handler if file handler fails
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        return logger

    def __init__(self, project_path: Path, delay_between_requests: float = 1.0):
        """Initialize the PDF downloader.

        Args:
            project_path: Path to the literature review project
            delay_between_requests: Delay in seconds between download requests
        """
        self.project_path = project_path
        # Find the project root (where the src/ directory is located)
        self.project_root = project_path
        while (
            not (self.project_root / "src").exists()
            and self.project_root.parent != self.project_root
        ):
            self.project_root = self.project_root.parent

        self.pdfs_path = project_path / "pdfs"
        self.automatic_path = self.pdfs_path / "automatic"
        self.manual_path = self.pdfs_path / "manual"
        self.reports_path = (
            self.automatic_path / "reports"
        )  # Reports now under automatic/
        self.delay = delay_between_requests

        # Ensure directories exist
        self.automatic_path.mkdir(parents=True, exist_ok=True)
        self.manual_path.mkdir(parents=True, exist_ok=True)
        self.reports_path.mkdir(parents=True, exist_ok=True)

        # Setup logging
        self.logger = self._setup_logger()

        # Setup HTTP session with retries
        self.session = self._setup_session()

        # Log initialization completion
        self.logger.info("PDFDownloader initialization completed successfully.")

    def _setup_session(self) -> requests.Session:
        """Setup HTTP session with retry strategy."""
        session = requests.Session()

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        # Set user agent and browser-like headers
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                ),
                "Accept": (
                    "text/html,application/xhtml+xml,application/xml;q=0.9,"
                    "image/avif,image/webp,*/*;q=0.8"
                ),
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )

        return session

    def clean_reports_directory(self) -> None:
        """Clean all existing reports from the reports directory."""
        self.logger.info("Cleaning reports directory...")
        print("🧹 Cleaning existing reports...")

        if not self.reports_path.exists():
            self.logger.info("Reports directory does not exist, creating it.")
            self.reports_path.mkdir(parents=True, exist_ok=True)
            return

        # Remove all report files
        removed_count = 0
        for report_file in self.reports_path.glob("*"):
            if report_file.is_file() and report_file.name not in [
                "README.md"
            ]:  # Keep README
                try:
                    report_file.unlink()
                    removed_count += 1
                    self.logger.info(f"Removed report file: {report_file.name}")
                except Exception as e:
                    self.logger.warning(f"Could not remove {report_file.name}: {e}")

        self.logger.info(
            f"Cleaned {removed_count} report files from {self.reports_path}"
        )
        print(f"🗑️  Removed {removed_count} existing report files")

    def download_query_pdfs(
        self,
        query_id: str,
        papers_df: pd.DataFrame,
        max_downloads: Optional[int] = None,
    ) -> List[PaperDownloadResult]:
        """Download PDFs for all papers in a query result.

        Args:
            query_id: Query identifier (e.g., 'q1', 'q2')
            papers_df: DataFrame with paper information
            max_downloads: Maximum number of papers to download (for testing)

        Returns:
            List of download results
        """
        self.logger.info(f"Starting PDF download for query {query_id}")

        # Debug: Log the CSV columns to understand data structure
        self.logger.info(f"CSV columns: {list(papers_df.columns)}")
        if len(papers_df) > 0:
            first_row = papers_df.iloc[0]
            self.logger.info(f"First row keys: {list(first_row.keys())}")
            self.logger.info(f"Sample data: {dict(first_row.head())}")

        # Create query directory (but don't clean it - that's done at project level)
        query_auto_dir = self.automatic_path / query_id
        query_auto_dir.mkdir(exist_ok=True)
        self.logger.info(f"Created/verified directory: {query_auto_dir}")

        results = []
        papers_to_process = (
            papers_df.head(max_downloads) if max_downloads else papers_df
        )

        self.logger.info(
            f"Processing {len(papers_to_process)} papers for query {query_id}"
        )
        print(f"  📄 Processing {len(papers_to_process)} papers...")

        for idx, paper in papers_to_process.iterrows():
            try:
                result = self._download_paper_pdf(paper, query_auto_dir, query_id)
                results.append(result)

                self.logger.info(f"Paper {result.paper_id}: {result.status}")

                # Log the outcome for each paper
                if result.status == DownloadStatus.SUCCESS and result.file_path:
                    print(f"    ✅ Downloaded: {result.file_path.name}")
                    self.logger.info(
                        f"Successfully downloaded: {result.file_path.name}"
                    )
                elif (
                    result.status == DownloadStatus.ALREADY_EXISTED and result.file_path
                ):
                    print(f"    📁 Already existed: {result.file_path.name}")
                    self.logger.info(f"File already existed: {result.file_path.name}")
                elif result.status == DownloadStatus.MANUAL_REQUIRED:
                    print(f"    ❌ Manual required: Paper {result.paper_id}")
                    self.logger.info(
                        f"Manual download required for paper {result.paper_id}"
                    )
                elif result.status == DownloadStatus.FAILED:
                    print(f"    ⚠️  Failed: Paper {result.paper_id}")
                    self.logger.error(
                        f"Download failed for paper {result.paper_id}: "
                        f"{result.error_message}"
                    )

                # Respect rate limiting only for actual downloads
                if result.status == DownloadStatus.SUCCESS:
                    time.sleep(self.delay)

            except Exception as e:
                error_msg = f"Unexpected error downloading paper {idx}: {str(e)}"
                self.logger.error(error_msg)

                result = PaperDownloadResult(
                    paper_id=str(idx),
                    title=paper.get("Title", "Unknown"),
                    status=DownloadStatus.FAILED,
                    error_message=error_msg,
                )
                results.append(result)

        # Generate reports
        self._generate_reports(query_id, results)

        downloaded_count = sum(1 for r in results if r.status == DownloadStatus.SUCCESS)
        existed_count = sum(
            1 for r in results if r.status == DownloadStatus.ALREADY_EXISTED
        )
        failed_count = sum(
            1
            for r in results
            if r.status in [DownloadStatus.FAILED, DownloadStatus.NOT_FOUND]
        )
        manual_count = sum(
            1 for r in results if r.status == DownloadStatus.MANUAL_REQUIRED
        )

        self.logger.info(
            f"Completed PDF download for query {query_id}. "
            f"Downloaded: {downloaded_count}, "
            f"Already existed: {existed_count}, "
            f"Failed: {failed_count}, "
            f"Manual required: {manual_count}"
        )

        return results

    def download_project_pdfs(
        self,
        project_id: str,
        query_ids: List[str],
        papers_data: Dict[str, pd.DataFrame],
        max_downloads: Optional[int] = None,
    ) -> Dict[str, List[PaperDownloadResult]]:
        """Download PDFs for all queries in a project.

        Args:
            project_id: Project identifier
            query_ids: List of query identifiers
            papers_data: Dictionary mapping query IDs to DataFrames
            max_downloads: Maximum number of downloads per query (for testing)

        Returns:
            Dictionary mapping query IDs to download results
        """
        self.logger.info(f"Starting project-wide PDF download for {project_id}")
        self.logger.info(f"Found {len(papers_data)} queries to process")

        # Clean reports directory before starting
        self.clean_reports_directory()

        all_results = {}

        for query_id, df in papers_data.items():
            self.logger.info(f"Processing query: {query_id} ({len(df)} papers)")

            try:
                results = self.download_query_pdfs(query_id, df, max_downloads)
                all_results[query_id] = results

                # Log summary for this query
                success_count = sum(
                    1 for r in results if r.status == DownloadStatus.SUCCESS
                )
                existed_count = sum(
                    1 for r in results if r.status == DownloadStatus.ALREADY_EXISTED
                )
                failed_count = sum(
                    1
                    for r in results
                    if r.status in [DownloadStatus.FAILED, DownloadStatus.NOT_FOUND]
                )
                manual_count = sum(
                    1 for r in results if r.status == DownloadStatus.MANUAL_REQUIRED
                )

                self.logger.info(
                    f"Query {query_id} complete: {success_count} downloaded, "
                    f"{existed_count} existed, {manual_count} manual, "
                    f"{failed_count} failed"
                )

            except Exception as e:
                self.logger.error(f"Error processing query {query_id}: {str(e)}")
                all_results[query_id] = []

        # Generate project-wide reports
        self._generate_project_reports(project_id, all_results, papers_data)

        # Calculate overall totals
        total_papers = sum(len(results) for results in all_results.values())
        total_success = sum(
            1
            for results in all_results.values()
            for r in results
            if r.status == DownloadStatus.SUCCESS
        )
        total_existed = sum(
            1
            for results in all_results.values()
            for r in results
            if r.status == DownloadStatus.ALREADY_EXISTED
        )
        total_failed = sum(
            1
            for results in all_results.values()
            for r in results
            if r.status in [DownloadStatus.FAILED, DownloadStatus.NOT_FOUND]
        )
        total_manual = sum(
            1
            for results in all_results.values()
            for r in results
            if r.status == DownloadStatus.MANUAL_REQUIRED
        )

        self.logger.info(
            f"Project download complete: {total_papers} papers processed, "
            f"{total_success} downloaded, {total_existed} existed, "
            f"{total_manual} manual, {total_failed} failed"
        )

        return all_results

    def download_consolidated_pdfs(
        self,
        project_id: str,
        consolidated_df: pd.DataFrame,
        max_downloads: Optional[int] = None,
    ) -> Dict[str, List[PaperDownloadResult]]:
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
        self.logger.info(f"Starting consolidated PDF download for {project_id}")
        self.logger.info(f"Processing {len(consolidated_df)} unique papers")

        # Clean reports directory before starting
        self.clean_reports_directory()

        # Download papers to unified directory
        output_dir = self.automatic_path  # No subdirectories anymore
        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        for idx, (_, paper) in enumerate(consolidated_df.iterrows()):
            if max_downloads and idx >= max_downloads:
                break

            try:
                print(
                    f"Processing paper {idx}: "
                    f"{paper.get('title', paper.get('Title', 'Unknown'))[:50]}..."
                )

                result = self._download_paper_pdf(paper, output_dir, "consolidated")
                results.append(result)

                # Print status
                if result.status == DownloadStatus.SUCCESS:
                    if result.file_path:
                        print(f"    ✅ Downloaded: {result.file_path.name}")
                    self.logger.info(f"Successfully downloaded paper {result.paper_id}")
                elif result.status == DownloadStatus.ALREADY_EXISTED:
                    if result.file_path:
                        print(f"    📁 Already existed: {result.file_path.name}")
                    self.logger.info(f"Paper {result.paper_id} already exists")
                elif result.status == DownloadStatus.MANUAL_REQUIRED:
                    print(f"    ❌ Manual required: Paper {result.paper_id}")
                    self.logger.warning(
                        f"Manual download required for paper {result.paper_id}: "
                        f"{result.error_message}"
                    )
                elif result.status == DownloadStatus.FAILED:
                    print(f"    ⚠️  Failed: Paper {result.paper_id}")
                    self.logger.error(
                        f"Download failed for paper {result.paper_id}: "
                        f"{result.error_message}"
                    )

                # Respect rate limiting only for actual downloads
                if result.status == DownloadStatus.SUCCESS:
                    time.sleep(self.delay)

            except Exception as e:
                error_msg = f"Unexpected error downloading paper {idx}: {str(e)}"
                self.logger.error(error_msg)

                result = PaperDownloadResult(
                    paper_id=str(idx),
                    title=paper.get("title", paper.get("Title", "Unknown")),
                    status=DownloadStatus.FAILED,
                    error_message=error_msg,
                )
                results.append(result)

        # Generate consolidated reports
        self._generate_project_reports(
            project_id, {project_id: results}, {project_id: consolidated_df}
        )

        # For compatibility, organize results by source queries
        results_by_query = self._organize_results_by_source_queries(
            consolidated_df, results
        )

        # Calculate totals
        total_success = sum(1 for r in results if r.status == DownloadStatus.SUCCESS)
        total_existed = sum(
            1 for r in results if r.status == DownloadStatus.ALREADY_EXISTED
        )
        total_failed = sum(
            1
            for r in results
            if r.status in [DownloadStatus.FAILED, DownloadStatus.NOT_FOUND]
        )
        total_manual = sum(
            1 for r in results if r.status == DownloadStatus.MANUAL_REQUIRED
        )

        self.logger.info(
            f"Consolidated download complete: {len(results)} papers processed, "
            f"{total_success} downloaded, {total_existed} existed, "
            f"{total_manual} manual, {total_failed} failed"
        )

        return results_by_query

    def _organize_results_by_source_queries(
        self, consolidated_df: pd.DataFrame, results: List[PaperDownloadResult]
    ) -> Dict[str, List[PaperDownloadResult]]:
        """
        Organize download results by source queries for compatibility.

        Args:
            consolidated_df: The consolidated DataFrame with source_queries column
            results: List of download results

        Returns:
            Dictionary mapping query IDs to their related download results
        """
        results_by_query: Dict[str, List[PaperDownloadResult]] = {}

        for i, result in enumerate(results):
            if i < len(consolidated_df):
                source_queries = consolidated_df.iloc[i].get("source_queries", "")
                if source_queries:
                    query_list = source_queries.split(",")
                    for query_id in query_list:
                        query_id = query_id.strip()
                        if query_id not in results_by_query:
                            results_by_query[query_id] = []
                        results_by_query[query_id].append(result)

        return results_by_query

    def _download_paper_pdf(
        self,
        paper: pd.Series,
        output_dir: Path,
        query_id: str,
    ) -> PaperDownloadResult:
        """Download PDF for a single paper.

        Args:
            paper: Paper information from DataFrame
            output_dir: Directory to save the PDF
            query_id: Query identifier

        Returns:
            Download result
        """
        paper_id = str(paper.name)  # DataFrame index as paper ID
        title = paper.get(
            "title", paper.get("Title", "Unknown Title")
        )  # Try lowercase first

        # Debug logging to see what data we have
        self.logger.info(f"Processing paper {paper_id}:")
        self.logger.info(f"  Title: {title}")
        self.logger.info(
            f"  Authors: {paper.get('authors', paper.get('Authors', 'N/A'))}"
        )
        self.logger.info(f"  Year: {paper.get('year', paper.get('Year', 'N/A'))}")

        # Check if we have a DOI or URL to work with
        doi = paper.get("DOI", "")
        url = paper.get("URL", "")
        article_url = paper.get("article_url", paper.get("ArticleURL", ""))
        fulltext_url = paper.get("FullTextURL", "")

        # Log available URLs for debugging
        self.logger.debug(
            f"Paper {paper_id} URLs - DOI: {doi}, URL: {url}, "
            f"ArticleURL: {article_url}, FullTextURL: {fulltext_url}"
        )

        if not any([doi, url, article_url, fulltext_url]):
            return PaperDownloadResult(
                paper_id=paper_id,
                title=title,
                status=DownloadStatus.MANUAL_REQUIRED,
                error_message="No DOI, URL, ArticleURL, or FullTextURL available "
                "for automatic download",
            )

        # Generate filename
        authors = paper.get("authors", paper.get("Authors", "Unknown"))
        year = paper.get("year", paper.get("Year", "Unknown"))
        filename = self._generate_filename(paper_id, authors, year, title)
        file_path = output_dir / filename

        self.logger.info(f"Generated filename for paper {paper_id}: {filename}")
        print(f"Target filename: {filename}")

        # Check if already downloaded
        if file_path.exists():
            self.logger.info(f"File already exists for paper {paper_id}: {filename}")
            print(f"  📁 Already exists: {filename}")
            return PaperDownloadResult(
                paper_id=paper_id,
                title=title,
                status=DownloadStatus.ALREADY_EXISTED,
                file_path=file_path,
                file_size=file_path.stat().st_size,
            )

        # Try different download strategies
        download_urls = self._get_download_urls(doi, url, article_url, fulltext_url)

        for source, download_url in download_urls:
            self.logger.info(f"Trying to download from {source}: {download_url}")
            try:
                # Special handling for IEEE URLs
                headers = {}
                if "ieeexplore.ieee.org" in download_url:
                    headers.update(
                        {
                            "Referer": "https://ieeexplore.ieee.org/",
                            "Accept": (
                                "application/pdf,text/html,application/xhtml+xml,"
                                "application/xml;q=0.9,*/*;q=0.8"
                            ),
                            "Accept-Language": "en-US,en;q=0.5",
                            "Accept-Encoding": "gzip, deflate",
                            "DNT": "1",
                            "Connection": "keep-alive",
                            "Upgrade-Insecure-Requests": "1",
                        }
                    )

                response = self.session.get(download_url, timeout=30, headers=headers)
                self.logger.info(
                    f"Response from {source}: {response.status_code}, "
                    f"Content-Type: {response.headers.get('content-type', 'Unknown')}"
                )

                if response.status_code == 200:
                    content_type = response.headers.get("content-type", "").lower()

                    if "pdf" in content_type:
                        # Save the PDF
                        with open(file_path, "wb") as f:
                            f.write(response.content)

                        self.logger.info(
                            f"Successfully downloaded PDF from {source} to {file_path}"
                        )
                        return PaperDownloadResult(
                            paper_id=paper_id,
                            title=title,
                            status=DownloadStatus.SUCCESS,
                            file_path=file_path,
                            download_source=source,
                            file_size=len(response.content),
                        )
                    else:
                        # Not a PDF, might be HTML page
                        self.logger.debug(
                            f"Content from {source} is not PDF "
                            f"(content-type: {content_type})"
                        )
                        continue

                elif response.status_code == 403:
                    self.logger.debug(f"Access denied (403) from {source}")
                    continue  # Access denied, try next source
                elif response.status_code == 404:
                    self.logger.debug(f"Not found (404) from {source}")
                    continue  # Not found, try next source
                else:
                    self.logger.debug(
                        f"HTTP error {response.status_code} from {source}"
                    )
                    continue  # Other error, try next source

            except requests.RequestException as e:
                self.logger.debug(f"Failed to download from {source}: {str(e)}")
                continue

        # If we get here, all download attempts failed

        # Create a more helpful error message based on the URLs we tried
        all_text = f"{doi} {url} {article_url} {fulltext_url}".lower()
        error_details = "Could not download automatically from available sources"

        if "ieeexplore.ieee.org" in all_text:
            error_details = (
                "IEEE papers often require institutional access. "
                "Try downloading manually from your institution's library "
                "or use the IEEE Xplore direct download if you have access."
            )
        elif "springer" in all_text or "link.springer.com" in all_text:
            error_details = (
                "Springer papers may require subscription access. "
                "Try downloading manually through your institution."
            )
        elif "acm.org" in all_text:
            error_details = (
                "ACM papers may require ACM Digital Library access. "
                "Try downloading manually through your institution."
            )
        elif not any([doi, url, article_url, fulltext_url]):
            error_details = "No download URLs available for this paper."
        elif "pdf" not in all_text:
            error_details = (
                "No direct PDF URLs found. The available URLs may lead to "
                "publisher pages that require manual download."
            )

        return PaperDownloadResult(
            paper_id=paper_id,
            title=title,
            status=DownloadStatus.MANUAL_REQUIRED,
            error_message=error_details,
        )

    def _get_download_urls(
        self, doi: str, url: str, article_url: str, fulltext_url: str
    ) -> List[Tuple[str, str]]:
        """Get potential download URLs for a paper.

        Args:
            doi: Paper DOI
            url: Paper URL
            article_url: Article URL from ArticleURL field
            fulltext_url: Full text URL from FullTextURL field

        Returns:
            List of (source_name, url) tuples to try
        """
        urls = []

        # Try FullTextURL first (most likely to be direct PDF link)
        if fulltext_url:
            urls.append(("fulltext_url", fulltext_url))

        # Try ArticleURL (often links to publisher page with PDF)
        if article_url:
            urls.append(("article_url", article_url))

        # Special handling for IEEE URLs
        all_text = f"{url} {doi} {article_url} {fulltext_url}".lower()
        if "ieeexplore.ieee.org" in all_text:
            # Try to convert IEEE viewer URLs to direct PDF URLs
            ieee_urls = self._get_ieee_pdf_urls(url, article_url, fulltext_url)
            for ieee_label, ieee_url in ieee_urls:
                if ieee_url:
                    urls.append((ieee_label, ieee_url))

        # Try DOI URL directly
        if doi:
            urls.append(("doi_direct", f"https://doi.org/{doi}"))

        # Try original URL
        if url:
            urls.append(("original_url", url))

        # Try arXiv if it looks like an arXiv paper
        if "arxiv" in all_text:
            # Extract arXiv ID and construct PDF URL
            arxiv_id = self._extract_arxiv_id(url, doi)
            if arxiv_id:
                urls.append(("arxiv", f"https://arxiv.org/pdf/{arxiv_id}.pdf"))

        return urls

    def _get_ieee_pdf_urls(
        self, url: str, article_url: str, fulltext_url: str
    ) -> List[Tuple[str, str]]:
        """Get multiple IEEE PDF URL attempts."""
        ieee_urls = []

        for source_url in [fulltext_url, article_url, url]:
            if not source_url or "ieeexplore.ieee.org" not in source_url:
                continue

            # Extract article number from various IEEE URL formats
            arnumber_match = re.search(r"arnumber=(\d+)", source_url)
            doc_match = re.search(r"/document/(\d+)", source_url)

            if arnumber_match:
                arnumber = arnumber_match.group(1)
                # Try multiple IEEE URL formats
                ieee_urls.append(
                    (
                        "ieee_stamp",
                        (
                            f"https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&"
                            f"arnumber={arnumber}"
                        ),
                    )
                )
                ieee_urls.append(
                    (
                        "ieee_pdf",
                        (
                            f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&"
                            f"arnumber={arnumber}"
                        ),
                    )
                )
                break
            elif doc_match:
                doc_id = doc_match.group(1)
                ieee_urls.append(
                    (
                        "ieee_stamp",
                        (
                            f"https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&"
                            f"arnumber={doc_id}"
                        ),
                    )
                )
                ieee_urls.append(
                    (
                        "ieee_pdf",
                        (
                            f"https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&"
                            f"arnumber={doc_id}"
                        ),
                    )
                )
                break

        return ieee_urls

    def _extract_arxiv_id(self, url: str, doi: str) -> Optional[str]:
        """Extract arXiv ID from URL or DOI."""
        text = f"{url} {doi}".lower()
        # Match arXiv:2301.12345, /abs/2301.12345, /pdf/2301.12345, arxiv.org/2301.12345
        match = re.search(r"arxiv[:/](\d+\.\d+)", text)
        if match:
            return match.group(1)
        match = re.search(
            r"arxiv\.org/(?:abs|pdf)/([0-9]{4}\.[0-9]{5}|[0-9]{4}\.[0-9]{4,5})", text
        )
        if match:
            return match.group(1)
        match = re.search(r"arxiv[: ]([0-9]{4}\.[0-9]{4,5})", text)
        if match:
            return match.group(1)
        return None

    def _generate_filename(
        self, paper_id: str, authors: str, year: str, title: str = ""
    ) -> str:
        """Generate filename for PDF."""
        # Clean up authors to get first author's last name
        if isinstance(authors, str) and authors:
            # Remove quotes and clean the author string
            authors = authors.strip('"').strip("'")
            first_author = authors.split(",")[0].split(";")[0].strip()
            # Remove common prefixes and get last word (surname)
            author_parts = first_author.split()
            if author_parts:
                last_name = author_parts[-1]
                # Remove non-alphanumeric characters
                last_name = "".join(c for c in last_name if c.isalnum())
            else:
                last_name = "Unknown"
        else:
            last_name = "Unknown"

        # Clean year
        if (
            isinstance(year, (str, int, float))
            and str(year).replace(".0", "").isdigit()
        ):
            clean_year = str(int(float(year)))  # Convert float to int to string
        else:
            clean_year = "Unknown"

        # Clean title to create a short descriptive name
        title_part = ""
        if isinstance(title, str) and title:
            # Take first few words of title and clean them
            title_words = title.split()[:4]  # First 4 words
            title_part = "_".join(
                "".join(c for c in word if c.isalnum())
                for word in title_words
                if len(word) > 2
            )[
                :50
            ]  # Limit to 50 characters
            if title_part:
                title_part = "_" + title_part

        filename = f"{paper_id}_{last_name}_{clean_year}{title_part}.pdf"

        # Ensure filename is not too long (filesystem limit)
        if len(filename) > 200:
            filename = f"{paper_id}_{last_name}_{clean_year}.pdf"

        return filename

    def _generate_reports(
        self, query_id: str, results: List[PaperDownloadResult]
    ) -> None:
        """Generate download reports."""
        print(
            f"DEBUG: _generate_reports called for query {query_id} "
            f"with {len(results)} results"
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        self.logger.info(f"Starting report generation for query {query_id}...")
        self.logger.info(f"Results count: {len(results)}")

        try:
            # JSON detailed report
            json_report: Dict[str, Any] = {
                "query_id": query_id,
                "timestamp": timestamp,
                "summary": {
                    "total_papers": len(results),
                    "successful_downloads": sum(
                        1 for r in results if r.status == DownloadStatus.SUCCESS
                    ),
                    "failed_downloads": sum(
                        1 for r in results if r.status == DownloadStatus.FAILED
                    ),
                    "manual_required": sum(
                        1 for r in results if r.status == DownloadStatus.MANUAL_REQUIRED
                    ),
                    "skipped": sum(
                        1 for r in results if r.status == DownloadStatus.SKIPPED
                    ),
                },
                "results": [r.to_dict() for r in results],
            }

            json_file = (
                self.reports_path / f"download_status_{query_id}_{timestamp}.json"
            )
            print(f"DEBUG: Writing JSON report to {json_file}")
            with open(json_file, "w") as f:
                json.dump(json_report, f, indent=2)
            print("DEBUG: JSON report written successfully")
            self.logger.info(f"JSON report written to {json_file}")

            # Also update the latest status file
            latest_file = self.reports_path / f"download_status_{query_id}_latest.json"
            print(f"DEBUG: Writing latest status to {latest_file}")
            with open(latest_file, "w") as f:
                json.dump(json_report, f, indent=2)
            print("DEBUG: Latest status written successfully")

            # Text summary report
            summary_file = (
                self.reports_path / f"download_summary_{query_id}_{timestamp}.txt"
            )
            print(f"DEBUG: Writing text summary to {summary_file}")
            with open(summary_file, "w") as f:
                f.write(f"PDF Download Summary for Query {query_id}\n")
                f.write(f"Generated: {timestamp}\n")
                f.write("=" * 50 + "\n\n")

                f.write(f"Total papers: {json_report['summary']['total_papers']}\n")
                f.write(
                    f"Successful downloads: "
                    f"{json_report['summary']['successful_downloads']}\n"
                )
                f.write(
                    f"Failed downloads: "
                    f"{json_report['summary']['failed_downloads']}\n"
                )
                f.write(
                    f"Manual downloads required: "
                    f"{json_report['summary']['manual_required']}\n"
                )
                f.write(
                    f"Skipped (already downloaded): "
                    f"{json_report['summary']['skipped']}\n\n"
                )
            print("DEBUG: Text summary written successfully")
            self.logger.info(f"Text summary report written to {summary_file}")

            # Generate user-friendly manual download report
            self._generate_manual_download_report(query_id, results, timestamp)

        except Exception as e:
            self.logger.error(
                f"Error generating reports for query {query_id}: {str(e)}"
            )

    def _generate_manual_download_report(
        self, query_id: str, results: List[PaperDownloadResult], timestamp: str
    ) -> None:
        """Generate a user-friendly manual download report with all metadata
        needed for manual retrieval.

        Args:
            query_id: Query identifier
            results: List of download results
            timestamp: Report timestamp
        """
        # Load the CSV data to get full metadata for manual downloads
        csv_file = (
            self.project_root
            / "data"
            / "literature_reviews"
            / "qplanner_literature_review"
            / "results"
            / f"{query_id}.csv"
        )
        if not csv_file.exists():
            self.logger.warning(f"CSV file not found: {csv_file}")
            return

        try:
            papers_df = pd.read_csv(csv_file)

            # Filter for manual required papers
            manual_required = [
                r for r in results if r.status == DownloadStatus.MANUAL_REQUIRED
            ]
            successful_downloads = [
                r for r in results if r.status == DownloadStatus.SUCCESS
            ]

            if not manual_required and not successful_downloads:
                return  # No report needed if nothing to show

            # Generate HTML report
            html_file = (
                self.reports_path / f"manual_download_guide_{query_id}_{timestamp}.html"
            )

            with open(html_file, "w", encoding="utf-8") as f:
                f.write(
                    self._generate_manual_download_html(
                        query_id, papers_df, manual_required, successful_downloads
                    )
                )

            # Also generate a simple text version
            text_file = (
                self.reports_path / f"manual_download_guide_{query_id}_{timestamp}.txt"
            )
            with open(text_file, "w", encoding="utf-8") as f:
                f.write(
                    self._generate_manual_download_text(
                        query_id, papers_df, manual_required, successful_downloads
                    )
                )

            self.logger.info(
                f"Manual download guides generated: {html_file}, {text_file}"
            )
            print(f"📋 Manual download guide generated: {html_file.name}")

        except Exception as e:
            self.logger.error(f"Error generating manual download report: {str(e)}")

    def _generate_manual_download_html(
        self,
        query_id: str,
        papers_df: pd.DataFrame,
        manual_required: List[PaperDownloadResult],
        successful_downloads: List[PaperDownloadResult],
    ) -> str:
        """Generate HTML content for manual download guide."""
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Manual Download Guide - Query {query_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px;
                   margin-bottom: 20px; }}
        .summary {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px;
                    margin-bottom: 20px; }}
        .paper {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px;
                  border-radius: 5px; }}
        .paper.manual {{ background-color: #fff5f5; }}
        .paper.success {{ background-color: #f0f8f0; }}
        .paper.existed {{ background-color: #f0f0ff; }}
        .paper-id {{ font-weight: bold; color: #333; }}
        .query-id {{ font-size: 0.9em; color: #666; background-color: #f5f5f5;
                   padding: 2px 6px; border-radius: 3px; }}

        .title {{ font-size: 1.1em; font-weight: bold; color: #0066cc;
                  margin: 5px 0; }}
        .authors {{ font-style: italic; margin: 5px 0; }}
        .metadata {{ margin: 10px 0; }}
        .metadata-item {{ margin: 5px 0; }}
        .url-list {{ margin: 10px 0; }}
        .url-item {{ margin: 5px 0; padding: 5px; background-color: #f9f9f9;
                     border-radius: 3px; }}
        .url-link {{ color: #0066cc; text-decoration: none;
                     word-break: break-all; }}
        .url-link:hover {{ text-decoration: underline; }}
        .abstract {{ background-color: #f9f9f9; padding: 10px; border-radius: 3px;
                     margin: 10px 0; }}
        .citation {{ background-color: #f0f0f0; padding: 10px; border-radius: 3px;
                     margin: 10px 0; font-family: monospace; }}
        .status {{ padding: 3px 8px; border-radius: 3px; font-size: 0.9em;
                   font-weight: bold; }}
        .status.manual {{ background-color: #ffebee; color: #c62828; }}
        .status.success {{ background-color: #e8f5e8; color: #2e7d32; }}
        .status.existed {{ background-color: #e3f2fd; color: #1565c0; }}
        .instructions {{ background-color: #fff3cd; padding: 15px; border-radius: 5px;
                         margin-bottom: 20px; border-left: 4px solid #ffc107; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📄 Manual Download Guide - Query {query_id}</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>

    <div class="summary">
        <h2>📊 Download Summary</h2>
        <ul>
            <li><strong>Total papers:</strong> {len(papers_df)}</li>
            <li><strong>✅ Successfully downloaded:</strong>
                {len(successful_downloads)}</li>
            <li><strong>❌ Require manual download:</strong>
                {len(manual_required)}</li>
        </ul>
    </div>

    <div class="instructions">
        <h3>📝 Instructions for Manual Download</h3>
        <ol>
            <li>For each paper below marked as "Manual Required", try the provided
                URLs in order</li>
            <li>Look for PDF download links on the publisher's page</li>
            <li>If you have institutional access, try accessing through your
                library</li>
            <li>Save the PDF with the suggested filename in the target
                directory</li>
            <li>Use the DOI for academic search engines if direct links don't
                work</li>
        </ol>
    </div>
"""

        # Add successfully downloaded papers section
        if successful_downloads:
            html += f"""
    <h2>✅ Successfully Downloaded Papers ({len(successful_downloads)})</h2>
"""
            for result in successful_downloads:
                paper_data = papers_df.iloc[int(result.paper_id)]
                authors = paper_data.get("Authors", "Unknown Authors")
                year = paper_data.get("Year", "Unknown Year")

                html += f"""
    <div class="paper success">
        <div class="paper-id">Paper ID: {result.paper_id}</div>
        <div class="title">{result.title}</div>
        <div class="authors">{authors} ({year})</div>
        <div class="metadata">
            <span class="status success">✅ DOWNLOADED</span>
            <div>📁 File: {result.file_path.name if result.file_path else 'N/A'}</div>"""

        size_str = f"{result.file_size / 1024:.1f} KB" if result.file_size else "N/A"
        html += f"""            <div>📊 Size: {size_str}</div>
        </div>
    </div>
"""

        # Add manual download section
        if manual_required:
            html += f"""
    <h2>❌ Papers Requiring Manual Download ({len(manual_required)})</h2>
"""
            for result in manual_required:
                paper_data = papers_df.iloc[int(result.paper_id)]

                authors = paper_data.get("Authors", "Unknown Authors")
                year = paper_data.get("Year", "Unknown Year")
                doi = paper_data.get("DOI", "")
                article_url = paper_data.get("ArticleURL", "")
                fulltext_url = paper_data.get("FullTextURL", "")
                source = paper_data.get("Source", "")
                publisher = paper_data.get("Publisher", "")
                abstract = paper_data.get("Abstract", "")
                cites = paper_data.get("Cites", 0)

                # Generate suggested filename
                filename = self._generate_filename(
                    result.paper_id, authors, year, result.title
                )

                # Build citation
                citation = f"{authors} ({year}). {result.title}."
                if source:
                    citation += f" {source}."
                if doi:
                    citation += f" DOI: {doi}"

                html += f"""
    <div class="paper manual">
        <div class="paper-id">Paper ID: {result.paper_id}</div>
        <div class="title">{result.title}</div>
        <div class="authors">{authors} ({year})</div>

        <div class="metadata">
            <span class="status manual">❌ MANUAL REQUIRED</span>
            <div class="metadata-item"><strong>📁 Suggested filename:</strong> {filename}</div>
            <div class="metadata-item"><strong>📊 Citations:</strong> {cites}</div>
            <div class="metadata-item"><strong>📰 Source:</strong> {source}</div>
            <div class="metadata-item"><strong>🏢 Publisher:</strong> {publisher}</div>
            {(f'<div class="metadata-item"><strong>🔗 DOI:</strong> '
                    f'<a href="https://doi.org/{doi}" class="url-link" '
                    f'target="_blank">{doi}</a></div>')
                    if doi and str(doi).lower() != 'nan' and doi.strip() else ''}
        </div>

        <div class="url-list">
            <h4>🔗 Available URLs (try in order):</h4>
"""

                # Add URLs in priority order
                urls_to_try = []
                if (
                    fulltext_url
                    and str(fulltext_url).lower() != "nan"
                    and fulltext_url.strip()
                ):
                    urls_to_try.append(
                        ("Full Text URL (most likely PDF)", fulltext_url)
                    )
                if (
                    article_url
                    and str(article_url).lower() != "nan"
                    and article_url.strip()
                ):
                    urls_to_try.append(("Article Page", article_url))
                if doi and str(doi).lower() != "nan" and doi.strip():
                    urls_to_try.append(("DOI Link", f"https://doi.org/{doi}"))

                for url_type, url in urls_to_try:
                    html += f"""
            <div class="url-item">
                <strong>{url_type}:</strong><br>
                <a href="{url}" class="url-link" target="_blank">{url}</a>
            </div>
"""

                if not urls_to_try:
                    html += (
                        "<div class='url-item'>❌ No direct URLs available - "
                        "try searching by title and authors</div>"
                    )

                html += "</div>"

                # Add abstract if available
                if abstract and abstract.strip():
                    html += f"""
        <div class="abstract">
            <strong>📄 Abstract:</strong><br>
            {abstract}
        </div>
"""

                # Add citation
                html += f"""
        <div class="citation">
            <strong>📖 Citation:</strong><br>
            {citation}
        </div>
    </div>
"""

        html += """
</body>
</html>"""

        return html

    def _generate_manual_download_text(
        self,
        query_id: str,
        papers_df: pd.DataFrame,
        manual_required: List[PaperDownloadResult],
        successful_downloads: List[PaperDownloadResult],
    ) -> str:
        """Generate text content for manual download guide."""
        text = f"""MANUAL DOWNLOAD GUIDE - QUERY {query_id}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'=' * 60}

DOWNLOAD SUMMARY
Total papers: {len(papers_df)}
Successfully downloaded: {len(successful_downloads)}
Require manual download: {len(manual_required)}

INSTRUCTIONS FOR MANUAL DOWNLOAD
1. For each paper below marked as "MANUAL REQUIRED", try the provided URLs in order
2. Look for PDF download links on the publisher's page
3. If you have institutional access, try accessing through your library
4. Save the PDF with the suggested filename in the target directory
5. Use the DOI for academic search engines if direct links don't work

"""

        # Add successfully downloaded papers
        if successful_downloads:
            text += f"\nSUCCESSFULLY DOWNLOADED PAPERS ({len(successful_downloads)})\n"
            text += "-" * 50 + "\n"

            for result in successful_downloads:
                paper_data = papers_df.iloc[int(result.paper_id)]
                authors = paper_data.get("Authors", "Unknown Authors")
                year = paper_data.get("Year", "Unknown Year")

                text += f"\n[{result.paper_id}] ✅ DOWNLOADED\n"
                text += f"Title: {result.title}\n"
                text += f"Authors: {authors} ({year})\n"
                text += (
                    f"File: {result.file_path.name if result.file_path else 'N/A'}\n"
                )
                size_str = (
                    f"{result.file_size / 1024:.1f} KB" if result.file_size else "N/A"
                )
                text += f"Size: {size_str}\n"

        # Add manual download section
        if manual_required:
            text += f"\n\nPAPERS REQUIRING MANUAL DOWNLOAD ({len(manual_required)})\n"
            text += "-" * 50 + "\n"

            for result in manual_required:
                paper_data = papers_df.iloc[int(result.paper_id)]

                authors = paper_data.get("Authors", "Unknown Authors")
                year = paper_data.get("Year", "Unknown Year")
                doi = paper_data.get("DOI", "")
                article_url = paper_data.get("ArticleURL", "")
                fulltext_url = paper_data.get("FullTextURL", "")
                source = paper_data.get("Source", "")
                publisher = paper_data.get("Publisher", "")
                abstract = paper_data.get("Abstract", "")
                cites = paper_data.get("Cites", 0)

                # Generate suggested filename
                filename = self._generate_filename(
                    result.paper_id, authors, year, result.title
                )

                text += f"\n[{result.paper_id}] ❌ MANUAL REQUIRED\n"
                text += f"Title: {result.title}\n"
                text += f"Authors: {authors} ({year})\n"
                text += f"Citations: {cites}\n"
                text += f"Source: {source}\n"
                text += f"Publisher: {publisher}\n"
                text += f"Suggested filename: {filename}\n"

                if doi and str(doi).lower() != "nan" and doi.strip():
                    text += f"DOI: {doi}\n"
                    text += f"DOI URL: https://doi.org/{doi}\n"

                text += "\nURLs to try (in order):\n"
                url_count = 1
                if (
                    fulltext_url
                    and str(fulltext_url).lower() != "nan"
                    and fulltext_url.strip()
                ):
                    text += f"  {url_count}. Full Text URL: {fulltext_url}\n"
                    url_count += 1
                if (
                    article_url
                    and str(article_url).lower() != "nan"
                    and article_url.strip()
                ):
                    text += f"  {url_count}. Article Page: {article_url}\n"
                    url_count += 1
                if doi and str(doi).lower() != "nan" and doi.strip():
                    text += f"  {url_count}. DOI Link: https://doi.org/{doi}\n"
                    url_count += 1

                if url_count == 1:  # No URLs were added
                    text += (
                        "  ❌ No direct URLs available - try searching by "
                        "title and authors\n"
                    )

                if abstract and abstract.strip():
                    text += f"\nAbstract: {abstract}\n"

                # Add citation
                citation = f"{authors} ({year}). {result.title}."
                if source:
                    citation += f" {source}."
                if doi:
                    citation += f" DOI: {doi}"
                text += f"\nCitation: {citation}\n"
                text += "-" * 40 + "\n"

        return text

    def get_download_statistics(self, query_id: Optional[str] = None) -> Dict[str, Any]:
        """Get download statistics for a query or all queries.

        Args:
            query_id: Specific query ID, or None for all queries

        Returns:
            Dictionary with download statistics
        """
        # First try to get project-level statistics (preferred)
        project_files = list(
            self.reports_path.glob("project_download_status_*_latest.json")
        )

        if project_files and not query_id:
            # Use the most recent project report
            latest_project_file = max(project_files, key=lambda p: p.stat().st_mtime)
            try:
                with open(latest_project_file) as f:
                    data: Dict[str, Any] = json.load(f)
                # Update format to include already_existed
                summary = data["summary"]
                summary["already_existed"] = summary.get("already_existed", 0)
                # Keep compatibility with old field names
                summary["skipped"] = summary.get("already_existed", 0)
                return data
            except Exception as e:
                self.logger.warning(
                    f"Could not read project report {latest_project_file}: {e}"
                )

        if query_id:
            # Statistics for specific query
            latest_file = self.reports_path / f"download_status_{query_id}_latest.json"
            if latest_file.exists():
                with open(latest_file) as f:
                    query_data: Dict[str, Any] = json.load(f)
                query_summary: Dict[str, Any] = query_data["summary"]
                # Add already_existed field if not present
                query_summary["already_existed"] = query_summary.get(
                    "already_existed", 0
                )
                return query_summary
            else:
                return {
                    "total_papers": 0,
                    "successful_downloads": 0,
                    "already_existed": 0,
                    "failed_downloads": 0,
                    "manual_required": 0,
                    "skipped": 0,
                }
        else:
            # Combined statistics for all queries (fallback)
            total_stats: Dict[str, Any] = {
                "total_papers": 0,
                "successful_downloads": 0,
                "already_existed": 0,
                "failed_downloads": 0,
                "manual_required": 0,
                "skipped": 0,
                "by_query": {},
            }

            # Find all latest status files
            for status_file in self.reports_path.glob("download_status_*_latest.json"):
                try:
                    with open(status_file) as f:
                        status_data: Dict[str, Any] = json.load(f)
                        query = status_data["query_id"]
                        status_summary: Dict[str, Any] = status_data["summary"]

                        # Ensure all fields are present
                        status_summary["already_existed"] = status_summary.get(
                            "already_existed", 0
                        )
                        status_summary["skipped"] = status_summary.get(
                            "already_existed", 0
                        )

                        total_stats["by_query"][query] = status_summary
                        for key in [
                            "total_papers",
                            "successful_downloads",
                            "already_existed",
                            "failed_downloads",
                            "manual_required",
                        ]:
                            total_stats[key] += status_summary.get(key, 0)
                        total_stats["skipped"] += status_summary.get(
                            "already_existed", 0
                        )
                except Exception as e:
                    self.logger.warning(
                        f"Could not read query report {status_file}: {e}"
                    )

            return total_stats

    def _generate_project_reports(
        self,
        project_id: str,
        all_results: Dict[str, List[PaperDownloadResult]],
        papers_data: Dict[str, pd.DataFrame],
    ) -> None:
        """Generate comprehensive reports for the entire project download.

        Args:
            project_id: Project identifier
            all_results: Dictionary mapping query_id to download results
            papers_data: Dictionary mapping query_id to papers DataFrame
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Calculate totals across all queries
        total_papers = sum(len(results) for results in all_results.values())
        total_success = sum(
            1
            for results in all_results.values()
            for r in results
            if r.status == DownloadStatus.SUCCESS
        )
        total_already_existed = sum(
            1
            for results in all_results.values()
            for r in results
            if r.status == DownloadStatus.ALREADY_EXISTED
        )
        total_failed = sum(
            1
            for results in all_results.values()
            for r in results
            if r.status == DownloadStatus.FAILED
        )
        total_manual = sum(
            1
            for results in all_results.values()
            for r in results
            if r.status == DownloadStatus.MANUAL_REQUIRED
        )

        self.logger.info("Generating project reports for %s", project_id)
        print("📊 Generating comprehensive project reports...")

        # Generate JSON project report
        project_report: Dict[str, Any] = {
            "project_id": project_id,
            "timestamp": timestamp,
            "summary": {
                "total_papers": total_papers,
                "successful_downloads": total_success,
                "already_existed": total_already_existed,
                "failed_downloads": total_failed,
                "manual_required": total_manual,
                "skipped": 0,  # Deprecated, keeping for compatibility
            },
            "by_query": {},
            "all_results": {},
        }

        # Add per-query details
        for query_id, results in all_results.items():
            query_success = sum(
                1 for r in results if r.status == DownloadStatus.SUCCESS
            )
            query_existed = sum(
                1 for r in results if r.status == DownloadStatus.ALREADY_EXISTED
            )
            query_failed = sum(1 for r in results if r.status == DownloadStatus.FAILED)
            query_manual = sum(
                1 for r in results if r.status == DownloadStatus.MANUAL_REQUIRED
            )

            project_report["by_query"][query_id] = {
                "total_papers": len(results),
                "successful_downloads": query_success,
                "already_existed": query_existed,
                "failed_downloads": query_failed,
                "manual_required": query_manual,
                "skipped": 0,
            }

            project_report["all_results"][query_id] = [r.to_dict() for r in results]

        # Write project JSON report
        json_file = (
            self.reports_path / f"project_download_status_{project_id}_{timestamp}.json"
        )
        with open(json_file, "w") as f:
            json.dump(project_report, f, indent=2)

        # Write latest project status
        latest_file = (
            self.reports_path / f"project_download_status_{project_id}_latest.json"
        )
        with open(latest_file, "w") as f:
            json.dump(project_report, f, indent=2)

        # Generate project text summary
        summary_file = (
            self.reports_path / f"project_download_summary_{project_id}_{timestamp}.txt"
        )
        with open(summary_file, "w") as f:
            f.write(f"PROJECT PDF DOWNLOAD SUMMARY - {project_id}\n")
            f.write(f"Generated: {timestamp}\n")
            f.write("=" * 70 + "\n\n")

            f.write("OVERALL STATISTICS\n")
            f.write(f"Total papers: {total_papers}\n")
            f.write(f"Successfully downloaded: {total_success}\n")
            f.write(f"Already existed: {total_already_existed}\n")
            f.write(f"Failed downloads: {total_failed}\n")
            f.write(f"Manual downloads required: {total_manual}\n\n")

            f.write("PER QUERY BREAKDOWN\n")
            f.write("-" * 40 + "\n")
            for query_id, results in all_results.items():
                query_success = sum(
                    1 for r in results if r.status == DownloadStatus.SUCCESS
                )
                query_existed = sum(
                    1 for r in results if r.status == DownloadStatus.ALREADY_EXISTED
                )
                query_failed = sum(
                    1 for r in results if r.status == DownloadStatus.FAILED
                )
                query_manual = sum(
                    1 for r in results if r.status == DownloadStatus.MANUAL_REQUIRED
                )

                f.write(f"\n{query_id} ({len(results)} papers):\n")
                f.write(f"  Downloaded: {query_success}\n")
                f.write(f"  Already existed: {query_existed}\n")
                f.write(f"  Failed: {query_failed}\n")
                f.write(f"  Manual required: {query_manual}\n")

        # Generate comprehensive manual download guide for all queries
        self._generate_project_manual_download_guide(
            project_id, all_results, papers_data, timestamp
        )

        self.logger.info(
            f"Project reports generated: {json_file.name}, {summary_file.name}"
        )
        print("📋 Project reports generated successfully!")

    def _generate_project_manual_download_guide(
        self,
        project_id: str,
        all_results: Dict[str, List[PaperDownloadResult]],
        papers_data: Dict[str, pd.DataFrame],
        timestamp: str,
    ) -> None:
        """Generate a comprehensive manual download guide for the entire project."""
        # Collect all successful downloads and manual required papers across all queries
        all_successful = []
        all_manual_required = []

        for query_id, results in all_results.items():
            if query_id not in papers_data:
                continue

            papers_df = papers_data[query_id]
            successful = [
                (r, papers_df, query_id)
                for r in results
                if r.status in [DownloadStatus.SUCCESS, DownloadStatus.ALREADY_EXISTED]
            ]
            manual = [
                (r, papers_df, query_id)
                for r in results
                if r.status == DownloadStatus.MANUAL_REQUIRED
            ]

            all_successful.extend(successful)
            all_manual_required.extend(manual)

        # Generate HTML guide
        html_file = (
            self.reports_path
            / f"project_manual_download_guide_{project_id}_{timestamp}.html"
        )
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(
                self._generate_project_manual_download_html(
                    project_id, all_successful, all_manual_required
                )
            )

        # Generate text guide
        text_file = (
            self.reports_path
            / f"project_manual_download_guide_{project_id}_{timestamp}.txt"
        )
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(
                self._generate_project_manual_download_text(
                    project_id, all_successful, all_manual_required
                )
            )

        self.logger.info(
            f"Project manual download guides generated: {html_file.name}, "
            f"{text_file.name}"
        )
        print(f"📋 Project manual download guide generated: {html_file.name}")

    def _generate_project_manual_download_html(
        self,
        project_id: str,
        all_successful: List[Tuple[PaperDownloadResult, pd.DataFrame, str]],
        all_manual_required: List[Tuple[PaperDownloadResult, pd.DataFrame, str]],
    ) -> str:
        """Generate HTML content for project-wide manual download guide."""
        total_papers = len(all_successful) + len(all_manual_required)

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Manual Download Guide - {project_id}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
        .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px;
           margin-bottom: 20px; }}

        .summary {{ background-color: #e8f5e8; padding: 15px; border-radius: 5px;
           margin-bottom: 20px; }}

        .paper {{ border: 1px solid #ddd; margin: 10px 0; padding: 15px;
           border-radius: 5px; }}

        .paper.manual {{ background-color: #fff5f5; }}
        .paper.success {{ background-color: #f0f8f0; }}
        .paper.existed {{ background-color: #f0f0ff; }}
        .paper-id {{ font-weight: bold; color: #333; }}
        .query-id {{ font-size: 0.9em; color: #666; background-color: #f5f5f5;
           padding: 2px 6px; border-radius: 3px; }}

        .title {{ font-size: 1.1em; font-weight: bold; color: #0066cc;
                  margin: 5px 0; }}
        .authors {{ font-style: italic; margin: 5px 0; }}
        .metadata {{ margin: 10px 0; }}
        .metadata-item {{ margin: 5px 0; }}
        .status {{ padding: 3px 8px; border-radius: 3px; font-size: 0.9em;
           font-weight: bold; }}

        .status.manual {{ background-color: #ffebee; color: #c62828; }}
        .status.success {{ background-color: #e8f5e8; color: #2e7d32; }}
        .status.existed {{ background-color: #e3f2fd; color: #1565c0; }}
        .instructions {{ background-color: #fff3cd; padding: 15px;
           border-radius: 5px; margin-bottom: 20px;
           border-left: 4px solid #ffc107; }}

    </style>
</head>
<body>
    <div class="header">
        <h1>📄 Project Manual Download Guide - {project_id}</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p><strong>Approach:</strong> Consolidated CSV with deduplicated papers</p>
        <p><strong>Directory:</strong> pdfs/automatic/ (unified structure)</p>
    </div>

    <div class="summary">
        <h2>📊 Download Summary</h2>
        <ul>
            <li><strong>Total unique papers:</strong> {total_papers}</li>
            <li><strong>✅ Successfully downloaded/existed:</strong> {
                len(all_successful)
            }</li>
            <li><strong>❌ Require manual download:</strong> {
                len(all_manual_required)
            }</li>
        </ul>
    </div>

    <div class="instructions" style="background-color: #fff3cd; padding: 15px;
         border-radius: 5px; margin-bottom: 20px; border-left: 4px solid #ffc107;">
        <h3>📝 Instructions for Manual Download</h3>
        <ol>
            <li>For each paper below marked as "Manual Required",
                try the provided URLs in order</li>
            <li>Look for PDF download links on the publisher's page</li>
            <li>If you have institutional access, try accessing through your
                library</li>
            <li>Save the PDF with the suggested filename in:
                <code>pdfs/automatic/</code></li>
            <li>The "Source Queries" field shows which queries this paper
                appeared in</li>
        </ol>
    </div>
"""

        # Add successfully processed papers section
        if all_successful:
            html += f"""
    <h2>✅ Successfully Processed Papers ({len(all_successful)})</h2>
"""
            for result, papers_df, query_id in all_successful:
                paper_data = papers_df.iloc[int(result.paper_id)]
                authors = paper_data.get("Authors", "Unknown Authors")
                year = paper_data.get("Year", "Unknown Year")

                status_class = (
                    "success" if result.status == DownloadStatus.SUCCESS else "existed"
                )
                status_icon = "✅" if result.status == DownloadStatus.SUCCESS else "📁"
                status_text = (
                    "DOWNLOADED"
                    if result.status == DownloadStatus.SUCCESS
                    else "ALREADY EXISTED"
                )

                html += f"""
    <div class="paper {status_class}">
        <div class="paper-id">Paper ID: {result.paper_id} <span class="query-id">
            Query: {query_id}</span></div>
        <div class="title">{result.title}</div>
        <div class="authors">{authors} ({year})</div>
        <div class="metadata">
            <span class="status {status_class}">{status_icon} {status_text}</span>
            <div>📁 File: {result.file_path.name if result.file_path else 'N/A'}</div>"""

        size_str = f"{result.file_size / 1024:.1f} KB" if result.file_size else "N/A"
        html += f"""            <div>📊 Size: {size_str}</div>
        </div>
    </div>
"""

        # Add manual download section
        if all_manual_required:
            html += f"""
    <h2>❌ Papers Requiring Manual Download ({len(all_manual_required)})</h2>
"""
            for result, papers_df, query_id in all_manual_required:
                paper_data = papers_df.iloc[int(result.paper_id)]

                authors = paper_data.get("Authors", "Unknown Authors")
                year = paper_data.get("Year", "Unknown Year")
                doi = paper_data.get("DOI", "")
                article_url = paper_data.get("ArticleURL", "")
                fulltext_url = paper_data.get("FullTextURL", "")
                source = paper_data.get("Source", "")
                publisher = paper_data.get("Publisher", "")
                abstract = paper_data.get("Abstract", "")
                # Clean NaN values
                if str(doi).lower() == "nan":
                    doi = ""
                if str(article_url).lower() == "nan":
                    article_url = ""
                if str(fulltext_url).lower() == "nan":
                    fulltext_url = ""
                if str(source).lower() == "nan":
                    source = "Unknown"
                if str(publisher).lower() == "nan":
                    publisher = "Unknown"
                if str(abstract).lower() == "nan":
                    abstract = ""

                # Generate suggested filename
                filename = self._generate_filename(
                    result.paper_id, authors, year, result.title
                )

                # Build citation
                citation = f"{authors} ({year}). {result.title}."
                if source and source != "Unknown":
                    citation += f" {source}."
                if doi:
                    citation += f" DOI: {doi}"

                html += f"""
    <div class="paper manual">
        <div class="paper-id">Paper ID: {result.paper_id} <span class="query-id">Query: {query_id}</span></div>
        <div class="title">{result.title}</div>
        <div class="authors">{authors} ({year})</div>
        <div class="metadata">
            <span class="status manual">❌ MANUAL REQUIRED</span>
            <div class="metadata-item"><strong>📁 Suggested filename:</strong> {filename}</div>
            <div class="metadata-item"><strong>📂 Save to:</strong> pdfs/automatic/</div>
            {(f'<div class="metadata-item"><strong>🔗 DOI:</strong> '
                    f'<a href="https://doi.org/{doi}" target="_blank">{doi}</a>'
                    f'</div>')
                    if doi and str(doi).lower() != 'nan' and doi.strip() else ''}
        </div>
    </div>
"""

        html += """
</body>
</html>"""

        return html

    def _generate_project_manual_download_text(
        self,
        project_id: str,
        all_successful: List[Tuple[PaperDownloadResult, pd.DataFrame, str]],
        all_manual_required: List[Tuple[PaperDownloadResult, pd.DataFrame, str]],
    ) -> str:
        """Generate text content for project-level manual download guide."""
        text = f"""PROJECT MANUAL DOWNLOAD GUIDE - {project_id}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'=' * 60}

SUMMARY:
- Successfully Downloaded: {len(all_successful)}
- Requiring Manual Download: {len(all_manual_required)}

"""

        if all_manual_required:
            text += (
                f"\nPAPERS REQUIRING MANUAL DOWNLOAD ({len(all_manual_required)}):\n"
            )
            text += "=" * 50 + "\n\n"

            for i, (result, _, _) in enumerate(all_manual_required, 1):
                text += f"{i}. {result.title}\n"
                text += f"   Paper ID: {result.paper_id}\n"
                if result.error_message:
                    text += f"   Issue: {result.error_message}\n"
                text += "\n"

        return text
