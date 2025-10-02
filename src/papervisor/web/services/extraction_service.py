"""
Text extraction business logic for Papervisor web app (refactored).
"""

from typing import Any, Dict, Optional
import pandas as pd
from pathlib import Path


class ExtractionService:
    def __init__(self, papervisor: Any, data_dir: str) -> None:
        self.papervisor = papervisor
        self.data_dir = Path(data_dir)

    def get_extraction_data(self, project_id: str) -> Dict[str, Any]:
        current_project = self.papervisor.get_project(project_id)
        if not current_project:
            raise ValueError(f"Project '{project_id}' not found")
        project_path = self.data_dir / current_project.project_path
        consolidated_path = project_path / "pdfs" / "consolidated_papers.csv"
        if not consolidated_path.exists():
            raise FileNotFoundError(
                "No consolidated papers file found. Please run the download process first."
            )
        papers_df = pd.read_csv(consolidated_path)
        extraction_status = self._load_extraction_status(project_path)
        papers_data = []
        for idx, paper in papers_df.iterrows():
            paper_id = str(idx)
            title = paper.get("title", paper.get("Title", "Unknown Title"))
            authors = paper.get("authors", paper.get("Authors", "Unknown Authors"))
            year = paper.get("year", paper.get("Year", "Unknown"))
            papers_data.append(
                {
                    "paper_id": paper_id,
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "status": extraction_status.get(paper_id, {}).get(
                        "status", "pending"
                    ),
                    "sections": extraction_status.get(paper_id, {}).get("sections", []),
                    "json_file": extraction_status.get(paper_id, {}).get(
                        "json_file", ""
                    ),
                }
            )
        return {
            "papers": papers_data,
            "extraction_status": extraction_status,
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
