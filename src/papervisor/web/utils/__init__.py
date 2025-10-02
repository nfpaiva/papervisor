# Utility functions for Papervisor web app

import pandas as pd
import re
import difflib
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_downloaded_files_with_source(
    project_path: Optional[Path] = None,
) -> List[Dict[str, str]]:
    """Get list of downloaded PDF files with their source directory."""
    files_info: List[Dict[str, str]] = []
    if project_path is None:
        return files_info
    auto_dir = project_path / "pdfs" / "automatic"
    if auto_dir.exists():
        for f in auto_dir.glob("*.pdf"):
            files_info.append(
                {"filename": f.name, "source": "automatic", "path": str(f)}
            )
    manual_dir = project_path / "pdfs" / "manual"
    if manual_dir.exists():
        for f in manual_dir.glob("*.pdf"):
            files_info.append({"filename": f.name, "source": "manual", "path": str(f)})
    return files_info


def get_paper_urls(paper: pd.Series) -> Dict[str, str]:
    """Extract available URLs from paper data."""
    urls = {}

    def safe_get_string(value: Any) -> str:
        if pd.isna(value):
            return ""
        return str(value).strip()

    doi = safe_get_string(paper.get("DOI", ""))
    if doi and doi.lower() != "nan":
        urls["DOI"] = f"https://doi.org/{doi}"
    article_url = safe_get_string(
        paper.get("ArticleURL", "") or paper.get("article_url", "")
    )
    if article_url and article_url.lower() != "nan":
        urls["Article Page"] = article_url
    fulltext_url = safe_get_string(paper.get("FullTextURL", ""))
    if fulltext_url and fulltext_url.lower() != "nan":
        urls["Full Text PDF"] = fulltext_url
    original_url = safe_get_string(paper.get("URL", ""))
    if original_url and original_url.lower() != "nan":
        urls["Original URL"] = original_url
    return urls


def normalize_text(text: Optional[str]) -> str:
    if not text:
        return ""
    return text.lower().strip().replace(" ", "").replace("-", "").replace("_", "")


def parse_authors(authors_str: str) -> List[str]:
    if not authors_str or pd.isna(authors_str):
        return []
    separators = [";", ",", " and ", " & ", "\n"]
    authors = [authors_str]
    for sep in separators:
        new_authors = []
        for author in authors:
            new_authors.extend([a.strip() for a in author.split(sep) if a.strip()])
        authors = new_authors
    cleaned_authors = []
    for author in authors:
        author = re.sub(r"\([^)]*\)", "", author).strip()
        author = re.sub(r"\s+", " ", author).strip()
        if author and len(author) > 1:
            cleaned_authors.append(author)
    return cleaned_authors


def parse_year(year_value: Any) -> Optional[int]:
    if not year_value or pd.isna(year_value):
        return None
    try:
        year_str = str(year_value).strip()
        year_match = re.search(r"\b(19|20)\d{2}\b", year_str)
        if year_match:
            return int(year_match.group())
        return int(float(year_str))
    except (ValueError, TypeError):
        return None


def extract_doi_from_text(text: str) -> str:
    doi_pattern = r"(?:doi:?\s*)?10\.\d{4,}\/[^\s]+"
    match = re.search(doi_pattern, text, re.IGNORECASE)
    return match.group().replace("doi:", "").strip() if match else ""


def calculate_paper_similarity(paper1: Dict[str, Any], paper2: Dict[str, Any]) -> float:
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
            1.0 if year1 == year2 else (0.8 if abs(year1_int - year2_int) <= 2 else 0.0)
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


def extract_title_from_text(text: str) -> str:
    lines = text.split("\n")
    for line in lines[:10]:
        line = line.strip()
        if len(line) > 10 and not line.isupper() and not line.isdigit():
            return line
    return ""


def extract_source_from_text(text: str) -> str:
    patterns = [
        r"(?:Published in|Proceedings of|Journal of|Conference on)\s+([^\n]+)",
        r"([A-Z][a-z]+ (?:Journal|Conference|Proceedings|Review))[^\n]*",
        r"(IEEE [^,\n]+)",
        r"(ACM [^,\n]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1).strip()
    return ""


def preprocess_text(text: str) -> str:
    text = re.sub(r"\n\s*\n\s*\n", "\n\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\d+\s*\n", "\n", text)
    text = re.sub(r"\n[A-Z\s]{10,}\n", "\n", text)
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
    text = re.sub(r"(\w)-\s*\n\s*(\w)", r"\1\2", text)
    text = text.strip()
    return text
