"""
Flask app factory for Papervisor web server (refactored).
"""

from flask import Flask
import os
from typing import Any
from .routes.landing import register_landing_routes
from .routes.review import register_review_routes
from .routes.download import register_download_routes
from .routes.extraction import register_extraction_routes
from .routes.screening import register_screening_routes
from .routes.api import register_api_routes
from .routes.legacy import register_legacy_routes
from .routes.actions import register_action_routes
from .routes.serve import register_serve_routes
from .routes.project import register_project_routes


def create_app(config_object: Any = None, papervisor: Any = None) -> Flask:
    app = Flask(__name__)
    # Load config
    if config_object:
        app.config.from_object(config_object)
    # Set secret key from env or fallback
    app.secret_key = os.environ.get(
        "PAPERVISOR_SECRET_KEY",
        "papervisor_secret_key_change_in_production",  # nosec B105
    )
    # Register modular blueprints/routes
    register_landing_routes(app, papervisor)
    register_review_routes(app, papervisor)
    register_download_routes(app, papervisor)
    register_extraction_routes(app, papervisor)
    register_screening_routes(app, papervisor)
    register_api_routes(app, papervisor)
    register_legacy_routes(app, papervisor)
    register_action_routes(app, papervisor)
    register_serve_routes(app, papervisor)
    register_project_routes(app, papervisor)
    # ...register additional blueprints as needed...
    return app
