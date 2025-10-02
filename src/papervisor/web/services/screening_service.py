"""
Screening business logic for Papervisor web app (refactored).
"""

from typing import Any, Dict, Optional
import pandas as pd
from pathlib import Path


class ScreeningService:
    def __init__(self, papervisor: Any, data_dir: str) -> None:
        self.papervisor = papervisor
        self.data_dir = Path(data_dir)

    def get_screening_data(self, project_id: str) -> Dict[str, Any]:
        current_project = self.papervisor.get_project(project_id)
        if not current_project:
            raise ValueError(f"Project '{project_id}' not found")
        project_path = self.data_dir / current_project.project_path
        consolidated_path = project_path / "pdfs" / "consolidated_papers.csv"
        if not consolidated_path.exists():
            raise FileNotFoundError(
                "No consolidated papers found. Please run download first."
            )
        papers_df = pd.read_csv(consolidated_path)
        extraction_status = self._load_extraction_status(project_path)
        screening_results = self._load_screening_results(project_path)
        papers_to_screen = []
        for idx, row in papers_df.iterrows():
            key = str(idx)
            action = extraction_status.get(key, {}).get("screening_action", "")
            if action == "include":
                result = screening_results.get(key, {})
                papers_to_screen.append(
                    {
                        "paper_id": idx,
                        "title": row.get("title", row.get("Title", "")),
                        "result": result.get("result", "pending"),
                        "justification": result.get("justification", ""),
                    }
                )
        total = len(papers_to_screen)
        done = len([p for p in papers_to_screen if p["result"] != "pending"])
        pending = total - done
        return {
            "papers": papers_to_screen,
            "total": total,
            "processed": done,
            "pending": pending,
        }

    def _load_extraction_status(
        self, project_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        if project_path is None:
            return {}
        status_file = project_path / "extraction_status.json"
        if status_file.exists():
            try:
                import json

                with open(status_file, "r") as f:
                    loaded_data: Dict[str, Any] = json.load(f)
                    return loaded_data
            except Exception as e:
                print(f"Error loading extraction status: {e}")
        return {}

    def _load_screening_results(
        self, project_path: Optional[Path] = None
    ) -> Dict[str, Any]:
        if project_path is None:
            return {}
        file = project_path / "screening_results.json"
        if file.exists():
            try:
                import json

                with open(file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
                    else:
                        return {}
            except Exception:
                return {}
        return {}
