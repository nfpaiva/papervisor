"""
Text extraction routes for Papervisor web app (refactored).
"""

from flask import render_template, request, current_app, Flask
from papervisor.web.services.extraction_service import ExtractionService
from typing import Any


def register_extraction_routes(app: Flask, papervisor: Any) -> None:
    @app.route("/text_extraction")
    def text_extraction() -> str:
        try:
            project_id = request.args.get("project_id")
            if not project_id:
                return render_template("error.html", error="No project specified")
            extraction_service = ExtractionService(
                papervisor, current_app.config.get("DATA_DIR", "data")
            )
            data = extraction_service.get_extraction_data(project_id)
            return render_template(
                "text_extraction.html",
                project_id=project_id,
                papers=data["papers"],
                extraction_status=data["extraction_status"],
            )
        except Exception as e:
            return render_template("error.html", error=str(e))
