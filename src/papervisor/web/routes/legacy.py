"""
Legacy and redirect routes for Papervisor web app (modularized).
"""

from flask import redirect, url_for, request, Flask
from typing import Any


def register_legacy_routes(app: Flask, papervisor: Any) -> None:
    @app.route("/review")
    def review_legacy() -> Any:
        project_id = request.args.get("project_id")
        if not project_id:
            # TODO: Optionally redirect to landing or error
            return redirect(url_for("landing_page"))
        return redirect(url_for("review_papers", project_id=project_id))

    @app.route("/downloads")
    def downloads_legacy() -> Any:
        project_id = request.args.get("project_id")
        if not project_id:
            return redirect(url_for("landing_page"))
        return redirect(url_for("download_management", project_id=project_id))

    @app.route("/screening")
    def screening_legacy() -> Any:
        project_id = request.args.get("project_id")
        if not project_id:
            return redirect(url_for("landing_page"))
        return redirect(url_for("screening", project_id=project_id))
