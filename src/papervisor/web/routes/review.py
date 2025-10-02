"""
Review page routes for Papervisor web app (refactored).
"""

from flask import render_template, current_app, Flask
from papervisor.web.services.review_service import ReviewService
from typing import Any


def register_review_routes(app: Flask, papervisor: Any) -> None:
    @app.route("/project/<project_id>/review")
    def review_papers(project_id: str) -> str:
        try:
            review_service = ReviewService(
                papervisor, current_app.config.get("DATA_DIR", "data")
            )
            data = review_service.get_review_data(project_id)
            return render_template(
                "review_papers.html",
                project_id=project_id,
                paper_groups=data["paper_groups"],
                total_papers=data["total_papers"],
                search_queries=data.get("search_queries", []),
            )
        except Exception as e:
            return render_template("error.html", error=str(e))
