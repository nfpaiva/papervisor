"""
Landing page routes for Papervisor web app (refactored).
"""

from flask import render_template, redirect, url_for, Flask
from typing import Any, Dict

# Dependency injection: pass papervisor instance to route handlers


def register_landing_routes(app: Flask, papervisor: Any) -> None:
    @app.route("/")
    def index() -> Any:
        # Single project mode: redirect to review page (to be handled)
        # Multi-project mode: show landing page
        return redirect(url_for("landing_page"))

    @app.route("/projects")
    def landing_page() -> str:
        try:
            projects = papervisor.list_projects()
            project_queries: Dict[str, Any] = {}
            project_stats: Dict[str, Any] = {}
            query_stats: Dict[str, Any] = {}

            for project in projects:
                queries = papervisor.list_project_queries(project.project_id)
                project_queries[project.project_id] = queries
                # Example stats (replace with real logic as needed)
                project_stats[project.project_id] = {
                    "total_papers": 0,
                    "downloaded_papers": 0,
                    "has_consolidated": False,
                    "consolidated_date": "",
                }
                query_stats[project.project_id] = {}
                for query in queries:
                    query_stats[project.project_id][query.id] = {"paper_count": 0}

            return render_template(
                "landing.html",
                projects=projects,
                project_queries=project_queries,
                project_stats=project_stats,
                query_stats=query_stats,
            )
        except Exception as e:
            return render_template("error.html", error=str(e))
