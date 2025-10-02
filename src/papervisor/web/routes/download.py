"""
Download management routes for Papervisor web app (refactored).
"""

from flask import (
    render_template,
    current_app,
    request,
    redirect,
    url_for,
    flash,
)
from papervisor.web.services.download_service import DownloadService
from typing import Any
from flask import Flask
import threading


def register_download_routes(app: Flask, papervisor: Any) -> None:
    @app.route("/project/<project_id>/downloads")
    def download_management(project_id: str) -> Any:
        try:
            download_service = DownloadService(
                papervisor, current_app.config.get("DATA_DIR", "data")
            )
            data = download_service.get_download_data(project_id)
            return render_template(
                "download_management.html",
                project_id=project_id,
                papers=data["papers"],
                download_stats=data["download_stats"],
                total_papers=data["total_papers"],
                downloaded_count=data["downloaded_count"],
                manual_count=data["manual_count"],
                total_papers_in_file=data["total_papers_in_file"],
                total_after_duplicate_filter=data["total_after_duplicate_filter"],
                success_rate=int(
                    (data["downloaded_count"] / data["total_papers"] * 100)
                    if data["total_papers"] > 0
                    else 0
                ),
            )
        except Exception as e:
            return render_template("error.html", error=str(e))

    @app.route("/project/<project_id>/download_all_pdfs", methods=["POST"])
    def download_all_pdfs(project_id: str) -> Any:
        """Endpoint to trigger download of all PDFs for a project (background)."""
        try:
            download_service = DownloadService(
                papervisor, current_app.config.get("DATA_DIR", "data")
            )
            current_project = papervisor.get_project(project_id)
            if not current_project:
                flash(f"Project '{project_id}' not found.", "error")
                return redirect(url_for("download_management", project_id=project_id))
            project_path = download_service.data_dir / current_project.project_path
            consolidated_path = project_path / "pdfs" / "consolidated_papers.csv"
            if not consolidated_path.exists():
                flash(
                    "No consolidated papers file found. Please run the download process first.",
                    "error",
                )
                return redirect(url_for("download_management", project_id=project_id))
            import pandas as pd

            consolidated_df = pd.read_csv(consolidated_path)
            # Reset all download statuses and sources to 'Pending' before starting
            consolidated_df["auto_download_status"] = "Pending"
            consolidated_df["auto_download_message"] = ""
            consolidated_df["available_url"] = ""
            consolidated_df["download_source"] = ""
            consolidated_df["manual_dw_file_url"] = ""
            consolidated_df.to_csv(consolidated_path, index=False)

            # Run download in background thread
            def run_download() -> None:
                download_service.download_consolidated_pdfs(
                    project_path, project_id, consolidated_df
                )

            threading.Thread(target=run_download, daemon=True).start()
            flash("Download of all PDFs started in background.", "success")
        except Exception as e:
            flash(f"Error downloading PDFs: {str(e)}", "error")
        return redirect(url_for("download_management", project_id=project_id))

    @app.route("/project/<project_id>/download_failed_pdfs", methods=["POST"])
    def download_failed_pdfs(project_id: str) -> Any:
        """Endpoint to retry download of only failed PDFs for a project (background)."""
        try:
            download_service = DownloadService(
                papervisor, current_app.config.get("DATA_DIR", "data")
            )
            current_project = papervisor.get_project(project_id)
            if not current_project:
                flash(f"Project '{project_id}' not found.", "error")
                return redirect(url_for("download_management", project_id=project_id))
            project_path = download_service.data_dir / current_project.project_path
            consolidated_path = project_path / "pdfs" / "consolidated_papers.csv"
            if not consolidated_path.exists():
                flash(
                    "No consolidated papers file found. Please run the download process first.",
                    "error",
                )
                return redirect(url_for("download_management", project_id=project_id))
            import pandas as pd

            consolidated_df = pd.read_csv(consolidated_path)
            # Filter only failed or not-yet-tried
            status_column = consolidated_df.get(
                "auto_download_status", pd.Series(dtype=str)
            )
            if isinstance(status_column, pd.Series):
                failed_mask = status_column.astype(str).str.lower() != "success"
            else:
                # Fallback if get returns a scalar
                failed_mask = pd.Series([True] * len(consolidated_df))
            failed_df = consolidated_df[failed_mask].copy()
            # Reset all download statuses and sources to 'Pending' before starting
            failed_df["auto_download_status"] = "Pending"
            failed_df["auto_download_message"] = ""
            failed_df["available_url"] = ""
            failed_df["download_source"] = ""
            failed_df["manual_dw_file_url"] = ""
            failed_df.to_csv(consolidated_path, index=False)
            # Immediately reload the CSV and update KPIs for the next page load
            _ = download_service.get_download_data(project_id)

            # Run download in background thread
            def run_failed() -> None:
                download_service.download_consolidated_pdfs(
                    project_path, project_id, failed_df
                )

            threading.Thread(target=run_failed, daemon=True).start()
            flash("Retry of failed downloads started in background.", "success")
        except Exception as e:
            flash(f"Error retrying failed downloads: {str(e)}", "error")
        return redirect(url_for("download_management", project_id=project_id))

    @app.route("/project/<project_id>/download_status", methods=["GET"])
    def download_status(project_id: str) -> Any:
        """Return current download status for AJAX polling."""
        try:
            download_service = DownloadService(
                papervisor, current_app.config.get("DATA_DIR", "data")
            )
            data = download_service.get_download_data(project_id)
            # Only return fields needed for AJAX update
            return {
                "papers": [
                    {
                        "paper_id": p["paper_id"],
                        "auto_download_status": p.get("auto_download_status", ""),
                        "available_url": p.get("available_url", ""),
                        "downloaded_file": p.get("downloaded_file", ""),
                        "download_source": p.get("download_source", ""),
                    }
                    for p in data["papers"]
                ],
                "downloaded_count": data["downloaded_count"],
                "manual_count": data["manual_count"],
                "total_papers": data["total_papers"],
            }, 200
        except Exception as e:
            return {"error": str(e)}, 500

    @app.route("/project/<project_id>/downloaded_file/<path:filename>")
    def serve_downloaded_file(project_id: str, filename: str) -> Any:
        """Serve a downloaded PDF file from the automatic directory."""
        import logging
        from flask import send_from_directory, abort, current_app
        import os

        download_service = DownloadService(
            papervisor, current_app.config.get("DATA_DIR", "data")
        )
        current_project = papervisor.get_project(project_id)
        if not current_project:
            logging.error(f"Project not found: {project_id}")
            abort(404, description=f"Project not found: {project_id}")
        project_path = download_service.data_dir / current_project.project_path
        pdf_dir = project_path / "pdfs" / "automatic"
        pdf_dir_abs = os.path.abspath(str(pdf_dir))
        file_path = pdf_dir / filename
        if not file_path.exists():
            logging.error(f"File not found: {file_path}")
            abort(404, description=f"File not found: {file_path}")
        logging.info(
            f"Serving file from directory: {pdf_dir_abs}, filename: {filename}"
        )
        try:
            return send_from_directory(pdf_dir_abs, str(filename), as_attachment=False)
        except Exception as e:
            logging.exception(f"Error serving file {file_path}: {e}")
            abort(404, description=f"Error serving file: {e}")

    @app.route("/project/<project_id>/manual_download/<paper_id>", methods=["POST"])
    def manual_download_pdf(project_id: str, paper_id: str) -> Any:
        """Download a PDF from a user-provided URL to the manual folder and update the CSV."""
        import pandas as pd

        url = request.form.get(f"manual_download_url_{paper_id}")
        if not url or not url.lower().startswith("http"):
            flash("Invalid or missing URL for manual download.", "error")
            return redirect(url_for("download_management", project_id=project_id))
        download_service = DownloadService(
            papervisor, current_app.config.get("DATA_DIR", "data")
        )
        current_project = papervisor.get_project(project_id)
        if not current_project:
            flash(f"Project '{project_id}' not found.", "error")
            return redirect(url_for("download_management", project_id=project_id))
        project_path = download_service.data_dir / current_project.project_path
        manual_dir = project_path / "pdfs" / "manual"
        manual_dir.mkdir(parents=True, exist_ok=True)
        consolidated_path = project_path / "pdfs" / "consolidated_papers.csv"
        consolidated_df = pd.read_csv(consolidated_path)
        # Ensure column is string type
        if "manual_dw_file_url" in consolidated_df.columns:
            consolidated_df["manual_dw_file_url"] = consolidated_df[
                "manual_dw_file_url"
            ].astype(str)
        try:
            import requests

            response = requests.get(url, timeout=20)
            if response.status_code == 200 and response.headers.get(
                "content-type", ""
            ).startswith("application/pdf"):
                filename = f"{paper_id}_manual.pdf"
                file_path = manual_dir / filename
                with open(file_path, "wb") as f:
                    f.write(response.content)
                # Update CSV with manual file url by paper_id value, not index
                consolidated_df.loc[
                    consolidated_df["paper_id"] == int(paper_id), "manual_dw_file_url"
                ] = filename
                consolidated_df.to_csv(consolidated_path, index=False)
                flash("Manual PDF downloaded successfully.", "success")
            else:
                flash(
                    f"Manual download failed: HTTP {response.status_code} or not a PDF.",
                    "error",
                )
        except Exception as e:
            flash(f"Manual download failed: {e}", "error")
        return redirect(url_for("download_management", project_id=project_id))

    @app.route("/project/<project_id>/manual_file/<path:filename>")
    def serve_manual_file(project_id: str, filename: str) -> Any:
        from flask import send_from_directory, abort

        download_service = DownloadService(
            papervisor, current_app.config.get("DATA_DIR", "data")
        )
        current_project = papervisor.get_project(project_id)
        if not current_project:
            abort(404)
        project_path = download_service.data_dir / current_project.project_path
        manual_dir = project_path / "pdfs" / "manual"
        try:
            return send_from_directory(manual_dir, filename, as_attachment=False)
        except Exception:
            abort(404)

    @app.route("/project/<project_id>/manual_upload/<paper_id>", methods=["POST"])
    def manual_upload_pdf(project_id: str, paper_id: str) -> Any:
        """Handle manual PDF upload to the manual folder and update the CSV."""
        import pandas as pd

        file = request.files.get(f"manual_upload_pdf_{paper_id}")
        if not file or file.filename == "":
            flash("No file selected for upload.", "error")
            return redirect(url_for("download_management", project_id=project_id))
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            flash("Only PDF files are allowed for manual upload.", "error")
            return redirect(url_for("download_management", project_id=project_id))
        download_service = DownloadService(
            papervisor, current_app.config.get("DATA_DIR", "data")
        )
        current_project = papervisor.get_project(project_id)
        if not current_project:
            flash(f"Project '{project_id}' not found.", "error")
            return redirect(url_for("download_management", project_id=project_id))
        project_path = download_service.data_dir / current_project.project_path
        manual_dir = project_path / "pdfs" / "manual"
        manual_dir.mkdir(parents=True, exist_ok=True)
        consolidated_path = project_path / "pdfs" / "consolidated_papers.csv"
        consolidated_df = pd.read_csv(consolidated_path)
        # Ensure column is string type
        if "manual_dw_file_url" in consolidated_df.columns:
            consolidated_df["manual_dw_file_url"] = consolidated_df[
                "manual_dw_file_url"
            ].astype(str)
        try:
            filename = f"{paper_id}_manual.pdf"
            file_path = manual_dir / filename
            file.save(file_path)
            # Robustly update by paper_id column or index
            if "paper_id" in consolidated_df.columns:
                mask = consolidated_df["paper_id"] == int(paper_id)
                if mask.any():
                    consolidated_df.loc[mask, "manual_dw_file_url"] = filename
                else:
                    flash(f"Paper ID {paper_id} not found in CSV.", "error")
                    return redirect(
                        url_for("download_management", project_id=project_id)
                    )
            elif (
                consolidated_df.index.name == "paper_id"
                or consolidated_df.index.name is not None
            ):
                if int(paper_id) in consolidated_df.index:
                    consolidated_df.loc[int(paper_id), "manual_dw_file_url"] = filename
                else:
                    flash(f"Paper ID {paper_id} not found in CSV index.", "error")
                    return redirect(
                        url_for("download_management", project_id=project_id)
                    )
            else:
                flash("CSV does not contain a 'paper_id' column or index.", "error")
                return redirect(url_for("download_management", project_id=project_id))
            consolidated_df.to_csv(consolidated_path, index=False)
            flash("Manual PDF uploaded successfully.", "success")
        except Exception as e:
            flash(f"Manual upload failed: {e}", "error")
        return redirect(url_for("download_management", project_id=project_id))
