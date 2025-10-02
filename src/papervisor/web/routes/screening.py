"""
Screening routes for Papervisor web app (refactored).
"""

from flask import render_template, make_response, current_app, Flask
from papervisor.web.services.screening_service import ScreeningService
from typing import Any


def register_screening_routes(app: Flask, papervisor: Any) -> None:
    @app.route("/project/<project_id>/screening")
    def screening(project_id: str) -> Any:
        try:
            screening_service = ScreeningService(
                papervisor, current_app.config.get("DATA_DIR", "data")
            )
            data = screening_service.get_screening_data(project_id)
            return make_response(
                render_template(
                    "screening.html",
                    project_id=project_id,
                    papers=data["papers"],
                    total=data["total"],
                    processed=data["processed"],
                    pending=data["pending"],
                )
            )
        except Exception as e:
            return render_template("error.html", error=str(e))
