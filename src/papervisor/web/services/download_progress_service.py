"""
Service for download progress operations.
"""

from typing import Any, Dict


class DownloadProgressService:
    def __init__(self, papervisor: Any) -> None:
        self.papervisor = papervisor

    def get_progress(self, project_id: str) -> Dict[str, Any]:
        # Try to get progress from papervisor or its download manager
        progress = getattr(self.papervisor, "progress", None)
        if progress and project_id in progress:
            # Convert to dict if needed
            prog = progress[project_id]
            if hasattr(prog, "to_dict"):
                dict_result: Dict[str, Any] = prog.to_dict()
                return dict_result
            elif hasattr(prog, "__dict__"):
                attr_result: Dict[str, Any] = dict(prog.__dict__)
                return attr_result
            else:
                # Fallback for any other type - try to convert to dict safely
                try:
                    fallback_result: Dict[str, Any] = dict(prog) if prog else {}
                    return fallback_result
                except (TypeError, ValueError):
                    return {"error": "Unable to convert progress to dict"}
        # Fallback: return empty/default progress
        return {
            "project_id": project_id,
            "total_papers": 0,
            "completed": 0,
            "failed": 0,
            "success": 0,
            "current_paper": "",
            "is_running": False,
            "error_message": "",
            "start_time": 0.0,
        }
