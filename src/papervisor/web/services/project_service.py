"""
Project-related business logic for Papervisor web app (refactored).
"""

import ast
import pandas as pd
from typing import Any, Dict


class ProjectService:
    def __init__(self, papervisor: Any, data_dir: str = "data") -> None:
        self.papervisor = papervisor
        self.data_dir = data_dir

    def get_projects_with_stats(self) -> Dict[str, Any]:
        """
        Returns a dict with projects, project_queries, project_stats, query_stats.
        (Stub: fill in with logic from old landing_page route)
        """
        projects = self.papervisor.list_projects()
        # TODO: Extract and compute project_queries, project_stats, query_stats
        return {
            "projects": projects,
            "project_queries": {},
            "project_stats": {},
            "query_stats": {},
        }

    def get_project_dashboard(self, project_id: str) -> Dict[str, Any]:
        # TODO: Implement logic to get project dashboard data
        if not project_id:
            return {"error": "Project ID is required."}
        # Example: return dummy data for now
        return {
            "project_id": project_id,
            "papers": [],
            "download_stats": {},
            "total_papers": 0,
        }

    def consolidate_project(self, project_id: str) -> Dict[str, Any]:
        """
        Concatenate all query result CSVs for a project into one DataFrame and write consolidated_papers.csv (no deduplication).
        Adds merged_source_queries as an array, and leaves deduplication columns empty (to be filled after deduplication step).
        """
        from pathlib import Path

        if not project_id:
            return {"error": "Project ID is required."}
        # Get project path
        current_project = self.papervisor.get_project(project_id)
        if not current_project:
            return {"error": f"Project '{project_id}' not found"}
        project_path = Path(self.data_dir) / current_project.project_path
        results_dir = project_path / "results"
        pdfs_dir = project_path / "pdfs"
        # Find all query CSVs in results_dir (excluding consolidated_papers.csv)
        query_csvs = [
            f for f in results_dir.glob("*.csv") if f.name != "consolidated_papers.csv"
        ]
        if not query_csvs:
            return {"error": "No query CSVs found to consolidate."}
        # Read and concatenate all query CSVs
        dfs = []
        for csv_path in query_csvs:
            try:
                df = pd.read_csv(csv_path)
                df["source_queries"] = csv_path.stem  # Track source query
                dfs.append(df)
            except Exception as e:
                print(f"Error reading CSV {csv_path}: {e}")
                continue
        if not dfs:
            return {"error": "No valid query CSVs to consolidate."}
        all_papers = pd.concat(dfs, ignore_index=True)
        # Assign paper_id as first column (no deduplication)
        all_papers = all_papers.reset_index(drop=True)
        all_papers.insert(0, "paper_id", all_papers.index.astype(str))
        # Aggregate merged_source_queries as an array of unique queries per paper
        if "merged_source_queries" not in all_papers.columns:
            grouped = (
                all_papers.groupby("paper_id")["source_queries"]
                .apply(lambda x: list(sorted(set(x))))
                .reset_index()
            )
            all_papers = all_papers.drop_duplicates(subset=["paper_id"]).reset_index(
                drop=True
            )
            all_papers = all_papers.merge(grouped, on="paper_id", suffixes=("", "_agg"))
            all_papers["merged_source_queries"] = all_papers[
                "source_queries_agg"
            ].apply(lambda x: str(x))
            all_papers = all_papers.drop(
                columns=["source_queries_agg"]
            )  # keep original source_queries for traceability
        # Prepare empty columns for deduplication/selection (empty string, not False/[])
        all_papers["is_duplicate"] = ""
        all_papers["duplicate_group"] = ""
        all_papers["is_reference"] = ""
        all_papers["will_progress"] = ""
        # Write consolidated_papers.csv
        consolidated_path = pdfs_dir / "consolidated_papers.csv"
        all_papers.to_csv(consolidated_path, index=False)
        return {
            "status": "success",
            "project_id": project_id,
            "consolidated_path": str(consolidated_path),
        }

    def mark_duplicates(
        self, project_id: str, form_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        # TODO: Implement logic to mark duplicates
        if not project_id:
            return {"error": "Project ID is required."}
        return {"status": "success", "project_id": project_id}

    def resolve_duplicates_and_proceed(
        self, project_id: str, form_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update consolidated_papers.csv to add merged_source_queries and is_reference columns.
        For each duplicate group, set is_reference=True for the chosen record, False for others, based only on UI selection.
        Unique papers (not in any group, i.e., is_duplicate is False/0/empty/NaN) are also marked as reference.
        All other papers (duplicates not selected as reference) are is_reference=False.
        Robust to all representations of 'not duplicate'.
        """
        # Load and validate project data
        df, consolidated_path = self._load_project_for_duplicates(project_id)
        if isinstance(df, dict):  # Error case
            return df

        # Initialize required columns
        df = self._initialize_duplicate_columns(df)

        # Process form data to build group mappings
        paper_to_group, group_to_papers, ref_paper_map = self._parse_form_data(
            form_data
        )

        # Apply duplicate group logic
        df = self._apply_duplicate_grouping(df, paper_to_group, group_to_papers)

        # Set reference relationships
        df = self._set_reference_relationships(df, paper_to_group, ref_paper_map)

        # Save updated dataframe
        df.to_csv(consolidated_path, index=False)
        return {
            "status": "success",
            "project_id": project_id,
            "consolidated_path": str(consolidated_path),
        }

    def _load_project_for_duplicates(self, project_id: str) -> tuple[Any, Any]:
        """Load and validate project data for duplicate resolution."""
        from pathlib import Path

        if not project_id:
            return {"error": "Project ID is required."}, None
        current_project = self.papervisor.get_project(project_id)
        if not current_project:
            return {"error": f"Project '{project_id}' not found"}, None
        project_path = Path(self.data_dir) / current_project.project_path
        pdfs_dir = project_path / "pdfs"
        consolidated_path = pdfs_dir / "consolidated_papers.csv"
        if not consolidated_path.exists():
            return {"error": "No consolidated papers file found."}, None
        df = pd.read_csv(consolidated_path)
        return df, consolidated_path

    def _initialize_duplicate_columns(self, df: Any) -> Any:
        """Initialize required columns for duplicate processing."""
        # Add columns if missing
        if "merged_source_queries" not in df.columns:
            df["merged_source_queries"] = df["source_queries"].astype(str)

        # Drop and recreate deduplication columns for clean state
        for col in [
            "is_duplicate",
            "reference_paper_id",
            "reference_paper",
            "is_reference",
            "will_progress",
        ]:
            if col in df.columns:
                df = df.drop(columns=[col])
        df["is_duplicate"] = False
        df["reference_paper_id"] = ""
        df["reference_paper"] = ""
        df["is_reference"] = False
        df["will_progress"] = False
        return df

    def _parse_form_data(
        self, form_data: Dict[str, Any]
    ) -> tuple[dict[str, str], dict[str, list[str]], dict[str, str]]:
        """Parse form data to extract group and reference mappings."""
        paper_to_group = {}
        group_to_papers = {}
        ref_paper_map = {}

        # Build group mappings
        for k, v in form_data.items():
            if k.startswith("group_"):
                group_id = k.split("_", 1)[1]
                if isinstance(v, list):
                    group_papers = [str(pid) for pid in v]
                else:
                    group_papers = [str(v)]
                group_to_papers[group_id] = group_papers
                for pid in group_papers:
                    paper_to_group[pid] = group_id

        # Build reference mappings
        for k, v in form_data.items():
            if k.startswith("reference_"):
                group_id = k.split("_", 1)[1]
                ref_paper_map[group_id] = str(v)

        return paper_to_group, group_to_papers, ref_paper_map

    def _apply_duplicate_grouping(
        self,
        df: Any,
        paper_to_group: dict[str, str],
        group_to_papers: dict[str, list[str]],
    ) -> Any:
        """Apply duplicate group logic to dataframe."""
        # Create duplicate_group column
        duplicate_group_col = []
        for idx, row in df.iterrows():
            pid = str(row["paper_id"])
            paper_group_id = paper_to_group.get(pid, "")
            if paper_group_id and paper_group_id in group_to_papers:
                duplicate_group_col.append(str(group_to_papers[paper_group_id]))
            else:
                duplicate_group_col.append("[]")
        df["duplicate_group"] = duplicate_group_col

        # Set is_duplicate based on group size
        df["is_duplicate"] = df["duplicate_group"].apply(
            lambda x: len(ast.literal_eval(x)) > 1
        )
        return df

    def _set_reference_relationships(
        self, df: Any, paper_to_group: dict[str, str], ref_paper_map: dict[str, str]
    ) -> Any:
        """Set reference paper relationships."""
        # Set reference_paper_id for group members
        reference_paper_id_col = []
        for idx, row in df.iterrows():
            pid = str(row["paper_id"])
            ref_group_id = paper_to_group.get(pid, "")
            if ref_group_id and ref_group_id in ref_paper_map:
                reference_paper_id_col.append(ref_paper_map[ref_group_id])
            else:
                reference_paper_id_col.append("")
        df["reference_paper_id"] = reference_paper_id_col

        # Set is_reference and will_progress
        df["is_reference"] = (
            df["reference_paper_id"].astype(str) == df["paper_id"].astype(str)
        ) & (df["is_duplicate"])
        df["will_progress"] = df["is_reference"] | (~df["is_duplicate"])

        return df
