"""
Download management business logic for Papervisor web app (refactored).
"""

from pathlib import Path
import pandas as pd
from typing import Any, Dict, List, Optional
from papervisor.web.utils import get_downloaded_files_with_source, get_paper_urls
import time
import requests
import logging


class DownloadService:
    def __init__(self, papervisor: Any, data_dir: str):
        self.papervisor = papervisor
        self.data_dir = Path(data_dir)

    def get_download_data(self, project_id: str) -> Dict[str, Any]:
        """
        Returns papers, download_stats, and related info for the downloads page.
        Only uses reference records (is_reference == True) in consolidated_papers.csv.
        """
        project_path, papers_df = self._load_project_data(project_id)
        filtered_df = self._filter_reference_papers(papers_df)
        downloaded_files_info = get_downloaded_files_with_source(project_path)

        papers_data = self._process_papers_data(filtered_df, downloaded_files_info)

        return self._build_download_response(papers_data, papers_df)

    def _load_project_data(self, project_id: str) -> tuple[Path, Any]:
        """Load and validate project data."""
        current_project = self.papervisor.get_project(project_id)
        if not current_project:
            raise ValueError(f"Project '{project_id}' not found")
        project_path = self.data_dir / current_project.project_path
        consolidated_path = project_path / "pdfs" / "consolidated_papers.csv"
        if not consolidated_path.exists():
            raise FileNotFoundError(
                "No consolidated papers file found. Please run the download process first."
            )
        papers_df = pd.read_csv(consolidated_path)
        logging.debug(
            f"Loaded consolidated_papers.csv with shape: {papers_df.shape} and columns: {list(papers_df.columns)}"
        )
        return project_path, papers_df

    def _filter_reference_papers(self, papers_df: Any) -> Any:
        """Filter to only reference records."""
        if "is_reference" in papers_df.columns:
            ref_col = papers_df["is_reference"]
            return papers_df[
                (ref_col)
                | (ref_col == 1)
                | (ref_col.astype(str).str.lower() == "true")
                | (ref_col.astype(str) == "1")
            ].copy()
        else:
            return papers_df.copy()  # fallback: show all if column missing

    def _process_papers_data(
        self, filtered_df: Any, downloaded_files_info: Any
    ) -> list[Dict[str, Any]]:
        """Process DataFrame rows into papers data."""
        papers_data = []
        downloaded_files = [info["filename"] for info in downloaded_files_info]

        for idx, paper in filtered_df.iterrows():
            logging.debug(
                f"[PAPER LOOP] idx={idx}, type={type(paper)}, paper={repr(paper)}"
            )
            if not hasattr(paper, "get") or paper.isnull().all():
                logging.debug(
                    f"[PAPER LOOP] Skipping row idx={idx}: not Series or all NaN"
                )
                continue

            try:
                paper_data = self._extract_paper_data(
                    paper, idx, downloaded_files, downloaded_files_info
                )
                papers_data.append(paper_data)
            except Exception as e:
                logging.exception(f"[PAPER LOOP] Exception for idx={idx}: {e}")
                continue

        return papers_data

    def _extract_paper_data(
        self,
        paper: Any,
        idx: Any,
        downloaded_files: list[str],
        downloaded_files_info: Any,
    ) -> Dict[str, Any]:
        """Extract data for a single paper."""
        idx_int = int(str(idx))
        paper_id = str(paper.get("paper_id", idx_int))

        # Basic paper info
        title = paper.get("title", paper.get("Title", "Unknown Title"))
        authors = paper.get("authors", paper.get("Authors", "Unknown Authors"))
        year = paper.get("year", paper.get("Year", "Unknown"))
        source_queries = paper.get("source_queries", "")
        doi = paper.get("DOI", "")
        if pd.isna(doi):
            doi = ""

        # Download status
        filename_pattern = f"{paper_id}_"
        is_downloaded = any(f.startswith(filename_pattern) for f in downloaded_files)
        downloaded_file, download_source = self._find_downloaded_file(
            paper_id, downloaded_files_info
        )

        # URLs and status
        urls = get_paper_urls(paper) if hasattr(paper, "get") else []
        url_data = self._extract_url_data(paper)

        return {
            "paper_id": paper_id,
            "title": title,
            "authors": authors,
            "year": year,
            "source_queries": source_queries,
            "is_downloaded": is_downloaded,
            "downloaded_file": downloaded_file,
            "download_source": download_source,
            "urls": urls,
            "doi": str(doi) if not pd.isna(doi) else "",
            "has_duplicates": False,
            "duplicate_count": 0,
            "auto_download_failed": not is_downloaded and download_source is None,
            "manual_download_failed": False,
            **url_data,
        }

    def _find_downloaded_file(
        self, paper_id: str, downloaded_files_info: Any
    ) -> tuple[Any, Any]:
        """Find downloaded file and source for a paper."""
        filename_pattern = f"{paper_id}_"
        for file_info in downloaded_files_info:
            if file_info["filename"].startswith(filename_pattern):
                return file_info["filename"], file_info["source"]
        return None, None

    def _extract_url_data(self, paper: Any) -> Dict[str, str]:
        """Extract URL-related data from paper."""
        auto_download_status = paper.get("auto_download_status", "")
        auto_download_message = str(paper.get("auto_download_message", "") or "")
        if len(auto_download_message) > 60:
            auto_download_message = auto_download_message[:57] + "..."

        original_url = paper.get("FullTextURL") or paper.get("article_url") or ""
        if pd.isna(original_url):
            original_url = ""
        original_url = str(original_url)

        available_url = str(paper.get("available_url", "") or "")
        if pd.isna(available_url):
            available_url = ""

        downloaded_file_url = available_url
        if downloaded_file_url and "/" in downloaded_file_url:
            downloaded_file_url = downloaded_file_url.split("/")[-1]

        manual_dw_file_url = str(paper.get("manual_dw_file_url", "") or "")
        if pd.isna(manual_dw_file_url):
            manual_dw_file_url = ""
        manual_dw_file_url = (
            manual_dw_file_url.split("/")[-1] if manual_dw_file_url else ""
        )

        return {
            "auto_download_status": auto_download_status,
            "auto_download_message": auto_download_message,
            "original_url": original_url,
            "downloaded_file_url": downloaded_file_url,
            "available_url": available_url,
            "manual_dw_file_url": manual_dw_file_url,
        }

    def _build_download_response(
        self, papers_data: list[Dict[str, Any]], papers_df: Any
    ) -> Dict[str, Any]:
        """Build the final response dictionary."""
        return {
            "papers": papers_data,
            "download_stats": {},  # TODO: Add download statistics logic here
            "total_papers": len(papers_data),
            "downloaded_count": sum(
                1 for p in papers_data if p["auto_download_status"] == "Downloaded"
            ),
            "manual_count": len(papers_data)
            - sum(1 for p in papers_data if p["auto_download_status"] == "Downloaded"),
            "total_papers_in_file": len(papers_df),
            "total_after_duplicate_filter": len(papers_data),
        }

    def download_query_pdfs(
        self,
        project_path: Path,
        query_id: str,
        papers_df: pd.DataFrame,
        max_downloads: Optional[int] = None,
    ) -> List[Any]:
        """Download PDFs for all papers in a query result."""
        query_auto_dir = project_path / "pdfs" / "automatic" / query_id
        query_auto_dir.mkdir(parents=True, exist_ok=True)
        results = []
        papers_to_process = (
            papers_df.head(max_downloads) if max_downloads else papers_df
        )
        for idx, paper in papers_to_process.iterrows():
            try:
                result = self._download_paper_pdf(paper, query_auto_dir, query_id)
                results.append(result)
                if result["status"] == "success":
                    time.sleep(1.0)
            except Exception as e:
                result = {
                    "paper_id": str(idx),
                    "title": paper.get("Title", "Unknown"),
                    "status": "failed",
                    "error_message": str(e),
                }
                results.append(result)
        self._generate_reports(project_path, query_id, results)
        return results

    def download_project_pdfs(
        self,
        project_path: Path,
        project_id: str,
        query_ids: List[str],
        papers_data: Dict[str, pd.DataFrame],
        max_downloads: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Download PDFs for all queries in a project."""
        all_results = {}
        for query_id, df in papers_data.items():
            try:
                results = self.download_query_pdfs(
                    project_path, query_id, df, max_downloads
                )
                all_results[query_id] = results
            except Exception:
                all_results[query_id] = []
        self._generate_project_reports(
            project_path, project_id, all_results, papers_data
        )
        return all_results

    def download_consolidated_pdfs(
        self,
        project_path: Path,
        project_id: str,
        consolidated_df: pd.DataFrame,
        max_downloads: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Download PDFs using the consolidated CSV approach."""
        output_dir = project_path / "pdfs" / "automatic"
        output_dir.mkdir(parents=True, exist_ok=True)
        results = []
        # Process downloads with proper type handling
        processed_count = 0
        for row_idx, paper_series in consolidated_df.iterrows():
            if max_downloads and processed_count >= max_downloads:
                break

            # Convert Series to dict for processing
            paper_dict = paper_series.to_dict()
            idx = processed_count
            # Download and update status
            result = self._download_paper_pdf(
                paper_dict, output_dir, "consolidated", idx
            )
            results.append(result)

            # Update DataFrame columns directly (MyPy type-safe approach)
            if result["status"] == "success":
                # Use .at for scalar assignment which is more type-safe
                consolidated_df.at[row_idx, "auto_download_status"] = "Downloaded"  # type: ignore
                consolidated_df.at[row_idx, "auto_download_message"] = ""  # type: ignore
                consolidated_df.at[row_idx, "available_url"] = result.get("file_path", "")  # type: ignore
                # Save the actual filename for serving
                if result.get("file_path"):
                    consolidated_df.at[row_idx, "downloaded_file"] = Path(result["file_path"]).name  # type: ignore
                else:
                    consolidated_df.at[row_idx, "downloaded_file"] = ""  # type: ignore
            else:
                consolidated_df.at[row_idx, "auto_download_status"] = "Failed"  # type: ignore
                consolidated_df.at[row_idx, "auto_download_message"] = result.get("error", "")  # type: ignore
                consolidated_df.at[row_idx, "available_url"] = ""  # type: ignore
                consolidated_df.at[row_idx, "downloaded_file"] = ""  # type: ignore

            # Save after each paper for live UI updates
            consolidated_path = project_path / "pdfs" / "consolidated_papers.csv"
            consolidated_df.to_csv(consolidated_path, index=False)
            time.sleep(1.0)  # polite delay

            processed_count += 1
        # Return results organized by source query for compatibility
        return self._organize_results_by_source_queries(consolidated_df, results)

    def resolve_pdf_url(self, paper: Dict[str, Any]) -> Optional[str]:
        """
        Try to resolve a PDF URL for a paper using OA APIs and publisher heuristics.
        Returns a valid PDF URL string or None if not found.
        """
        doi = self._extract_doi(paper)

        # Try open access APIs first
        if doi:
            url = self._try_unpaywall(doi)
            if url:
                return url
            url = self._try_openalex(doi)
            if url:
                return url
            url = self._try_semantic_scholar(doi)
            if url:
                return url

        # Try publisher heuristics
        url = self._try_publisher_heuristics(paper)
        if url:
            return url

        # Fallback to existing PDF URLs
        return self._try_fallback_urls(paper)

    def _extract_doi(self, paper: Dict[str, Any]) -> Optional[str]:
        """Extract and normalize DOI from paper data."""
        doi = paper.get("DOI") or paper.get("doi")
        if doi and isinstance(doi, str):
            doi = doi.strip().lower()
            if doi.startswith("http"):
                doi = doi.split("doi.org/")[-1]
            return str(doi)
        return None

    def _try_unpaywall(self, doi: str) -> Optional[str]:
        """Try to get PDF URL from Unpaywall API."""
        try:
            r = requests.get(
                f"https://api.unpaywall.org/v2/{doi}?email=demo@papervisor.org",
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                unpaywall_url = data.get("best_oa_location", {}).get("url_for_pdf")
                if (
                    unpaywall_url
                    and isinstance(unpaywall_url, str)
                    and unpaywall_url.lower().endswith(".pdf")
                ):
                    return str(unpaywall_url)
        except Exception as e:
            print(f"[OA] Unpaywall error for DOI {doi}: {e}")
        return None

    def _try_openalex(self, doi: str) -> Optional[str]:
        """Try to get PDF URL from OpenAlex API."""
        try:
            r = requests.get(
                f"https://api.openalex.org/works/https://doi.org/{doi}", timeout=10
            )
            if r.status_code == 200:
                data = r.json()
                for loc in data.get("primary_location", {}), *data.get(
                    "alternate_locations", []
                ):
                    if loc and loc.get("pdf_url"):
                        openalex_url = loc["pdf_url"]
                        if isinstance(
                            openalex_url, str
                        ) and openalex_url.lower().endswith(".pdf"):
                            return str(openalex_url)
        except Exception as e:
            print(f"[OA] OpenAlex error for DOI {doi}: {e}")
        return None

    def _try_semantic_scholar(self, doi: str) -> Optional[str]:
        """Try to get PDF URL from Semantic Scholar API."""
        try:
            r = requests.get(
                f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=title,openAccessPdf",
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                semantic_url = data.get("openAccessPdf", {}).get("url")
                if (
                    semantic_url
                    and isinstance(semantic_url, str)
                    and semantic_url.lower().endswith(".pdf")
                ):
                    return str(semantic_url)
        except Exception as e:
            print(f"[OA] Semantic Scholar error for DOI {doi}: {e}")
        return None

    def _try_publisher_heuristics(self, paper: Dict[str, Any]) -> Optional[str]:
        """Try publisher-specific URL patterns."""
        article_url = paper.get("article_url") or paper.get("FullTextURL")
        if not (article_url and isinstance(article_url, str)):
            return None

        # Springer
        if "link.springer.com" in article_url and "/article/" in article_url:
            return str(article_url.replace("/article/", "/content/pdf/") + ".pdf")

        # Elsevier/ScienceDirect
        if "sciencedirect.com/science/article/pii/" in article_url:
            pii = article_url.split("pii/")[-1].split("/")[0]
            return f"https://www.sciencedirect.com/science/article/pii/{pii}/pdfft?isDTMRedir=true&download=true"

        # IEEE Xplore
        if "ieeexplore.ieee.org/document/" in article_url:
            doc_id = article_url.split("/document/")[-1].split("/")[0]
            return f"https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={doc_id}"

        return None

    def _try_fallback_urls(self, paper: Dict[str, Any]) -> Optional[str]:
        """Try any available URL that looks like a PDF."""
        for k in ["FullTextURL", "article_url", "available_url"]:
            url = paper.get(k)
            if url and isinstance(url, str) and url.lower().endswith(".pdf"):
                return str(url)
        return None

    def _download_paper_pdf(
        self, paper: Any, output_dir: Path, query_id: str, row_idx: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Attempt to download a PDF for a paper using the correct PDF URL column.
        Returns a dict with status, file path, and error message if any.
        Logs each attempt to the server console for monitoring.
        """
        paper_id = str(
            paper.get(
                "ID",
                (
                    row_idx
                    if row_idx is not None
                    else paper.get("paper_id", paper.get("id", "unknown"))
                ),
            )
        )
        title = paper.get("title", paper.get("Title", "Unknown Title"))
        # Use 'FullTextURL' if present, otherwise 'article_url' for the PDF URL
        url = paper.get("FullTextURL")
        if not (url and isinstance(url, str) and url.lower().startswith("http")):
            url = paper.get("article_url")
            if not (url and isinstance(url, str) and url.lower().startswith("http")):
                # Try OA APIs and heuristics
                url = self.resolve_pdf_url(paper)
        print(
            f'[DOWNLOAD] Attempting download for paper_id={paper_id}, title="{title}", url={url}'
        )
        if not url:
            print(f"[DOWNLOAD] FAILED: No valid PDF URL found for paper_id={paper_id}")
            return {
                "status": "failed",
                "error": "No valid PDF URL found",
                "file_path": None,
            }
        try:
            response = requests.get(url, timeout=20)
            if response.status_code == 200 and response.headers.get(
                "content-type", ""
            ).startswith("application/pdf"):
                filename = f"{paper_id}_{query_id}.pdf"
                file_path = output_dir / filename
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"[DOWNLOAD] SUCCESS: Saved to {file_path}")
                return {"status": "success", "file_path": str(file_path), "url": url}
            else:
                print(
                    f"[DOWNLOAD] FAILED: HTTP {response.status_code} or not a PDF for paper_id={paper_id}"
                )
                return {
                    "status": "failed",
                    "error": f"HTTP {response.status_code} or not a PDF",
                    "file_path": None,
                    "url": url,
                }
        except Exception as e:
            print(f"[DOWNLOAD] FAILED: Exception for paper_id={paper_id}: {e}")
            return {"status": "failed", "error": str(e), "file_path": None, "url": url}

    def _generate_reports(
        self, project_path: Path, query_id: str, results: List[Any]
    ) -> None:
        # TODO: Move report generation logic to a shared utility or here directly.
        pass

    def _generate_project_reports(
        self,
        project_path: Path,
        project_id: str,
        all_results: Dict[str, Any],
        papers_data: Dict[str, Any],
    ) -> None:
        # Optionally migrate this logic from PDFDownloader
        pass

    def _organize_results_by_source_queries(
        self, consolidated_df: Any, results: List[Any]
    ) -> Dict[str, List[Any]]:
        # Organize results by source query for compatibility with legacy interface
        # For now, return all results under a 'consolidated' key
        return {"consolidated": results}
