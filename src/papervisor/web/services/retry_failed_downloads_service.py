"""
Service for retrying failed downloads for a project.
"""

from typing import Any, Dict


class RetryFailedDownloadsService:
    def __init__(self, papervisor: Any, data_dir: str = "data") -> None:
        self.papervisor = papervisor
        self.data_dir = data_dir

    def retry_failed_downloads(self, project_id: str) -> Dict[str, Any]:
        # TODO: Implement logic to retry failed downloads
        if not project_id:
            return {"error": "Project ID is required."}
        # Example: trigger retry process
        return {"status": "started", "project_id": project_id}
