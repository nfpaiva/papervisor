"""
Review-related business logic for Papervisor web app (refactored).
"""

from typing import Any, Dict, List, Optional
import pandas as pd
from pathlib import Path
import difflib


class ReviewService:
    def __init__(self, papervisor: Any, data_dir: str) -> None:
        self.papervisor = papervisor
        self.data_dir = Path(data_dir)

    def get_review_data(self, project_id: str) -> Dict[str, Any]:
        current_project = self.papervisor.get_project(project_id)
        if not current_project:
            raise ValueError(f"Project '{project_id}' not found")
        project_path = self.data_dir / current_project.project_path
        consolidated_path = project_path / "pdfs" / "consolidated_papers.csv"
        if not consolidated_path.exists():
            raise FileNotFoundError(
                "No consolidated papers file found. Please run the consolidation process first."
            )

        # Load search queries for display
        search_queries = []
        try:
            search_queries = current_project.load_project_queries()
        except Exception:
            # If queries can't be loaded, continue without them
            search_queries = []
        papers_df = pd.read_csv(consolidated_path)
        papers_data = []
        for idx, paper in papers_df.iterrows():
            paper_id = str(paper.get("paper_id", idx))
            title = paper.get("title", paper.get("Title", "Unknown Title"))
            authors = paper.get("authors", paper.get("Authors", "Unknown Authors"))
            year = paper.get("year", paper.get("Year", "Unknown"))
            source_queries = paper.get("source_queries", "")
            doi = paper.get("DOI", "")
            if pd.isna(doi):
                doi = ""
            abstract = paper.get("Abstract", "")
            if pd.isna(abstract):
                abstract = ""
            elif isinstance(abstract, str) and len(abstract) > 200:
                abstract = abstract[:200] + "..."
            is_duplicate = paper.get("is_duplicate", False)
            if pd.isna(is_duplicate):
                is_duplicate = False
            duplicate_of = paper.get("duplicate_of", "")
            if pd.isna(duplicate_of):
                duplicate_of = ""
            papers_data.append(
                {
                    "paper_id": paper_id,
                    "title": title,
                    "authors": authors,
                    "year": year,
                    "source_queries": source_queries,
                    "doi": str(doi) if not pd.isna(doi) else "",
                    "abstract": abstract,
                    "is_duplicate": is_duplicate,
                    "duplicate_of": duplicate_of,
                }
            )
        paper_groups = self._group_similar_papers(papers_data)
        return {
            "paper_groups": paper_groups,
            "total_papers": len(papers_data),
            "search_queries": search_queries,
        }

    def _group_similar_papers(
        self, papers_data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        groups_list: List[Dict[str, Any]] = []
        processed_papers = set()
        for i, paper in enumerate(papers_data):
            if paper["paper_id"] in processed_papers:
                continue
            current_group = [paper]
            processed_papers.add(paper["paper_id"])
            for j, other_paper in enumerate(papers_data):
                if i != j and other_paper["paper_id"] not in processed_papers:
                    similarity = self._calculate_paper_similarity(paper, other_paper)
                    if similarity > 0.6:
                        other_paper["similarity_score"] = similarity
                        other_paper["suggested_duplicate_of"] = paper["paper_id"]
                        current_group.append(other_paper)
                        processed_papers.add(other_paper["paper_id"])
            current_group.sort(
                key=lambda x: x.get("similarity_score", 1.0), reverse=True
            )
            # Add suggested_reference_id as the first paper's paper_id in the group
            suggested_reference_id = (
                current_group[0]["paper_id"] if current_group else None
            )
            group_info = {
                "group_id": f"group_{len(groups_list)}",
                "papers": current_group,
                "is_potential_duplicate_group": len(current_group) > 1,
                "group_size": len(current_group),
                "suggested_reference_id": suggested_reference_id,
            }
            groups_list.append(group_info)
        return groups_list

    def _calculate_paper_similarity(
        self, paper1: Dict[str, Any], paper2: Dict[str, Any]
    ) -> float:
        def normalize_text(text: Optional[str]) -> str:
            if not text or pd.isna(text):
                return ""
            return (
                str(text)
                .lower()
                .strip()
                .replace(" ", "")
                .replace("-", "")
                .replace("_", "")
            )

        title1 = normalize_text(paper1.get("title", ""))
        title2 = normalize_text(paper2.get("title", ""))
        title_similarity = difflib.SequenceMatcher(None, title1, title2).ratio()
        authors1 = normalize_text(paper1.get("authors", ""))
        authors2 = normalize_text(paper2.get("authors", ""))
        author_similarity = difflib.SequenceMatcher(None, authors1, authors2).ratio()
        year1 = str(paper1.get("year", ""))
        year2 = str(paper2.get("year", ""))
        try:
            year1_int = int(float(year1)) if year1 and year1 != "Unknown" else 0
            year2_int = int(float(year2)) if year2 and year2 != "Unknown" else 0
            year_similarity = (
                1.0
                if year1 == year2
                else (0.8 if abs(year1_int - year2_int) <= 2 else 0.0)
            )
        except (ValueError, TypeError):
            year_similarity = 1.0 if year1 == year2 else 0.0
        doi1 = normalize_text(paper1.get("doi", ""))
        doi2 = normalize_text(paper2.get("doi", ""))
        doi_similarity = 1.0 if doi1 and doi2 and doi1 == doi2 else 0.0
        if doi_similarity == 1.0:
            return 1.0
        weights = {"title": 0.6, "authors": 0.3, "year": 0.1}
        final_similarity = (
            title_similarity * weights["title"]
            + author_similarity * weights["authors"]
            + year_similarity * weights["year"]
        )
        return final_similarity
