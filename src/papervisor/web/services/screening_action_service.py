"""
Service for saving screening actions for papers in a project.
"""

from typing import Any, Dict


class ScreeningActionService:
    def __init__(self, papervisor: Any, data_dir: str = "data") -> None:
        self.papervisor = papervisor
        self.data_dir = data_dir

    def save_screening_actions(
        self, project_id: str, screening_actions: Dict[str, Any]
    ) -> Dict[str, Any]:
        # Save screening actions to extraction_status.json for the project
        if not project_id or not screening_actions:
            return {"error": "Project ID and screening actions are required."}
        import json
        from pathlib import Path

        project = self.papervisor.get_project(project_id)
        if not project:
            return {"error": f"Project '{project_id}' not found."}
        project_path = Path(self.data_dir) / project.project_path
        status_file = project_path / "extraction_status.json"
        # Load existing status
        if status_file.exists():
            try:
                with open(status_file, "r") as f:
                    status_data = json.load(f)
            except Exception:
                status_data = {}
        else:
            status_data = {}
        # Update screening actions
        for paper_id, action in screening_actions.items():
            if paper_id not in status_data:
                status_data[paper_id] = {}
            status_data[paper_id]["screening_action"] = action
        # Save back
        with open(status_file, "w") as f:
            json.dump(status_data, f, indent=2)
        return {
            "status": "success",
            "project_id": project_id,
            "count": len(screening_actions),
        }
