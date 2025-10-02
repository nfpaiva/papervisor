"""
Project-level routes for Papervisor web app (dashboard, consolidate, mark duplicates).
"""

from flask import (
    request,
    render_template,
    redirect,
    url_for,
    flash,
    current_app,
)
from papervisor.web.services.project_service import ProjectService
from typing import Any, Optional
from flask import Flask


def register_project_routes(app: Flask, papervisor: Any) -> None:
    @app.route("/project/<project_id>")
    def project_dashboard(project_id: str) -> Any:
        project_service = ProjectService(
            papervisor, current_app.config.get("DATA_DIR", "data")
        )
        data = project_service.get_project_dashboard(project_id)
        if "error" in data:
            flash(data["error"], "error")
            return redirect(url_for("landing_page"))
        return render_template("dashboard.html", **data)

    @app.route("/consolidate", methods=["POST"])
    def consolidate_project() -> Any:
        project_id = request.form.get("project_id")
        if not project_id:
            flash("Project ID is required", "error")
            return redirect(url_for("landing_page"))
        project_service = ProjectService(
            papervisor, current_app.config.get("DATA_DIR", "data")
        )
        result = project_service.consolidate_project(project_id)
        if "error" in result:
            flash(result["error"], "error")
        else:
            flash("Project consolidated successfully!", "success")
        # Redirect to review page after consolidation
        return redirect(url_for("review_papers", project_id=project_id))

    @app.route("/mark_duplicates", methods=["POST"])
    @app.route("/project/<project_id>/mark_duplicates", methods=["POST"])
    def mark_duplicates(project_id: Optional[str] = None) -> Any:
        if not project_id:
            project_id = request.args.get("project_id")
        if not project_id:
            return redirect(url_for("landing_page"))  # Handle missing project_id
        project_service = ProjectService(
            papervisor, current_app.config.get("DATA_DIR", "data")
        )
        result = project_service.mark_duplicates(project_id, request.form)
        if "error" in result:
            flash(result["error"], "error")
        else:
            flash("Duplicate assignments saved.", "success")
        return redirect(url_for("review_papers", project_id=project_id))

    @app.route("/project/<project_id>/resolve_duplicates_and_proceed", methods=["POST"])
    def resolve_duplicates_and_proceed(project_id: str) -> Any:
        project_service = ProjectService(
            papervisor, current_app.config.get("DATA_DIR", "data")
        )
        result = project_service.resolve_duplicates_and_proceed(
            project_id, request.form
        )
        if "error" in result:
            flash(result["error"], "error")
            return redirect(url_for("review_papers", project_id=project_id))
        flash("Duplicates resolved. Proceeding to download management.", "success")
        return redirect(url_for("download_management", project_id=project_id))
