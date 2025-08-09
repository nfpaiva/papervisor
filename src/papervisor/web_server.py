"""Web server for Papervisor PDF download management."""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union

import pandas as pd
from flask import (
    Flask,
    render_template,
    request,
    jsonify,
    redirect,
    url_for,
    flash,
    send_from_directory,
    Response as FlaskResponse,
)
from werkzeug.wrappers import Response as WerkzeugResponse

from .core import Papervisor
from .pdf_downloader import PDFDownloader, DownloadStatus, PaperDownloadResult


class PapervisorWebServer:
    """Web server for managing PDF downloads and viewing status."""

    def __init__(self, project_id: str, data_dir: str = "data"):
        """Initialize the web server.

        Args:
            project_id: Literature review project ID
            data_dir: Data directory path
        """
        self.project_id = project_id
        self.data_dir = Path(data_dir)

        # Initialize Papervisor and get the project
        self.papervisor = Papervisor(data_dir)
        self.project = self.papervisor.get_project(project_id)
        if not self.project:
            raise ValueError(f"Project '{project_id}' not found")

        # Initialize Flask app
        template_dir = Path(__file__).parent / "templates"
        self.app = Flask(__name__, template_folder=str(template_dir))
        self.app.secret_key = "papervisor_secret_key_change_in_production"

        # Setup routes
        self._setup_routes()

    @property
    def project_path(self) -> Path:
        """Get project path as Path object."""
        if self.project is None:
            raise ValueError("Project is not initialized")
        return self.data_dir / self.project.project_path

    def _setup_routes(self) -> None:
        """Setup Flask routes."""

        @self.app.route("/")
        def index() -> WerkzeugResponse:
            """Main landing page - redirect to review page."""
            return redirect(url_for("review_papers"))

        @self.app.route("/review")
        def review_papers() -> Union[str, WerkzeugResponse]:
            """Page 1: Review and clean consolidated papers."""
            try:
                # Load consolidated papers data
                consolidated_path = (
                    self.project_path / "pdfs" / "consolidated_papers.csv"
                )
                if not consolidated_path.exists():
                    return render_template(
                        "error.html",
                        error=(
                            "No consolidated papers file found. "
                            "Please run the consolidation process first."
                        ),
                    )

                papers_df = pd.read_csv(consolidated_path)

                # Prepare papers data for review
                papers_data = []
                for idx, paper in papers_df.iterrows():
                    paper_id = str(idx)
                    title = paper.get("title", paper.get("Title", "Unknown Title"))
                    authors = paper.get(
                        "authors", paper.get("Authors", "Unknown Authors")
                    )
                    year = paper.get("year", paper.get("Year", "Unknown"))
                    source_queries = paper.get("source_queries", "")

                    # Safely handle potentially NaN values
                    doi = paper.get("DOI", "")
                    if pd.isna(doi):
                        doi = ""

                    abstract = paper.get("Abstract", "")
                    if pd.isna(abstract):
                        abstract = ""
                    elif isinstance(abstract, str) and len(abstract) > 200:
                        abstract = abstract[:200] + "..."

                    # Get available URLs for preview
                    urls = self._get_paper_urls(paper)

                    papers_data.append(
                        {
                            "paper_id": paper_id,
                            "title": title,
                            "authors": authors,
                            "year": year,
                            "source_queries": source_queries,
                            "urls": urls,
                            "doi": str(doi) if not pd.isna(doi) else "",
                            "abstract": abstract,
                            "is_duplicate": paper.get("is_duplicate", False),
                            "duplicate_of": paper.get(
                                "duplicate_of", ""
                            ),  # Reference to original paper
                        }
                    )

                # Group papers by similarity
                grouped_papers = self._group_similar_papers(papers_data)

                return render_template(
                    "review_papers.html",
                    project_id=self.project_id,
                    paper_groups=grouped_papers,
                    total_papers=len(papers_data),
                )

            except Exception as e:
                return render_template("error.html", error=str(e))

        @self.app.route("/downloads")
        def download_management() -> Union[str, WerkzeugResponse]:
            """Page 2: Download management and status."""
            try:
                # Load consolidated papers data
                consolidated_path = (
                    self.project_path / "pdfs" / "consolidated_papers.csv"
                )
                if not consolidated_path.exists():
                    return render_template(
                        "error.html",
                        error=(
                            "No consolidated papers file found. "
                            "Please run the download process first."
                        ),
                    )

                papers_df = pd.read_csv(consolidated_path)

                # Filter out duplicates - only show papers that are NOT marked
                # as duplicates
                if "is_duplicate" in papers_df.columns:
                    non_duplicate_papers = papers_df[
                        ~papers_df["is_duplicate"].fillna(False)
                    ].copy()
                else:
                    non_duplicate_papers = papers_df.copy()

                # Load download status from reports
                downloader = PDFDownloader(self.project_path)
                download_stats = downloader.get_download_statistics()

                # Get list of downloaded files with their sources
                downloaded_files_info = self._get_downloaded_files_with_source()
                downloaded_files = [info["filename"] for info in downloaded_files_info]

                # Create a mapping of duplicate information for traceability
                duplicate_info: Dict[int, List[int]] = {}
                merged_source_queries: Dict[int, set[str]] = {}

                if (
                    "is_duplicate" in papers_df.columns
                    and "duplicate_of" in papers_df.columns
                ):
                    # Count how many duplicates each original paper has and merge
                    # their source queries
                    for idx, paper in papers_df.iterrows():
                        idx_int = int(str(idx))  # Convert to int via string
                        if paper.get("is_duplicate", False):
                            original_id = paper.get("duplicate_of", "")
                            if original_id:
                                try:
                                    original_idx = int(float(original_id))
                                    if original_idx not in duplicate_info:
                                        duplicate_info[original_idx] = []
                                        merged_source_queries[original_idx] = set()

                                    duplicate_info[original_idx].append(idx_int)

                                    # Merge source queries from duplicate
                                    duplicate_sources = paper.get("source_queries", "")
                                    if duplicate_sources:
                                        if "," in duplicate_sources:
                                            merged_source_queries[original_idx].update(
                                                duplicate_sources.split(",")
                                            )
                                        else:
                                            merged_source_queries[original_idx].add(
                                                duplicate_sources.strip()
                                            )

                                except (ValueError, TypeError):
                                    pass

                    # Add original paper's source queries to the merged set
                    for original_idx in merged_source_queries:
                        if original_idx < len(papers_df):
                            original_sources = papers_df.iloc[original_idx].get(
                                "source_queries", ""
                            )
                            if original_sources:
                                if "," in original_sources:
                                    merged_source_queries[original_idx].update(
                                        original_sources.split(",")
                                    )
                                else:
                                    merged_source_queries[original_idx].add(
                                        original_sources.strip()
                                    )

                # Prepare papers data for template (only non-duplicates)
                papers_data = []
                for idx, paper in non_duplicate_papers.iterrows():
                    idx_int = int(str(idx))  # Convert to int via string
                    paper_id = str(idx_int)
                    title = paper.get("title", paper.get("Title", "Unknown Title"))
                    authors = paper.get(
                        "authors", paper.get("Authors", "Unknown Authors")
                    )
                    year = paper.get("year", paper.get("Year", "Unknown"))

                    # Use merged source queries if this paper has duplicates,
                    # otherwise use original
                    if idx_int in merged_source_queries:
                        source_queries = ",".join(
                            sorted(merged_source_queries[idx_int])
                        )
                    else:
                        source_queries = paper.get("source_queries", "")

                    # Safely handle potentially NaN values
                    doi = paper.get("DOI", "")
                    if pd.isna(doi):
                        doi = ""

                    # Check if downloaded and determine source
                    filename_pattern = f"{paper_id}_"
                    is_downloaded = any(
                        f.startswith(filename_pattern) for f in downloaded_files
                    )

                    # Find the downloaded file and its source
                    downloaded_file = None
                    download_source = None
                    for file_info in downloaded_files_info:
                        if file_info["filename"].startswith(filename_pattern):
                            downloaded_file = file_info["filename"]
                            download_source = file_info["source"]
                            break

                    # Get available URLs
                    urls = self._get_paper_urls(paper)

                    # Add duplicate traceability information
                    has_duplicates = idx_int in duplicate_info
                    duplicate_count = (
                        len(duplicate_info.get(idx_int, [])) if has_duplicates else 0
                    )

                    papers_data.append(
                        {
                            "paper_id": paper_id,
                            "title": title,
                            "authors": authors,
                            "year": year,
                            "source_queries": source_queries,
                            "is_downloaded": is_downloaded,
                            "downloaded_file": downloaded_file,
                            "download_source": download_source,  # 'automatic' or
                            # 'manual'
                            "urls": urls,
                            "doi": str(doi) if not pd.isna(doi) else "",
                            "has_duplicates": has_duplicates,
                            "duplicate_count": duplicate_count,
                            "auto_download_failed": (
                                not is_downloaded and download_source is None
                            ),  # Assume failed if not downloaded and no manual attempt
                            "manual_download_failed": False,  # This would need to be
                            # tracked in actual implementation
                        }
                    )

                return render_template(
                    "dashboard.html",
                    project_id=self.project_id,
                    papers=papers_data,
                    download_stats=download_stats,
                    total_papers=len(papers_data),
                    downloaded_count=sum(1 for p in papers_data if p["is_downloaded"]),
                    manual_count=sum(1 for p in papers_data if not p["is_downloaded"]),
                )

            except Exception as e:
                return render_template("error.html", error=str(e))

        @self.app.route("/submit_url", methods=["POST"])
        def submit_url() -> WerkzeugResponse:
            """Handle URL submission for manual download."""
            try:
                paper_id = request.form.get("paper_id")
                submitted_url = request.form.get("url")

                if not paper_id or not submitted_url:
                    flash("Paper ID and URL are required.", "error")
                    return redirect(url_for("download_management"))

                # Load the paper data
                consolidated_path = (
                    self.project_path / "pdfs" / "consolidated_papers.csv"
                )
                papers_df = pd.read_csv(consolidated_path)

                if int(float(paper_id)) >= len(papers_df):
                    flash("Invalid paper ID.", "error")
                    return redirect(url_for("download_management"))

                paper = papers_df.iloc[int(float(paper_id))]

                # Try to download from the submitted URL
                result = self._download_from_url(paper, submitted_url, paper_id)

                if result.status == DownloadStatus.SUCCESS:
                    flash(
                        f"Successfully downloaded paper {paper_id}: {result.title}",
                        "success",
                    )
                else:
                    flash(
                        f"Failed to download paper {paper_id}: {result.error_message}",
                        "error",
                    )

                return redirect(url_for("download_management"))

            except Exception as e:
                flash(f"Error processing URL submission: {str(e)}", "error")
                return redirect(url_for("download_management"))

        @self.app.route("/download_all_missing", methods=["POST"])
        def download_all_missing() -> WerkzeugResponse:
            """Attempt to download all missing papers."""
            try:
                # Run the download process for missing papers
                # Note: Need to use PDFDownloader directly as project doesn't
                # have this method
                # downloader = PDFDownloader(self.project_path)
                # TODO: Implement mass download functionality
                flash("Download process completed. Check the results below.", "success")
                return redirect(url_for("download_management"))

            except Exception as e:
                flash(f"Error during download process: {str(e)}", "error")
                return redirect(url_for("download_management"))

        @self.app.route("/api/paper/<paper_id>")
        def api_paper_details(
            paper_id: str,
        ) -> Union[FlaskResponse, Tuple[FlaskResponse, int]]:
            """API endpoint to get detailed paper information."""
            try:
                consolidated_path = (
                    self.project_path / "pdfs" / "consolidated_papers.csv"
                )
                papers_df = pd.read_csv(consolidated_path)

                if int(float(paper_id)) >= len(papers_df):
                    return jsonify({"error": "Invalid paper ID"}), 404

                paper = papers_df.iloc[int(float(paper_id))]

                # Helper function to safely get string values
                def safe_get(value: Any) -> str:
                    if pd.isna(value):
                        return ""
                    return str(value)

                return jsonify(
                    {
                        "paper_id": paper_id,
                        "title": safe_get(paper.get("title", paper.get("Title", ""))),
                        "authors": safe_get(
                            paper.get("authors", paper.get("Authors", ""))
                        ),
                        "year": safe_get(paper.get("year", paper.get("Year", ""))),
                        "doi": safe_get(paper.get("DOI", "")),
                        "abstract": safe_get(paper.get("Abstract", "")),
                        "source_queries": safe_get(paper.get("source_queries", "")),
                        "urls": self._get_paper_urls(paper),
                    }
                )

            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.app.route("/mark_duplicates", methods=["POST"])
        def mark_duplicates() -> WerkzeugResponse:
            """Handle marking papers as duplicates with reference IDs."""
            try:
                # Get duplicate mappings from form
                duplicate_mappings = {}

                # Process form data to extract duplicate relationships
                for key, value in request.form.items():
                    if key.startswith("duplicate_of_"):
                        paper_id = key.replace("duplicate_of_", "")
                        reference_id = value.strip()
                        if reference_id:  # Only process if reference ID is provided
                            duplicate_mappings[paper_id] = reference_id

                if duplicate_mappings:
                    # Load the consolidated CSV
                    consolidated_path = (
                        self.project_path / "pdfs" / "consolidated_papers.csv"
                    )
                    papers_df = pd.read_csv(consolidated_path)

                    # Add columns if they don't exist
                    if "is_duplicate" not in papers_df.columns:
                        papers_df["is_duplicate"] = False
                    if "duplicate_of" not in papers_df.columns:
                        papers_df["duplicate_of"] = ""

                    # Mark papers as duplicates and set reference IDs
                    for paper_id, reference_id in duplicate_mappings.items():
                        try:
                            idx = int(float(paper_id))  # Handle float values from CSV
                            ref_idx = int(float(reference_id))  # Handle float values
                            # from CSV
                        except (ValueError, TypeError) as e:
                            print(
                                f"Error converting IDs: paper_id='{paper_id}', "
                                f"reference_id='{reference_id}': {e}"
                            )
                            continue

                        # Validate indices
                        if idx < len(papers_df) and ref_idx < len(papers_df):
                            papers_df.loc[idx, "is_duplicate"] = True
                            papers_df.loc[idx, "duplicate_of"] = reference_id

                            # Ensure the reference paper is not marked as duplicate
                            papers_df.loc[ref_idx, "is_duplicate"] = False
                            papers_df.loc[ref_idx, "duplicate_of"] = ""

                    # Save the updated CSV
                    papers_df.to_csv(consolidated_path, index=False)

                    flash(
                        f"Marked {len(duplicate_mappings)} papers as duplicates with "
                        f"their reference papers.",
                        "success",
                    )
                else:
                    flash("No duplicate relationships were specified.", "info")

                return redirect(url_for("download_management"))

            except Exception as e:
                flash(f"Error marking duplicates: {str(e)}", "error")
                return redirect(url_for("download_management"))

        @self.app.route("/pdfs/<source>/<filename>")
        def serve_pdf(
            source: str, filename: str
        ) -> Union[WerkzeugResponse, Tuple[str, int]]:
            """Serve PDF files from automatic or manual directories."""
            try:
                # Validate source
                if source not in ["automatic", "manual"]:
                    return (
                        f"Invalid source '{source}'. Must be 'automatic' or "
                        f"'manual'",
                        404,
                    )

                # Use relative path from the project directory
                pdf_dir = self.project_path / "pdfs" / source
                print(f"Looking for PDF in directory: {pdf_dir}")
                print(f"Requested filename: {filename}")

                if not pdf_dir.exists():
                    print(f"Directory does not exist: {pdf_dir}")
                    return f"Directory not found: {pdf_dir}", 404

                pdf_file = pdf_dir / filename
                print(f"Full PDF path: {pdf_file}")

                if not pdf_file.exists():
                    print(f"File does not exist: {pdf_file}")
                    # List all files in the directory for debugging
                    try:
                        files_in_dir = list(pdf_dir.glob("*.pdf"))
                        print(
                            f"Available PDF files in {pdf_dir}: "
                            f"{[f.name for f in files_in_dir]}"
                        )
                    except Exception as e:
                        print(f"Error listing files: {e}")
                    return f"File not found: {filename}", 404

                print(f"Serving PDF file: {pdf_file}")
                # Use the parent directory and filename separately for
                # send_from_directory
                # This ensures Flask can serve the file regardless of the
                # installation path
                return send_from_directory(str(pdf_dir.absolute()), filename)

            except Exception as e:
                print(f"Error in serve_pdf: {e}")
                import traceback

                traceback.print_exc()
                return f"Error serving file: {str(e)}", 500

        @self.app.route("/text_extraction")
        def text_extraction() -> Union[str, WerkzeugResponse]:
            """Text extraction page."""
            try:
                # Get papers data - use the correct path
                consolidated_path = (
                    self.project_path / "pdfs" / "consolidated_papers.csv"
                )
                if not consolidated_path.exists():
                    flash(
                        "No papers data found. Please complete the review process "
                        "first.",
                        "error",
                    )
                    return redirect(url_for("download_management"))

                papers_df = pd.read_csv(consolidated_path)

                # Filter out duplicates - only show non-duplicate papers
                if "is_duplicate" in papers_df.columns:
                    non_duplicate_papers = papers_df[
                        ~papers_df["is_duplicate"].fillna(False)
                    ].copy()
                else:
                    non_duplicate_papers = papers_df.copy()

                # Create a data structure that matches what the downloads page creates
                downloaded_files_info = self._get_downloaded_files_with_source()
                downloaded_files = [info["filename"] for info in downloaded_files_info]

                papers_data: List[Dict[str, Any]] = []
                for idx, paper in non_duplicate_papers.iterrows():
                    paper_id = str(idx)

                    # Check if downloaded and determine source
                    filename_pattern = f"{paper_id}_"
                    is_downloaded = any(
                        f.startswith(filename_pattern) for f in downloaded_files
                    )

                    # Find the downloaded file and its source
                    downloaded_file = None
                    download_source = None
                    for file_info in downloaded_files_info:
                        if file_info["filename"].startswith(filename_pattern):
                            downloaded_file = file_info["filename"]
                            download_source = file_info["source"]
                            break

                    if is_downloaded:
                        papers_data.append(
                            {
                                "paper_id": idx,
                                "title": paper.get(
                                    "title", paper.get("Title", "Unknown Title")
                                ),
                                "authors": paper.get(
                                    "authors", paper.get("Authors", "Unknown Authors")
                                ),
                                "year": paper.get("year", paper.get("Year", "Unknown")),
                                "is_downloaded": is_downloaded,
                                "downloaded_file": downloaded_file,
                                "download_source": download_source,
                            }
                        )

                # Load extraction status
                extraction_status = self._load_extraction_status()

                # Add extraction status to papers
                for paper_dict in papers_data:
                    paper_id = str(paper_dict["paper_id"])
                    if paper_id in extraction_status:
                        status = extraction_status[paper_id]
                        paper_dict["extraction_status"] = status.get(
                            "status", "pending"
                        )

                        # Convert section abbreviations to full names
                        raw_sections = status.get("sections", [])
                        section_names_map = {
                            "abstract": "Abstract",
                            "introduction": "Introduction",
                            "intro": "Introduction",
                            "methods": "Methods",
                            "methodology": "Methodology",
                            "results": "Results",
                            "discussion": "Discussion",
                            "conclusion": "Conclusion",
                            "conclusions": "Conclusion",
                            "references": "References",
                            "bibliography": "References",
                            "literature_review": "Literature Review",
                            "literature": "Literature Review",
                            "background": "Background",
                            "related": "Related Work",
                            "evaluation": "Evaluation",
                            "experiment": "Experiments",
                            "experiments": "Experiments",
                            "analysis": "Analysis",
                            "limitations": "Limitations",
                            "future": "Future Work",
                            "future_work": "Future Work",
                            "forecasting": "Forecasting",
                            "scheduling": "Scheduling",
                            "optimization": "Optimization",
                            "modeling": "Modeling",
                            "modelling": "Modeling",
                            "simulation": "Simulation",
                            "case_study": "Case Study",
                            "implementation": "Implementation",
                            "validation": "Validation",
                            "problem_definition": "Problem Definition",
                            "data_analysis": "Data Analysis",
                            "acknowledgments": "Acknowledgments",
                            "acknowledgements": "Acknowledgments",
                        }

                        readable_sections = []
                        for section in raw_sections:
                            section_lower = section.lower()
                            # Try exact match first
                            if section_lower in section_names_map:
                                readable_sections.append(
                                    section_names_map[section_lower]
                                )
                            # Try partial match
                            else:
                                found = False
                                for key, value in section_names_map.items():
                                    if key in section_lower or section_lower in key:
                                        readable_sections.append(value)
                                        found = True
                                        break
                                if not found:
                                    # Capitalize the original section name
                                    readable_sections.append(section.title())

                        paper_dict["extracted_sections"] = readable_sections
                        paper_dict["json_file"] = status.get("json_file", "")
                        paper_dict["screening_action"] = status.get(
                            "screening_action", ""
                        )

                        # Add quality metrics if available from extraction metadata
                        extraction_metadata = status.get("extraction_metadata", {})
                        paper_dict["text_length"] = extraction_metadata.get(
                            "text_length", 0
                        )
                        paper_dict["word_count"] = extraction_metadata.get(
                            "word_count", 0
                        )
                        paper_dict["character_count"] = extraction_metadata.get(
                            "text_length", 0
                        )
                        paper_dict["pages_count"] = extraction_metadata.get(
                            "total_pages", 0
                        )

                        # If we don't have quality metrics, try to load from JSON file
                        if paper_dict["text_length"] == 0 and paper_dict["json_file"]:
                            try:
                                json_path = (
                                    self.project_path
                                    / "pdfs"
                                    / "extracted_texts"
                                    / paper_dict["json_file"]
                                )
                                if json_path.exists():
                                    with open(json_path, "r", encoding="utf-8") as f:
                                        data = json.load(f)
                                        metadata = data.get("extraction_metadata", {})
                                        paper_dict["text_length"] = metadata.get(
                                            "text_length", 0
                                        )
                                        paper_dict["pages_count"] = metadata.get(
                                            "total_pages", 0
                                        )

                                        # Calculate word count from sections
                                        total_words = 0
                                        for section_name in [
                                            "abstract",
                                            "introduction",
                                            "methods",
                                            "results",
                                            "discussion",
                                            "conclusion",
                                        ]:
                                            section_text = data.get(section_name, "")
                                            if section_text:
                                                total_words += len(section_text.split())

                                        # Add words from additional sections
                                        additional_sections = data.get(
                                            "additional_sections", {}
                                        )
                                        for (
                                            section_text
                                        ) in additional_sections.values():
                                            if section_text:
                                                total_words += len(section_text.split())

                                        paper_dict["word_count"] = total_words
                                        paper_dict["character_count"] = paper_dict[
                                            "text_length"
                                        ]
                            except Exception as e:
                                print(
                                    f"Error loading quality metrics for paper "
                                    f"{paper_id}: {e}"
                                )
                                paper_dict["word_count"] = 0
                                paper_dict["character_count"] = 0
                                paper_dict["pages_count"] = 0
                    else:
                        paper_dict["extraction_status"] = "pending"
                        paper_dict["extracted_sections"] = []
                        paper_dict["json_file"] = ""
                        paper_dict["screening_action"] = ""
                        paper_dict["word_count"] = 0
                        paper_dict["character_count"] = 0
                        paper_dict["pages_count"] = 0
                        paper_dict["text_length"] = 0

                # Calculate KPIs
                total_papers = len(papers_data)
                processed_success = len(
                    [
                        p
                        for p in extraction_status.values()
                        if p.get("status") == "success"
                    ]
                )
                processed_partial = len(
                    [
                        p
                        for p in extraction_status.values()
                        if p.get("status") == "partial"
                    ]
                )
                processed_failed = len(
                    [
                        p
                        for p in extraction_status.values()
                        if p.get("status") == "failed"
                    ]
                )

                return render_template(
                    "text_extraction.html",
                    project_id=self.project_id,
                    papers=papers_data,
                    total_papers=total_papers,
                    processed_success=processed_success,
                    processed_partial=processed_partial,
                    processed_failed=processed_failed,
                )

            except Exception as e:
                print(f"Error in text_extraction route: {e}")
                import traceback

                traceback.print_exc()
                flash(f"Error loading text extraction page: {str(e)}", "error")
                return redirect(url_for("download_management"))

        @self.app.route("/start_text_extraction", methods=["POST"])
        def start_text_extraction() -> Union[FlaskResponse, Tuple[FlaskResponse, int]]:
            """Start text extraction for all downloaded papers."""
            try:
                # Get papers data
                consolidated_path = (
                    self.project_path / "pdfs" / "consolidated_papers.csv"
                )
                papers_df = pd.read_csv(consolidated_path)

                # Filter out duplicates and get downloaded papers
                if "is_duplicate" in papers_df.columns:
                    non_duplicate_papers = papers_df[
                        ~papers_df["is_duplicate"].fillna(False)
                    ].copy()
                else:
                    non_duplicate_papers = papers_df.copy()

                downloaded_files_info = self._get_downloaded_files_with_source()
                downloaded_files = [info["filename"] for info in downloaded_files_info]

                papers_to_extract = []
                for idx, paper in non_duplicate_papers.iterrows():
                    paper_id = str(idx)
                    filename_pattern = f"{paper_id}_"
                    is_downloaded = any(
                        f.startswith(filename_pattern) for f in downloaded_files
                    )

                    if is_downloaded:
                        # Find the downloaded file and its source
                        for file_info in downloaded_files_info:
                            if file_info["filename"].startswith(filename_pattern):
                                paper_dict = paper.to_dict()
                                paper_dict["paper_id"] = idx
                                paper_dict["downloaded_file"] = file_info["filename"]
                                paper_dict["download_source"] = file_info["source"]
                                papers_to_extract.append(paper_dict)
                                break

                # Start extraction process in background
                import threading

                extraction_thread = threading.Thread(
                    target=self._extract_texts_background, args=(papers_to_extract,)
                )
                extraction_thread.daemon = True
                extraction_thread.start()

                flash("Text extraction started successfully!", "success")
                return jsonify({"status": "started"})

            except Exception as e:
                print(f"Error starting text extraction: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route("/extract_single_paper", methods=["POST"])
        def extract_single_paper() -> Union[FlaskResponse, Tuple[FlaskResponse, int]]:
            """Extract text from a single paper."""
            try:
                paper_id = request.args.get("paper_id")
                if not paper_id:
                    return (
                        jsonify({"status": "error", "message": "Paper ID required"}),
                        400,
                    )

                # Get paper data
                consolidated_path = (
                    self.project_path / "pdfs" / "consolidated_papers.csv"
                )
                papers_df = pd.read_csv(consolidated_path)

                paper_idx = int(paper_id)
                if paper_idx >= len(papers_df):
                    return (
                        jsonify({"status": "error", "message": "Paper not found"}),
                        404,
                    )

                paper = papers_df.iloc[paper_idx]

                # Find downloaded file info
                downloaded_files_info = self._get_downloaded_files_with_source()
                filename_pattern = f"{paper_id}_"

                paper_dict = paper.to_dict()
                paper_dict["paper_id"] = paper_idx

                for file_info in downloaded_files_info:
                    if file_info["filename"].startswith(filename_pattern):
                        paper_dict["downloaded_file"] = file_info["filename"]
                        paper_dict["download_source"] = file_info["source"]
                        break

                # Extract text for this paper
                result = self._extract_text_from_paper(paper_dict)

                return jsonify({"status": "success", "result": result})

            except Exception as e:
                print(f"Error extracting single paper: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route("/retry_all_text_extraction", methods=["POST"])
        def retry_all_text_extraction() -> (
            Union[FlaskResponse, Tuple[FlaskResponse, int]]
        ):
            """Retry text extraction for all downloaded papers, including
            previously processed ones."""
            try:
                # Get papers data
                consolidated_path = (
                    self.project_path / "pdfs" / "consolidated_papers.csv"
                )
                papers_df = pd.read_csv(consolidated_path)

                # Filter out duplicates and get downloaded papers
                if "is_duplicate" in papers_df.columns:
                    non_duplicate_papers = papers_df[
                        ~papers_df["is_duplicate"].fillna(False)
                    ].copy()
                else:
                    non_duplicate_papers = papers_df.copy()

                downloaded_files_info = self._get_downloaded_files_with_source()
                downloaded_files = [info["filename"] for info in downloaded_files_info]

                papers_to_extract = []
                for idx, paper in non_duplicate_papers.iterrows():
                    paper_id = str(idx)
                    filename_pattern = f"{paper_id}_"
                    is_downloaded = any(
                        f.startswith(filename_pattern) for f in downloaded_files
                    )

                    if is_downloaded:
                        # Find the downloaded file and its source
                        for file_info in downloaded_files_info:
                            if file_info["filename"].startswith(filename_pattern):
                                paper_dict = paper.to_dict()
                                paper_dict["paper_id"] = idx
                                paper_dict["downloaded_file"] = file_info["filename"]
                                paper_dict["download_source"] = file_info["source"]
                                papers_to_extract.append(paper_dict)
                                break

                # Clear previous extraction status for all papers to force re-processing
                self._clear_extraction_status()

                # Start extraction process in background
                import threading

                extraction_thread = threading.Thread(
                    target=self._extract_texts_background, args=(papers_to_extract,)
                )
                extraction_thread.daemon = True
                extraction_thread.start()

                flash(
                    "Text extraction retry started successfully! All papers will "
                    "be re-processed.",
                    "success",
                )
                return jsonify({"status": "started"})

            except Exception as e:
                print(f"Error starting retry text extraction: {e}")
                return jsonify({"status": "error", "message": str(e)}), 500

        @self.app.route("/extracted_texts/<filename>")
        def serve_extracted_text(
            filename: str,
        ) -> Union[WerkzeugResponse, Tuple[str, int]]:
            """Serve extracted text JSON files."""
            try:
                extracted_dir = self.project_path / "pdfs" / "extracted_texts"
                if not extracted_dir.exists():
                    return "Extracted texts directory not found", 404

                json_file = extracted_dir / filename
                if not json_file.exists():
                    return f"File not found: {filename}", 404

                return send_from_directory(str(extracted_dir.absolute()), filename)

            except Exception as e:
                print(f"Error serving extracted text: {e}")
                return f"Error serving file: {str(e)}", 500

        @self.app.route("/save_screening_actions", methods=["POST"])
        def save_screening_actions() -> WerkzeugResponse:
            """Save screening action decisions for papers."""
            try:
                screening_actions = {}

                # Process form data to extract screening decisions
                for key, value in request.form.items():
                    if key.startswith("screening_action_"):
                        paper_id = key.replace("screening_action_", "")
                        screening_actions[paper_id] = value

                if screening_actions:
                    # Load the extraction status
                    status = self._load_extraction_status()

                    # Update each paper's screening status
                    for paper_id, action in screening_actions.items():
                        if paper_id in status:
                            status[paper_id]["screening_action"] = action
                            status[paper_id][
                                "screening_updated"
                            ] = pd.Timestamp.now().isoformat()

                    # Save the updated status
                    self._save_extraction_status(status)

                    flash(
                        f"Saved screening actions for {len(screening_actions)} papers.",
                        "success",
                    )
                else:
                    flash("No screening actions to save.", "info")

                return redirect(url_for("text_extraction"))

            except Exception as e:
                flash(f"Error saving screening actions: {str(e)}", "error")
                return redirect(url_for("text_extraction"))

    def _get_downloaded_files(self) -> List[str]:
        """Get list of downloaded PDF files from both automatic and manual
        directories."""
        downloaded_files = []

        # Check automatic directory
        auto_dir = self.project_path / "pdfs" / "automatic"
        if auto_dir.exists():
            downloaded_files.extend([f.name for f in auto_dir.glob("*.pdf")])

        # Check manual directory
        manual_dir = self.project_path / "pdfs" / "manual"
        if manual_dir.exists():
            downloaded_files.extend([f.name for f in manual_dir.glob("*.pdf")])

        return downloaded_files

    def _get_downloaded_files_with_source(self) -> List[Dict[str, str]]:
        """Get list of downloaded PDF files with their source directory."""
        files_info = []

        # Check automatic directory
        auto_dir = self.project_path / "pdfs" / "automatic"
        if auto_dir.exists():
            for f in auto_dir.glob("*.pdf"):
                files_info.append(
                    {"filename": f.name, "source": "automatic", "path": str(f)}
                )

        # Check manual directory
        manual_dir = self.project_path / "pdfs" / "manual"
        if manual_dir.exists():
            for f in manual_dir.glob("*.pdf"):
                files_info.append(
                    {"filename": f.name, "source": "manual", "path": str(f)}
                )

        return files_info

    def _get_paper_urls(self, paper: pd.Series) -> Dict[str, str]:
        """Extract available URLs from paper data."""
        urls = {}

        # Helper function to safely get string values
        def safe_get_string(value: Any) -> str:
            if pd.isna(value):
                return ""
            return str(value).strip()

        doi = safe_get_string(paper.get("DOI", ""))
        if doi and doi.lower() != "nan":
            urls["DOI"] = f"https://doi.org/{doi}"

        article_url = safe_get_string(
            paper.get("ArticleURL", "") or paper.get("article_url", "")
        )
        if article_url and article_url.lower() != "nan":
            urls["Article Page"] = article_url

        fulltext_url = safe_get_string(paper.get("FullTextURL", ""))
        if fulltext_url and fulltext_url.lower() != "nan":
            urls["Full Text PDF"] = fulltext_url

        original_url = safe_get_string(paper.get("URL", ""))
        if original_url and original_url.lower() != "nan":
            urls["Original URL"] = original_url

        return urls

    def _download_from_url(
        self, paper: pd.Series, url: str, paper_id: str
    ) -> PaperDownloadResult:
        """Download a paper from a specific URL to the manual folder."""
        try:
            downloader = PDFDownloader(self.project_path)

            # Create a modified paper series with the submitted URL as FullTextURL
            modified_paper = paper.copy()
            modified_paper["FullTextURL"] = url

            # Use the manual directory for web-submitted downloads
            output_dir = self.project_path / "pdfs" / "manual"
            output_dir.mkdir(
                parents=True, exist_ok=True
            )  # Ensure manual directory exists
            result = downloader._download_paper_pdf(
                modified_paper, output_dir, "web_submitted"
            )

            return result

        except Exception as e:
            return PaperDownloadResult(
                paper_id=paper_id,
                title=paper.get("title", paper.get("Title", "Unknown")),
                status=DownloadStatus.FAILED,
                error_message=f"Error downloading from submitted URL: {str(e)}",
            )

    def _group_similar_papers(self, papers_data: List[Dict]) -> List[Dict]:
        """Group papers by similarity to help identify duplicates."""
        # Calculate similarity scores between all papers
        groups_list: List[Dict[str, Any]] = []
        processed_papers = set()

        for i, paper in enumerate(papers_data):
            if paper["paper_id"] in processed_papers:
                continue

            # Create a group starting with this paper
            current_group = [paper]
            processed_papers.add(paper["paper_id"])

            # Find similar papers
            for j, other_paper in enumerate(papers_data):
                if i != j and other_paper["paper_id"] not in processed_papers:
                    similarity = self._calculate_paper_similarity(paper, other_paper)

                    # If similarity is high enough, add to group
                    if similarity > 0.6:  # Threshold for potential duplicates
                        other_paper["similarity_score"] = similarity
                        other_paper["suggested_duplicate_of"] = paper["paper_id"]
                        current_group.append(other_paper)
                        processed_papers.add(other_paper["paper_id"])

            # Sort group by similarity score (highest first)
            current_group.sort(
                key=lambda x: x.get("similarity_score", 1.0), reverse=True
            )

            # Add group info
            group_info = {
                "group_id": f"group_{len(groups_list)}",
                "papers": current_group,
                "is_potential_duplicate_group": len(current_group) > 1,
                "group_size": len(current_group),
            }

            groups_list.append(group_info)

        return groups_list

    def _calculate_paper_similarity(self, paper1: Dict, paper2: Dict) -> float:
        """Calculate similarity score between two papers."""
        import difflib

        # Normalize text for comparison
        def normalize_text(text: Optional[str]) -> str:
            if not text:
                return ""
            return (
                text.lower().strip().replace(" ", "").replace("-", "").replace("_", "")
            )

        # Title similarity (most important)
        title1 = normalize_text(paper1.get("title", ""))
        title2 = normalize_text(paper2.get("title", ""))
        title_similarity = difflib.SequenceMatcher(None, title1, title2).ratio()

        # Author similarity
        authors1 = normalize_text(paper1.get("authors", ""))
        authors2 = normalize_text(paper2.get("authors", ""))
        author_similarity = difflib.SequenceMatcher(None, authors1, authors2).ratio()

        # Year similarity (exact match or close)
        year1 = str(paper1.get("year", ""))
        year2 = str(paper2.get("year", ""))
        try:
            year1_int = int(float(year1)) if year1 and year1 != "Unknown" else 0
            year2_int = int(float(year2)) if year2 and year2 != "Unknown" else 0
            year_similarity = (
                1.0
                if year1 == year2
                else (0.8 if abs(year1_int - year2_int) <= 2 else 0.0)
            )
        except (ValueError, TypeError):
            year_similarity = 1.0 if year1 == year2 else 0.0

        # DOI similarity (if available)
        doi1 = normalize_text(paper1.get("doi", ""))
        doi2 = normalize_text(paper2.get("doi", ""))
        doi_similarity = 1.0 if doi1 and doi2 and doi1 == doi2 else 0.0

        # Weighted average (title is most important)
        if doi_similarity == 1.0:
            return 1.0  # Same DOI = definitely same paper

        weights = {"title": 0.6, "authors": 0.3, "year": 0.1}

        final_similarity = (
            title_similarity * weights["title"]
            + author_similarity * weights["authors"]
            + year_similarity * weights["year"]
        )

        return final_similarity

    def _load_extraction_status(self) -> Dict[str, Any]:
        """Load text extraction status from JSON file."""
        status_file = self.project_path / "extraction_status.json"
        if status_file.exists():
            try:
                with open(status_file, "r") as f:
                    loaded_data: Dict[str, Any] = json.load(f)
                    return loaded_data
            except Exception as e:
                print(f"Error loading extraction status: {e}")
        return {}

    def _save_extraction_status(self, status: Dict[str, Any]) -> None:
        """Save text extraction status to JSON file."""
        status_file = self.project_path / "extraction_status.json"
        try:
            with open(status_file, "w") as f:
                json.dump(status, f, indent=2)
        except Exception as e:
            print(f"Error saving extraction status: {e}")

    def _clear_extraction_status(self) -> None:
        """Clear all extraction status to force re-processing."""
        status_file = self.project_path / "extraction_status.json"
        try:
            # Remove the status file to start fresh
            if status_file.exists():
                status_file.unlink()
                print("Cleared extraction status - all papers will be re-processed")
        except Exception as e:
            print(f"Error clearing extraction status: {e}")

    def _extract_texts_background(self, papers_list: List[Dict[str, Any]]) -> None:
        """Extract texts from all papers in background thread."""
        try:
            print(f"Starting text extraction for {len(papers_list)} papers")

            for paper in papers_list:
                try:
                    result = self._extract_text_from_paper(paper)
                    print(f"Processed paper {paper['paper_id']}: {result['status']}")
                except Exception as e:
                    print(f"Error processing paper {paper['paper_id']}: {e}")

        except Exception as e:
            print(f"Error in background text extraction: {e}")

    def _extract_text_from_paper(self, paper: Dict) -> Dict:
        """Extract text from a single paper's PDF."""
        try:
            paper_id = str(paper["paper_id"])

            # Update status to processing
            status = self._load_extraction_status()
            status[paper_id] = {"status": "processing", "sections": [], "json_file": ""}
            self._save_extraction_status(status)

            # Find the PDF file
            pdf_file = None
            download_source = paper.get("download_source", "automatic")
            downloaded_file = paper.get("downloaded_file", "")

            if downloaded_file:
                pdf_path = (
                    self.project_path / "pdfs" / download_source / downloaded_file
                )
                if pdf_path.exists():
                    pdf_file = pdf_path

            if not pdf_file:
                # Update status to failed
                status[paper_id] = {
                    "status": "failed",
                    "sections": [],
                    "json_file": "",
                    "error": "PDF file not found",
                }
                self._save_extraction_status(status)
                return {"status": "failed", "error": "PDF file not found"}

            # Extract text using a simple PDF text extraction
            extracted_data = self._extract_pdf_text(pdf_file, paper)

            # Create extracted_texts directory
            extracted_dir = self.project_path / "pdfs" / "extracted_texts"
            extracted_dir.mkdir(exist_ok=True)

            # Save extracted text as JSON
            json_filename = f"paper_{paper_id}_extracted.json"
            json_path = extracted_dir / json_filename

            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(extracted_data, f, indent=2, ensure_ascii=False)

            # Update status to success
            sections = list(extracted_data.get("additional_sections", {}).keys())
            main_sections = [
                s
                for s in [
                    "abstract",
                    "introduction",
                    "methods",
                    "results",
                    "discussion",
                    "conclusion",
                ]
                if extracted_data.get(s, "")
            ]
            all_sections = main_sections + sections

            # Calculate word count safely
            try:
                word_count = self._calculate_word_count(extracted_data)
            except Exception as e:
                print(f"Error calculating word count for paper {paper_id}: {e}")
                word_count = 0

            status[paper_id] = {
                "status": "success" if all_sections else "partial",
                "sections": all_sections,
                "json_file": json_filename,
                "extracted_at": pd.Timestamp.now().isoformat(),
                "main_sections_found": main_sections,
                "additional_sections_found": sections,
                "extraction_metadata": {
                    "text_length": extracted_data.get("extraction_metadata", {}).get(
                        "text_length", 0
                    ),
                    "total_pages": extracted_data.get("extraction_metadata", {}).get(
                        "total_pages", 0
                    ),
                    "word_count": word_count,
                },
            }
            self._save_extraction_status(status)

            return {
                "status": "success",
                "sections": all_sections,
                "json_file": json_filename,
            }

        except Exception as e:
            print(f"Error extracting text from paper {paper_id}: {e}")

            # Update status to failed
            status = self._load_extraction_status()
            status[paper_id] = {
                "status": "failed",
                "sections": [],
                "json_file": "",
                "error": str(e),
            }
            self._save_extraction_status(status)

            return {"status": "failed", "error": str(e)}

    def _extract_pdf_text(self, pdf_path: Path, paper: Dict) -> Dict:
        """Extract text from PDF and organize into academic paper sections."""
        try:
            import PyPDF2

            # Extract raw text
            text_content = ""
            total_pages = 0

            try:
                with open(pdf_path, "rb") as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    total_pages = len(pdf_reader.pages)
                    for page_num, page in enumerate(pdf_reader.pages):
                        try:
                            page_text = page.extract_text()
                            if page_text:
                                text_content += page_text + "\n"
                        except Exception as e:
                            print(
                                f"Error extracting text from page {page_num + 1} of "
                                f"{pdf_path}: {e}"
                            )
                            continue
            except Exception as e:
                print(f"Error opening PDF {pdf_path}: {e}")
                # Return minimal data structure for failed extraction
                return self._create_fallback_extraction_data(paper, pdf_path, str(e))

            if not text_content.strip():
                print(f"No text content extracted from {pdf_path}")
                return self._create_fallback_extraction_data(
                    paper, pdf_path, "No text content extracted"
                )

            # Clean and preprocess text
            cleaned_text = self._preprocess_text(text_content)

            # Extract metadata from paper info and text
            metadata = self._extract_paper_metadata(paper, cleaned_text)

            # Extract academic paper sections
            sections = self._extract_academic_sections(cleaned_text)

            # Create structured output following the requirements
            extracted_data = {
                # Top-level metadata
                "title": metadata.get("title", ""),
                "authors": metadata.get("authors", []),
                "year": metadata.get("year", None),
                "doi": metadata.get("doi", ""),
                "source": metadata.get("source", ""),
                "url": metadata.get("url", ""),
                # Document sections
                "abstract": sections.get("abstract", ""),
                "introduction": sections.get("introduction", ""),
                "methods": sections.get("methods", ""),
                "results": sections.get("results", ""),
                "discussion": sections.get("discussion", ""),
                "conclusion": sections.get("conclusion", ""),
                # Additional sections that might be present
                "additional_sections": {
                    k: v
                    for k, v in sections.items()
                    if k
                    not in [
                        "abstract",
                        "introduction",
                        "methods",
                        "results",
                        "discussion",
                        "conclusion",
                    ]
                },
                # Technical metadata
                "extraction_metadata": {
                    "paper_id": int(paper["paper_id"]),
                    "pdf_file": str(pdf_path.name),
                    "extraction_date": pd.Timestamp.now().isoformat(),
                    "total_pages": total_pages,
                    "text_length": len(cleaned_text),
                    "sections_found": list(sections.keys()),
                    "extraction_method": "PyPDF2_academic_parser",
                },
            }

            return extracted_data

        except ImportError:
            print("PyPDF2 not available, using fallback")
            return self._create_fallback_extraction_data(
                paper, pdf_path, "PyPDF2 not installed"
            )
        except Exception as e:
            print(f"Unexpected error in PDF extraction for {pdf_path}: {e}")
            return self._create_fallback_extraction_data(paper, pdf_path, str(e))

    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess extracted text."""
        import re

        # Remove excessive whitespace and normalize line breaks
        text = re.sub(r"\n\s*\n", "\n\n", text)
        text = re.sub(r"[ \t]+", " ", text)

        # Remove page numbers and headers/footers (common patterns)
        text = re.sub(r"\n\d+\s*\n", "\n", text)
        text = re.sub(r"\n[A-Z\s]+\n", "\n", text)  # All caps headers

        # Fix common PDF extraction issues
        text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)  # Missing spaces
        text = re.sub(
            r"(\w)-\s*\n\s*(\w)", r"\1\2", text
        )  # Hyphenated words across lines

        return text.strip()

    def _extract_paper_metadata(self, paper: Dict, text: str) -> Dict:
        """Extract and enhance paper metadata."""
        metadata = {}

        # Title - prefer from paper data, fallback to text extraction
        metadata["title"] = paper.get("title", "") or self._extract_title_from_text(
            text
        )

        # Authors - parse from string to list
        metadata["authors"] = self._parse_authors(paper.get("authors", ""))

        # Year - ensure integer
        metadata["year"] = self._parse_year(paper.get("year", ""))

        # DOI - clean format
        doi = paper.get("DOI", "") or self._extract_doi_from_text(text)
        metadata["doi"] = doi.strip() if doi and not pd.isna(doi) else ""

        # Source (journal/conference) - extract from text if not available
        metadata["source"] = self._extract_source_from_text(text)

        # URL - get from paper data
        urls = self._get_paper_urls(pd.Series(paper))
        metadata["url"] = (
            urls.get("DOI", "")
            or urls.get("Article Page", "")
            or urls.get("Full Text PDF", "")
        )

        return metadata

    def _parse_authors(self, authors_str: str) -> List[str]:
        """Parse authors string into a list of individual authors."""
        if not authors_str or pd.isna(authors_str):
            return []

        # Common author separators
        separators = [";", ",", " and ", " & ", "\n"]
        authors = [authors_str]

        for sep in separators:
            new_authors = []
            for author in authors:
                new_authors.extend([a.strip() for a in author.split(sep) if a.strip()])
            authors = new_authors

        # Clean up author names
        cleaned_authors = []
        for author in authors:
            # Remove affiliations in parentheses
            author = re.sub(r"\([^)]*\)", "", author).strip()
            # Remove extra whitespace
            author = re.sub(r"\s+", " ", author).strip()
            if author and len(author) > 1:  # Avoid single characters
                cleaned_authors.append(author)

        return cleaned_authors

    def _parse_year(self, year_value: Any) -> Optional[int]:
        """Parse year value to integer."""
        if not year_value or pd.isna(year_value):
            return None

        try:
            year_str = str(year_value).strip()
            # Extract 4-digit year
            year_match = re.search(r"\b(19|20)\d{2}\b", year_str)
            if year_match:
                return int(year_match.group())
            return int(float(year_str))
        except (ValueError, TypeError):
            return None

    def _extract_title_from_text(self, text: str) -> str:
        """Extract title from paper text (first meaningful line)."""
        lines = text.split("\n")
        for line in lines[:10]:  # Check first 10 lines
            line = line.strip()
            if len(line) > 10 and not line.isupper() and not line.isdigit():
                return line
        return ""

    def _extract_doi_from_text(self, text: str) -> str:
        """Extract DOI from paper text."""
        doi_pattern = r"(?:doi:?\s*)?10\.\d{4,}\/[^\s]+"
        match = re.search(doi_pattern, text, re.IGNORECASE)
        return match.group().replace("doi:", "").strip() if match else ""

    def _extract_source_from_text(self, text: str) -> str:
        """Extract journal or conference name from text."""
        # Look for common patterns
        patterns = [
            r"(?:Published in|Proceedings of|Journal of|Conference on)\s+([^\n]+)",
            r"([A-Z][a-z]+ (?:Journal|Conference|Proceedings|Review))[^\n]*",
            r"(IEEE [^,\n]+)",
            r"(ACM [^,\n]+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return ""

    def _extract_academic_sections(self, text: str) -> Dict[str, str]:
        """Extract academic paper sections with improved detection."""
        import re

        sections = {}

        # Enhanced section patterns for academic papers
        section_patterns = {
            "abstract": [
                r"\babstract\b",
                r"\bsummary\b",
                r"\bexecutive summary\b",
                r"\b(?:paper\s+)?abstract\b",
            ],
            "introduction": [
                r"\b(?:1\.?\s*)?introduction\b",
                r"\b(?:1\.?\s*)?background\b",
                r"\b(?:1\.?\s*)?motivation\b",
                r"\b(?:I\.?\s*)?introduction\b",
            ],
            "methods": [
                r"\b(?:\d+\.?\s*)?(?:methods?|methodology)\b",
                r"\b(?:\d+\.?\s*)?(?:approach|framework)\b",
                r"\b(?:\d+\.?\s*)?(?:materials? and methods?)\b",
                r"\b(?:\d+\.?\s*)?(?:experimental (?:setup|design))\b",
                r"\b(?:\d+\.?\s*)?(?:problem statement)\b",
                r"\b(?:\d+\.?\s*)?(?:mathematical (?:model|formulation))\b",
                r"\b(?:\d+\.?\s*)?(?:solution approaches?)\b",
                r"\b(?:\d+\.?\s*)?(?:formulation)\b",
            ],
            "results": [
                r"\b(?:\d+\.?\s*)?results?\b",
                r"\b(?:\d+\.?\s*)?findings?\b",
                r"\b(?:\d+\.?\s*)?(?:experimental results?)\b",
                r"\b(?:\d+\.?\s*)?evaluation\b",
                r"\b(?:\d+\.?\s*)?(?:results and discussion)\b",
            ],
            "discussion": [
                r"\b(?:\d+\.?\s*)?discussion\b",
                r"\b(?:\d+\.?\s*)?analysis\b",
                r"\b(?:\d+\.?\s*)?(?:comparison|comparative analysis)\b",
            ],
            "conclusion": [
                r"\b(?:\d+\.?\s*)?conclusions?\b",
                r"\b(?:\d+\.?\s*)?(?:concluding remarks?)\b",
                r"\b(?:\d+\.?\s*)?(?:summary and conclusions?)\b",
                r"\b(?:\d+\.?\s*)?(?:final remarks?)\b",
                r"\b(?:\d+\.?\s*)?(?:future (?:work|directions))\b",
            ],
            "literature_review": [
                r"\b(?:\d+\.?\s*)?(?:literature review|related work)\b",
                r"\b(?:\d+\.?\s*)?(?:state of the art|prior work)\b",
                r"\b(?:\d+\.?\s*)?(?:previous work|background)\b",
            ],
            "acknowledgments": [r"\b(?:acknowledgments?|acknowledgements?)\b"],
            "references": [r"\b(?:references?|bibliography)\b"],
        }

        # Additional patterns to catch more general numbered sections with
        # descriptive titles
        general_section_patterns = {
            "forecasting": [r"\b(?:\d+\.?\s*)?forecasting\b"],
            "scheduling": [r"\b(?:\d+\.?\s*)?scheduling\b"],
            "optimization": [r"\b(?:\d+\.?\s*)?optimization\b"],
            "modeling": [r"\b(?:\d+\.?\s*)?(?:modeling|modelling)\b"],
            "simulation": [r"\b(?:\d+\.?\s*)?simulation\b"],
            "case_study": [r"\b(?:\d+\.?\s*)?(?:case study|case studies)\b"],
            "implementation": [r"\b(?:\d+\.?\s*)?implementation\b"],
            "experiments": [r"\b(?:\d+\.?\s*)?experiments?\b"],
            "validation": [r"\b(?:\d+\.?\s*)?validation\b"],
            "limitations": [r"\b(?:\d+\.?\s*)?limitations?\b"],
            "future_work": [
                r"\b(?:\d+\.?\s*)?(?:future work|future research|future directions)\b"
            ],
            "problem_definition": [
                r"\b(?:\d+\.?\s*)?(?:problem (?:definition|statement))\b"
            ],
            "data_analysis": [r"\b(?:\d+\.?\s*)?(?:data analysis|data processing)\b"],
        }

        # Split text into chunks - look at both lines and paragraphs
        lines = text.split("\n")
        paragraphs = text.split("\n\n")

        # Combine both pattern sets for comprehensive detection
        all_patterns = {**section_patterns, **general_section_patterns}

        # Find section boundaries using a more flexible approach
        section_starts = {}

        # First pass: Look for obvious section headers in lines
        for i, line in enumerate(lines):
            line_clean = line.strip().lower()
            if len(line_clean) < 3 or len(line_clean) > 150:
                continue

            for section_name, patterns in all_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, line_clean, re.IGNORECASE):
                        # Verify this looks like a section header
                        if self._is_section_header(
                            line.strip()
                        ) or self._is_likely_header(line.strip()):
                            if (
                                section_name not in section_starts
                            ):  # Take first occurrence
                                section_starts[section_name] = i
                                break
                if section_name in section_starts:
                    break

        # Second pass: Enhanced numbered section detection
        # Look for patterns like "2 Forecasting", "3. Methods", etc.
        numbered_section_pattern = r"^(\d+)\.?\s+([A-Z][a-zA-Z\s]+)$"
        for i, line in enumerate(lines):
            line_clean = line.strip()
            if len(line_clean) < 5 or len(line_clean) > 100:
                continue

            match = re.match(numbered_section_pattern, line_clean)
            if match:
                section_title = match.group(2).strip().lower()

                # Map common section titles to our standardized names
                title_mappings = {
                    "forecasting": "forecasting",
                    "introduction": "introduction",
                    "background": "introduction",
                    "methods": "methods",
                    "methodology": "methods",
                    "approach": "methods",
                    "results": "results",
                    "findings": "results",
                    "discussion": "discussion",
                    "analysis": "discussion",
                    "conclusion": "conclusion",
                    "conclusions": "conclusion",
                    "literature review": "literature_review",
                    "related work": "literature_review",
                    "problem statement": "methods",
                    "problem definition": "methods",
                    "solution approaches": "methods",
                    "case study": "case_study",
                    "experiments": "experiments",
                    "evaluation": "results",
                    "implementation": "implementation",
                    "simulation": "simulation",
                    "modeling": "modeling",
                    "modelling": "modeling",
                    "optimization": "optimization",
                    "validation": "validation",
                    "limitations": "limitations",
                    "future work": "future_work",
                    "future research": "future_work",
                    "future directions": "future_work",
                }

                # Find the best match for this section title
                matched_section = None
                for key, value in title_mappings.items():
                    if key in section_title:
                        matched_section = value
                        break

                # If we found a match and haven't recorded this section yet
                if matched_section and matched_section not in section_starts:
                    # Verify this looks like a section header
                    if (
                        self._is_section_header(line_clean)
                        or len(line_clean.split()) <= 5
                    ):
                        section_starts[matched_section] = i

        # Third pass: Look for sections within paragraph boundaries for cases
        # where headers aren't clearly separated
        if (
            len(section_starts) < 3
        ):  # If we found few sections, try paragraph-based search
            for section_name, patterns in all_patterns.items():
                if section_name in section_starts:
                    continue

                for pattern in patterns:
                    for para in paragraphs:
                        para_lines = para.split("\n")
                        if len(para_lines) > 0:
                            first_line = para_lines[0].strip().lower()
                            if re.search(pattern, first_line, re.IGNORECASE):
                                # Find line number in original text
                                para_start = text.find(para)
                                if para_start != -1:
                                    line_num = text[:para_start].count("\n")
                                    section_starts[section_name] = line_num
                                    break

        # Extract content for each section
        sorted_sections = sorted(section_starts.items(), key=lambda x: x[1])

        for i, (section_name, start_line) in enumerate(sorted_sections):
            # Determine end line
            if i + 1 < len(sorted_sections):
                end_line = sorted_sections[i + 1][1]
            else:
                # For the last section, use text length but limit to reasonable size
                end_line = min(len(lines), start_line + 200)  # Limit to ~200 lines

            # Extract section content
            section_lines = lines[start_line + 1 : end_line]
            content = "\n".join(section_lines).strip()

            # Clean up content
            content = self._clean_section_content(content)

            # More lenient content filtering - include sections with at least 20 words
            if content and len(content.split()) >= 20:  # At least 20 words
                sections[section_name] = content

        # Special handling for abstract - often appears early without clear header
        if "abstract" not in sections:
            abstract_content = self._extract_abstract_fallback(text)
            if abstract_content:
                sections["abstract"] = abstract_content

        return sections

    def _is_section_header(self, line: str) -> bool:
        """Determine if a line is likely a section header."""
        line = line.strip()

        # Headers are typically short to medium length
        if len(line) > 150 or len(line) < 3:
            return False

        # Check for common header patterns
        header_patterns = [
            r"^\d+\.?\s+\w+",  # Numbered sections (1. Introduction, 2 Methods,
            # 2 Forecasting)
            r"^\d+\.?\d*\.?\s+\w+",  # Sub-numbered sections (2.1 Methods,
            # 3.2.1 Analysis)
            r"^[IVX]+\.?\s+\w+",  # Roman numeral sections
            r"^[A-Z][A-Z\s]+$",  # All caps headers
            r"^\w+$",  # Single word headers
            r"^\w+\s+\w+$",  # Two word headers
            r"^\w+\s+\w+\s+\w+$",  # Three word headers
            r"^[A-Z][a-z]+(?:\s+[A-Z][a-z]*)*$",  # Title case headers
            r"^\d+\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]*)*$",  # Numbered title case
            # (e.g., "2 Forecasting")
        ]

        # Additional criteria for headers
        word_count = len(line.split())

        # Headers usually have 1-8 words
        if not (1 <= word_count <= 8):
            return False

        # Check if it matches header patterns
        pattern_match = any(re.match(pattern, line) for pattern in header_patterns)

        # Headers often don't end with punctuation (except periods after numbers)
        ends_properly = not line.endswith((",", ";", "!", "?")) or bool(
            re.match(r".*\d+\.$", line)
        )

        return pattern_match and ends_properly

    def _is_likely_header(self, line: str) -> bool:
        """Additional checks for section headers with more lenient criteria."""
        line = line.strip()

        # Check for common header characteristics
        if len(line) > 150:
            return False

        # Headers often end with specific patterns
        header_end_patterns = [
            r"\d+$",  # Ends with number (like "3. Methods 3")
            r"[A-Z\s]+$",  # All caps words
            r"\w+\s*$",  # Single word or short phrase
        ]

        # Headers often start with numbers or letters
        header_start_patterns = [
            r"^\d+\.?\s*",  # Starts with number
            r"^[IVX]+\.?\s*",  # Roman numerals
            r"^[A-Z][a-z]*\s*",  # Capitalized word
        ]

        return any(
            re.search(pattern, line) for pattern in header_start_patterns
        ) or any(re.search(pattern, line) for pattern in header_end_patterns)

    def _extract_abstract_fallback(self, text: str) -> str:
        """Fallback method to extract abstract when no clear header is found."""
        lines = text.split("\n")

        # Look for abstract-like content in the first few pages
        for i, line in enumerate(lines[:200]):  # First 200 lines
            line_clean = line.strip()

            # Skip very short lines, headers, and metadata
            if (
                len(line_clean) < 30
                or line_clean.lower().startswith(
                    (
                        "keywords",
                        "doi:",
                        "published",
                        "copyright",
                        "author",
                        "correspondence",
                    )
                )
                or re.match(r"^\d+\s*$", line_clean)
            ):
                continue

            # Look for paragraph that looks like an abstract
            if (
                len(line_clean) > 100
                and not line_clean.lower().startswith(
                    ("figure", "table", "section", "chapter")
                )
                and len(line_clean.split()) > 15
            ):
                # Try to get the full paragraph
                abstract_lines = [line_clean]
                j = i + 1
                while j < len(lines) and j < i + 20:  # Look ahead max 20 lines
                    next_line = lines[j].strip()
                    if (
                        len(next_line) < 10
                    ):  # Empty or very short line - end of paragraph
                        break
                    if next_line.lower().startswith(
                        ("keywords", "introduction", "1.", "doi:")
                    ):
                        break
                    abstract_lines.append(next_line)
                    j += 1

                abstract_text = " ".join(abstract_lines).strip()

                # Validate it looks like an abstract (50-500 words)
                word_count = len(abstract_text.split())
                if 50 <= word_count <= 500:
                    return abstract_text

        return ""

    def _clean_section_content(self, content: str) -> str:
        """Clean extracted section content."""
        # Remove excessive whitespace
        content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)
        content = re.sub(r"[ \t]+", " ", content)

        # Remove page numbers and artifacts
        content = re.sub(r"\n\d+\s*\n", "\n", content)
        content = re.sub(r"\n[A-Z\s]{20,}\n", "\n", content)  # Long all-caps lines

        return content.strip()

    def _detect_sections(self, text: str) -> Dict[str, str]:
        """Legacy method maintained for compatibility."""
        return self._extract_academic_sections(text)

    def _calculate_word_count(self, extracted_data: Dict[str, Any]) -> int:
        """Calculate word count from extracted text data.

        Args:
            extracted_data: Dictionary containing extracted text sections

        Returns:
            Total word count across all sections
        """
        total_words = 0
        for section_key, section_text in extracted_data.items():
            if isinstance(section_text, str) and section_text.strip():
                total_words += len(section_text.split())
        return total_words

    def _create_fallback_extraction_data(
        self, paper: Dict[str, Any], pdf_path: Path, error_msg: str
    ) -> Dict[str, Any]:
        """Create fallback extraction data when PDF processing fails.

        Args:
            paper: Paper information dictionary
            pdf_path: Path to the PDF file
            error_msg: Error message from failed extraction

        Returns:
            Fallback extraction data dictionary
        """
        return {
            "title": paper.get("title", "Unknown Title"),
            "authors": paper.get("authors", "Unknown Authors"),
            "year": paper.get("year", "Unknown"),
            "doi": paper.get("doi", ""),
            "abstract": paper.get("abstract", ""),
            "source": paper.get("source_queries", ""),
            "pdf_path": str(pdf_path),
            "extraction_status": "failed",
            "error": error_msg,
            "extracted_at": pd.Timestamp.now().isoformat(),
            "word_count": 0,
        }

    def run(
        self, host: str = "127.0.0.1", port: int = 5000, debug: bool = False
    ) -> None:
        """Run the Flask development server."""
        print(f"Starting Papervisor Web Server for project '{self.project_id}'")
        print(f"Access the dashboard at: http://{host}:{port}")
        self.app.run(host=host, port=port, debug=debug)


def create_app(project_id: str, data_dir: str = "data") -> Flask:
    """Create and configure the Flask app.

    Args:
        project_id: Literature review project ID
        data_dir: Data directory path

    Returns:
        Configured Flask app
    """
    server = PapervisorWebServer(project_id, data_dir)
    return server.app


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m papervisor.web_server <project_id> [data_dir]")
        sys.exit(1)

    project_id = sys.argv[1]
    data_dir = sys.argv[2] if len(sys.argv) > 2 else "data"

    server = PapervisorWebServer(project_id, data_dir)
    server.run()
