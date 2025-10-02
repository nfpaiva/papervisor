"""
Service for cancelling ongoing downloads for a project.
"""

from typing import Any, Dict


class CancelDownloadService:
    def __init__(self, papervisor: Any) -> None:
        self.papervisor = papervisor

    def cancel_download(self, project_id: str) -> Dict[str, Any]:
        # TODO: Implement logic to cancel download
        if not project_id:
            return {"error": "Project ID is required."}
        # Example: set is_running to False in progress
        progress = getattr(self.papervisor, "_download_progress", None)
        if progress and project_id in progress:
            progress[project_id].is_running = False
            return {"status": "cancelled", "project_id": project_id}
        return {"error": "No active download to cancel."}
