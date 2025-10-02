"""
API endpoints for Papervisor web app (modularized).
"""

from flask import jsonify, request, current_app
from papervisor.web.services.paper_service import PaperService
from papervisor.web.services.download_progress_service import (
    DownloadProgressService,
)
from typing import Any, Optional
from flask import Flask


def register_api_routes(app: Flask, papervisor: Any) -> None:
    @app.route("/api/paper/<paper_id>")
    @app.route("/project/<project_id>/api/paper/<paper_id>")
    def api_paper_details(paper_id: str, project_id: Optional[str] = None) -> Any:
        if not project_id:
            project_id = request.args.get("project_id")
        if not project_id:
            return jsonify({"error": "Project ID required"}), 400
        paper_service = PaperService(
            papervisor, current_app.config.get("DATA_DIR", "data")
        )
        result = paper_service.get_paper_details(project_id, paper_id)
        if "error" in result:
            return jsonify(result), 404
        return jsonify(result)

    @app.route("/api/download_progress")
    @app.route("/project/<project_id>/api/download_progress")
    def api_download_progress(project_id: Optional[str] = None) -> Any:
        if not project_id:
            project_id = request.args.get("project_id")
        if not project_id:
            return jsonify({"error": "Project ID required"}), 400
        progress_service = DownloadProgressService(papervisor)
        result = progress_service.get_progress(project_id)
        return jsonify(result)
