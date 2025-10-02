"""Web server for Papervisor PDF download management."""

from typing import Any

# PapervisorWebServer now delegates all web logic to the modularized web app in src/papervisor/web/app.py
# This file is retained for legacy compatibility or as a thin wrapper if needed.


class PapervisorWebServer:
    """Legacy wrapper for Papervisor web server. All web logic is now modularized under src/papervisor/web/."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        # Use the local create_app wrapper that handles data_dir argument
        self.app = create_app(*args, **kwargs)

    def run(
        self, host: str = "127.0.0.1", port: int = 5000, debug: bool = False
    ) -> None:
        """Run the Flask application."""
        self.app.run(host=host, port=port, debug=debug)

    # Optionally, you can add legacy methods or glue code here if needed for backward compatibility.
    # All route and business logic has been migrated to the modular structure.


def create_app(*args: Any, **kwargs: Any) -> Any:
    """Compatibility wrapper: return the Flask app from the modular web.app.create_app."""
    from papervisor.web.app import create_app as _create_app
    from papervisor.core import Papervisor

    # Handle test kwargs like data_dir, project_id
    data_dir = kwargs.pop("data_dir", "data")
    kwargs.pop("project_id", None)  # Tests may pass this but we don't use it directly

    # Instantiate Papervisor with the specified data_dir
    papervisor = Papervisor(data_dir=data_dir)

    # Pass papervisor instance to the real create_app
    return _create_app(papervisor=papervisor, **kwargs)


if __name__ == "__main__":
    from papervisor.web.app import create_app
    from papervisor.core import Papervisor

    papervisor = Papervisor()
    app = create_app(papervisor=papervisor)
    # Use localhost instead of binding to all interfaces for security
    app.run(host="127.0.0.1", port=5000, debug=True)
