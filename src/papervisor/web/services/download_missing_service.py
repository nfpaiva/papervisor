"""
Service for triggering download of all missing papers for a project.
"""

from typing import Any, Dict


class DownloadMissingService:
    def __init__(self, papervisor: Any, data_dir: str = "data") -> None:
        self.papervisor = papervisor
        self.data_dir = data_dir

    def download_all_missing(self, project_id: str) -> Dict[str, Any]:
        # Trigger download of all missing papers for the project in a background thread
        if not project_id:
            return {"error": "Project ID is required."}
        from pathlib import Path
        import pandas as pd
        import threading

        project = self.papervisor.get_project(project_id)
        if not project:
            return {"error": f"Project '{project_id}' not found."}
        project_path = Path(self.data_dir) / project.project_path
        consolidated_path = project_path / "pdfs" / "consolidated_papers.csv"
        if not consolidated_path.exists():
            return {
                "error": "No consolidated papers file found. Please run the download process first."
            }
        papers_df = pd.read_csv(consolidated_path)
        # status_file may be used in future to track extraction progress

        def download_worker() -> None:
            from papervisor.web.services.download_service import DownloadService

            download_service = DownloadService(None, self.data_dir)
            # Use the consolidated download method
            try:
                download_service.download_consolidated_pdfs(
                    project_path, project_id, papers_df, max_downloads=None
                )
            except Exception as e:
                print(f"Error downloading missing papers for project {project_id}: {e}")

        thread = threading.Thread(target=download_worker, daemon=True)
        thread.start()
        return {"status": "started", "project_id": project_id, "count": len(papers_df)}
