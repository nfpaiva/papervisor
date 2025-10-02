"""
Service for paper-level operations (fetching details, etc.).
"""

import pandas as pd
from pathlib import Path
from typing import Any, Dict


class PaperService:
    def __init__(self, papervisor: Any, data_dir: str = "data") -> None:
        self.papervisor = papervisor
        self.data_dir = Path(data_dir)

    def get_paper_details(self, project_id: str, paper_id: str) -> Dict[str, Any]:
        """Fetch details for a single paper by project and paper_id."""
        project = self.papervisor.get_project(project_id)
        if not project:
            return {"error": f"Project '{project_id}' not found"}
        project_path = self.data_dir / project.project_path
        consolidated_path = project_path / "pdfs" / "consolidated_papers.csv"
        if not consolidated_path.exists():
            return {"error": "No consolidated papers found."}
        papers_df = pd.read_csv(consolidated_path)
        try:
            paper_idx = int(paper_id)
            if paper_idx >= len(papers_df):
                return {"error": "Invalid paper ID."}
            paper = papers_df.iloc[paper_idx].to_dict()
            paper["paper_id"] = paper_idx
            return paper
        except Exception as e:
            return {"error": str(e)}
