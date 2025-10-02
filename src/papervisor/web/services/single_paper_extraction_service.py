"""
Service for extracting text from a single paper in a project.
"""

from typing import Any, Dict


class SinglePaperExtractionService:
    def __init__(self, papervisor: Any, data_dir: str = "data") -> None:
        self.papervisor = papervisor
        self.data_dir = data_dir

    def extract_single_paper(self, project_id: str, paper_id: str) -> Dict[str, Any]:
        # Extract text from a single paper in the project
        if not project_id or not paper_id:
            return {"error": "Project ID and Paper ID are required."}
        import json
        from pathlib import Path
        import pandas as pd

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
        # Find the paper row
        try:
            idx = int(paper_id)
            paper = papers_df.iloc[idx]
        except Exception:
            return {"error": f"Paper ID '{paper_id}' not found in project."}
        # Locate PDF file
        pdf_filename = paper.get("pdf_filename")
        if not pdf_filename:
            auto_pdf = project_path / "pdfs" / "automatic" / f"{paper_id}_*.pdf"
            manual_pdf = project_path / "pdfs" / "manual" / f"{paper_id}_*.pdf"
            import glob

            matches = glob.glob(str(auto_pdf)) + glob.glob(str(manual_pdf))
            pdf_path = matches[0] if matches else None
        else:
            pdf_path = project_path / "pdfs" / "automatic" / pdf_filename
            if not pdf_path.exists():
                pdf_path = project_path / "pdfs" / "manual" / pdf_filename
        if not pdf_path or not Path(pdf_path).exists():
            status_data.setdefault(paper_id, {})["status"] = "missing_pdf"
            with open(status_file, "w") as f:
                json.dump(status_data, f, indent=2)
            return {"error": f"PDF file for paper {paper_id} not found."}
        # Extract text
        try:
            from PyPDF2 import PdfReader

            reader = PdfReader(str(pdf_path))
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            extracted_dir = project_path / "pdfs" / "extracted_texts"
            extracted_dir.mkdir(parents=True, exist_ok=True)
            text_file = extracted_dir / f"{paper_id}.txt"
            with open(text_file, "w", encoding="utf-8") as tf:
                tf.write(text)
            status_data.setdefault(paper_id, {})["status"] = "done"
            status_data[paper_id]["text_file"] = str(
                text_file.relative_to(project_path)
            )
        except Exception as e:
            status_data.setdefault(paper_id, {})["status"] = "failed"
            status_data[paper_id]["error"] = str(e)
        with open(status_file, "w") as f:
            json.dump(status_data, f, indent=2)
        return {
            "status": status_data[paper_id]["status"],
            "paper_id": paper_id,
            "project_id": project_id,
        }
