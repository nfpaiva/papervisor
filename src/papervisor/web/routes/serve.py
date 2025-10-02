"""
Static file serving routes for Papervisor web app (PDFs, extracted texts).
"""

from flask import send_from_directory, request, jsonify, current_app, Flask, Response
from pathlib import Path
from typing import Any, Optional, Union


def register_serve_routes(app: Flask, papervisor: Any) -> None:
    @app.route("/pdfs/<source>/<filename>")
    @app.route("/project/<project_id>/pdfs/<source>/<filename>")
    def serve_pdf(
        source: str, filename: str, project_id: Optional[str] = None
    ) -> Union[Response, tuple[Response, int]]:
        # Use provided project_id or fallback to query param
        current_project_id = project_id or request.args.get("project_id")
        if not current_project_id:
            return jsonify({"error": "Project ID required"}), 400
        project = papervisor.get_project(current_project_id)
        if not project:
            return jsonify({"error": f"Project '{current_project_id}' not found"}), 404
        project_path = (
            Path(current_app.config.get("DATA_DIR", "data")) / project.project_path
        )
        pdf_dir = project_path / "pdfs" / source
        file_path = pdf_dir / filename
        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404
        return send_from_directory(str(pdf_dir.absolute()), filename)

    @app.route("/extracted_texts/<filename>")
    @app.route("/project/<project_id>/extracted_texts/<filename>")
    def serve_extracted_text(
        filename: str, project_id: Optional[str] = None
    ) -> Union[Response, tuple[Response, int]]:
        current_project_id = project_id or request.args.get("project_id")
        if not current_project_id:
            return jsonify({"error": "Project ID required"}), 400
        project = papervisor.get_project(current_project_id)
        if not project:
            return jsonify({"error": f"Project '{current_project_id}' not found"}), 404
        project_path = (
            Path(current_app.config.get("DATA_DIR", "data")) / project.project_path
        )
        extracted_dir = project_path / "pdfs" / "extracted_texts"
        file_path = extracted_dir / filename
        if not file_path.exists():
            return jsonify({"error": "File not found"}), 404
        return send_from_directory(str(extracted_dir.absolute()), filename)
