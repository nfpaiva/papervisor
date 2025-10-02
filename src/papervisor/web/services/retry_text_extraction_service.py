"""
Service for retrying text extraction for all papers in a project.
"""

from typing import Any, Dict


class RetryTextExtractionService:
    def __init__(self, papervisor: Any, data_dir: str = "data") -> None:
        self.papervisor = papervisor
        self.data_dir = data_dir

    def retry_all_text_extraction(self, project_id: str) -> Dict[str, Any]:
        # Retry extraction for all papers: reset status and trigger extraction
        if not project_id:
            return {"error": "Project ID is required."}
        import json
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
        # Reset all papers to 'in_progress' (force retry)
        for idx, paper in papers_df.iterrows():
            paper_id = str(idx)
            if paper_id not in status_data:
                status_data[paper_id] = {}
            status_data[paper_id]["status"] = "in_progress"
            status_data[paper_id].pop("error", None)
            status_data[paper_id].pop("text_file", None)
        with open(status_file, "w") as f:
            json.dump(status_data, f, indent=2)

        def extract_text_worker() -> None:
            for idx, paper in papers_df.iterrows():
                paper_id = str(idx)
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
                    status_data[paper_id]["status"] = "missing_pdf"
                    continue
                try:
                    from PyPDF2 import PdfReader

                    reader = PdfReader(str(pdf_path))
                    text = "\n".join(page.extract_text() or "" for page in reader.pages)
                    extracted_dir = project_path / "pdfs" / "extracted_texts"
                    extracted_dir.mkdir(parents=True, exist_ok=True)
                    text_file = extracted_dir / f"{paper_id}.txt"
                    with open(text_file, "w", encoding="utf-8") as tf:
                        tf.write(text)
                    status_data[paper_id]["status"] = "done"
                    status_data[paper_id]["text_file"] = str(
                        text_file.relative_to(project_path)
                    )
                except Exception as e:
                    status_data[paper_id]["status"] = "failed"
                    status_data[paper_id]["error"] = str(e)
                with open(status_file, "w") as f:
                    json.dump(status_data, f, indent=2)

        thread = threading.Thread(target=extract_text_worker, daemon=True)
        thread.start()
        return {"status": "started", "project_id": project_id, "count": len(papers_df)}
