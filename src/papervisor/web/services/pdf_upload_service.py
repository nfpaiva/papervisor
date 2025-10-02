"""
Service for handling PDF uploads for a project.
"""

from pathlib import Path
from typing import Any, Dict


class PDFUploadService:
    def __init__(self, papervisor: Any, data_dir: str = "data") -> None:
        self.papervisor = papervisor
        self.data_dir = Path(data_dir)

    def upload_pdf(
        self, project_id: str, paper_id: str, uploaded_file: Any
    ) -> Dict[str, Any]:
        # TODO: Implement logic to save uploaded PDF to the correct location
        if not project_id or not paper_id or not uploaded_file:
            return {"error": "Project ID, Paper ID, and PDF file are required."}
        # Example: save file to manual directory
        manual_dir = (
            self.data_dir / "literature_reviews" / project_id / "pdfs" / "manual"
        )
        manual_dir.mkdir(parents=True, exist_ok=True)
        file_path = manual_dir / uploaded_file.filename
        uploaded_file.save(str(file_path))
        return {
            "status": "success",
            "filename": uploaded_file.filename,
            "project_id": project_id,
            "paper_id": paper_id,
        }
