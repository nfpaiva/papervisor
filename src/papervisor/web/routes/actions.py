"""
Action (POST) endpoints for Papervisor web app (modularized).
"""

from flask import request, jsonify, flash, redirect, url_for, current_app, Flask
from typing import Any, Optional

from papervisor.web.services.url_submission_service import URLSubmissionService
from papervisor.web.services.download_missing_service import DownloadMissingService
from papervisor.web.services.text_extraction_service import TextExtractionService
from papervisor.web.services.single_paper_extraction_service import (
    SinglePaperExtractionService,
)
from papervisor.web.services.retry_text_extraction_service import (
    RetryTextExtractionService,
)
from papervisor.web.services.screening_action_service import ScreeningActionService
from papervisor.web.services.retry_failed_downloads_service import (
    RetryFailedDownloadsService,
)
from papervisor.web.services.cancel_download_service import CancelDownloadService
from papervisor.web.services.pdf_upload_service import PDFUploadService


def register_action_routes(app: Flask, papervisor: Any) -> None:
    """Register all action (POST) routes for the Flask application."""

    @app.route("/submit_url", methods=["POST"])
    @app.route("/project/<project_id>/submit_url", methods=["POST"])
    def submit_url(project_id: Optional[str] = None) -> Any:
        """Submit a URL for PDF processing in a project."""
        if not project_id:
            project_id = request.args.get("project_id")
        if not project_id:
            return jsonify({"error": "Project ID is required"}), 400
        url = request.form.get("url")
        if not url:
            return jsonify({"error": "URL is required"}), 400
        url_service = URLSubmissionService(
            papervisor, current_app.config.get("DATA_DIR", "data")
        )
        result = url_service.submit_url(str(project_id), str(url))
        if "error" in result:
            flash(result["error"], "error")
        else:
            flash("URL submitted successfully!", "success")
        return redirect(url_for("download_management", project_id=str(project_id)))

    @app.route("/download_all_missing", methods=["POST"])
    @app.route("/project/<project_id>/download_all_missing", methods=["POST"])
    def download_all_missing(project_id: Optional[str] = None) -> Any:
        """Start background download of all missing papers in a project."""
        if not project_id:
            project_id = request.args.get("project_id")
        if not project_id:
            flash("Project ID is required", "error")
            return redirect(url_for("landing_page"))
        download_service = DownloadMissingService(
            papervisor, current_app.config.get("DATA_DIR", "data")
        )
        result = download_service.download_all_missing(str(project_id))
        if "error" in result:
            flash(result["error"], "error")
        else:
            flash("Download of all missing papers started!", "success")
        return redirect(url_for("download_management", project_id=str(project_id)))

    @app.route("/start_text_extraction", methods=["POST"])
    def start_text_extraction() -> Any:
        """Start text extraction process for project PDFs."""
        project_id = request.args.get("project_id")
        if not project_id:
            return (
                jsonify({"status": "error", "message": "Project ID is required"}),
                400,
            )
        extraction_service = TextExtractionService(
            papervisor, current_app.config.get("DATA_DIR", "data")
        )
        result = extraction_service.start_text_extraction(str(project_id))
        if "error" in result:
            flash(result["error"], "error")
            return jsonify({"status": "error", "message": result["error"]}), 400
        flash("Text extraction started successfully!", "success")
        return jsonify({"status": "started"})

    @app.route("/extract_single_paper", methods=["POST"])
    def extract_single_paper() -> Any:
        paper_id = request.args.get("paper_id")
        project_id = request.args.get("project_id")
        if not paper_id or not project_id:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "paper_id and project_id are required",
                    }
                ),
                400,
            )
        extraction_service = SinglePaperExtractionService(
            papervisor, current_app.config.get("DATA_DIR", "data")
        )
        result = extraction_service.extract_single_paper(str(project_id), str(paper_id))
        if "error" in result:
            return jsonify({"status": "error", "message": result["error"]}), 400
        return jsonify({"status": "success", "result": result})

    @app.route("/retry_all_text_extraction", methods=["POST"])
    def retry_all_text_extraction() -> Any:
        project_id = request.args.get("project_id")
        if not project_id:
            return (
                jsonify({"status": "error", "message": "project_id is required"}),
                400,
            )
        retry_service = RetryTextExtractionService(
            papervisor, current_app.config.get("DATA_DIR", "data")
        )
        result = retry_service.retry_all_text_extraction(str(project_id))
        if "error" in result:
            flash(result["error"], "error")
            return jsonify({"status": "error", "message": result["error"]}), 400
        flash(
            "Retry text extraction started! All papers will be re-processed.", "success"
        )
        return jsonify({"status": "started"})

    @app.route("/save_screening_actions", methods=["POST"])
    def save_screening_actions() -> Any:
        project_id = request.args.get("project_id")
        if not project_id:
            return (
                jsonify({"status": "error", "message": "project_id is required"}),
                400,
            )
        screening_actions = {}
        for key, value in request.form.items():
            if key.startswith("screening_action_"):
                paper_id = key.replace("screening_action_", "")
                screening_actions[paper_id] = value
        screening_service = ScreeningActionService(
            papervisor, current_app.config.get("DATA_DIR", "data")
        )
        result = screening_service.save_screening_actions(
            str(project_id), screening_actions
        )
        if "error" in result:
            flash(result["error"], "error")
        else:
            flash(
                f"Saved screening actions for {result.get('count', 0)} papers.",
                "success",
            )
        return redirect(url_for("text_extraction", project_id=project_id))

    @app.route("/retry_failed_downloads", methods=["POST"])
    @app.route("/project/<project_id>/retry_failed_downloads", methods=["POST"])
    def retry_failed_downloads(project_id: Optional[str] = None) -> Any:
        if not project_id:
            project_id = request.args.get("project_id")
        if not project_id:
            flash("Project ID is required", "error")
            return redirect(url_for("landing_page"))
        retry_service = RetryFailedDownloadsService(
            papervisor, current_app.config.get("DATA_DIR", "data")
        )
        result = retry_service.retry_failed_downloads(str(project_id))
        if "error" in result:
            flash(result["error"], "error")
        else:
            flash("Retry download process started. Check progress below.", "info")
        return redirect(url_for("download_management", project_id=project_id))

    @app.route("/cancel_download", methods=["POST"])
    @app.route("/project/<project_id>/cancel_download", methods=["POST"])
    def cancel_download(project_id: Optional[str] = None) -> Any:
        if not project_id:
            project_id = request.args.get("project_id")
        if not project_id:
            flash("Project ID is required", "error")
            return redirect(url_for("landing_page"))
        cancel_service = CancelDownloadService(papervisor)
        result = cancel_service.cancel_download(str(project_id))
        if "error" in result:
            flash(result["error"], "error")
        else:
            flash(f"Download cancelled for project '{project_id}'", "warning")
        return redirect(url_for("download_management", project_id=project_id))

    @app.route("/upload_pdf", methods=["POST"])
    def upload_pdf_legacy() -> Any:
        project_id = request.args.get("project_id")
        if not project_id:
            flash("No project specified", "error")
            return redirect(url_for("landing_page"))
        return redirect(url_for("project_upload_pdf", project_id=project_id))

    @app.route("/project/<project_id>/upload_pdf", methods=["POST"])
    def project_upload_pdf(project_id: str) -> Any:
        paper_id = request.form.get("paper_id")
        uploaded_file = request.files.get("pdf_file")
        if not paper_id:
            flash("Paper ID is required", "error")
            return redirect(url_for("download_management", project_id=project_id))
        upload_service = PDFUploadService(
            papervisor, current_app.config.get("DATA_DIR", "data")
        )
        result = upload_service.upload_pdf(project_id, str(paper_id), uploaded_file)
        if "error" in result:
            flash(result["error"], "error")
        else:
            flash(
                f"Successfully uploaded PDF for paper {paper_id}: {result['filename']}",
                "success",
            )
        return redirect(url_for("download_management", project_id=project_id))
