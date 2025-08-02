"""CSV data loader for Publish or Perish exports."""
from pathlib import Path
import pandas as pd


class PublishOrPerishLoader:
    """Loads and processes CSV files exported from Publish or Perish."""

    # Standard column mapping for Publish or Perish exports
    STANDARD_COLUMNS = {
        "Cites": "citations",
        "Authors": "authors",
        "Title": "title",
        "Year": "year",
        "Source": "source",
        "Publisher": "publisher",
        "ArticleURL": "article_url",
        "CitesURL": "cites_url",
        "GSRank": "gs_rank",
    }

    def __init__(self, data_dir: Path):
        """Initialize with data directory path."""
        self.data_dir = Path(data_dir)

    def load_csv(self, filename: str, normalize_columns: bool = True) -> pd.DataFrame:
        """
        Load a Publish or Perish CSV file.

        Args:
            filename: Name of the CSV file to load
            normalize_columns: Whether to normalize column names to standard format

        Returns:
            DataFrame with the loaded data
        """
        file_path = self.data_dir / filename

        if not file_path.exists():
            raise FileNotFoundError(f"CSV file not found: {file_path}")

        # Load CSV with proper encoding (Publish or Perish may use different encodings)
        try:
            df = pd.read_csv(file_path, encoding="utf-8")
        except UnicodeDecodeError:
            # Try alternative encodings
            for encoding in ["latin-1", "cp1252", "iso-8859-1"]:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                raise ValueError(f"Could not decode CSV file: {file_path}")

        if normalize_columns:
            df = self._normalize_columns(df)

        # Clean and process the data
        df = self._clean_data(df)

        return df

    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize column names to standard format."""
        # Create a copy to avoid modifying original
        df_normalized = df.copy()

        # Rename columns according to mapping
        column_mapping = {}
        for col in df.columns:
            if col in self.STANDARD_COLUMNS:
                column_mapping[col] = self.STANDARD_COLUMNS[col]

        df_normalized = df_normalized.rename(columns=column_mapping)
        return df_normalized

    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and process the loaded data."""
        df_clean = df.copy()

        # Convert citations to numeric (handle cases where it might be string)
        if "citations" in df_clean.columns:
            df_clean["citations"] = pd.to_numeric(
                df_clean["citations"], errors="coerce"
            ).fillna(0)
        elif "Cites" in df_clean.columns:
            df_clean["Cites"] = pd.to_numeric(
                df_clean["Cites"], errors="coerce"
            ).fillna(0)

        # Convert year to numeric
        if "year" in df_clean.columns:
            df_clean["year"] = pd.to_numeric(df_clean["year"], errors="coerce")
        elif "Year" in df_clean.columns:
            df_clean["Year"] = pd.to_numeric(df_clean["Year"], errors="coerce")

        # Convert GS rank to numeric
        if "gs_rank" in df_clean.columns:
            df_clean["gs_rank"] = pd.to_numeric(df_clean["gs_rank"], errors="coerce")
        elif "GSRank" in df_clean.columns:
            df_clean["GSRank"] = pd.to_numeric(df_clean["GSRank"], errors="coerce")

        # Strip whitespace from string columns
        string_columns = df_clean.select_dtypes(include=["object"]).columns
        for col in string_columns:
            df_clean[col] = df_clean[col].astype(str).str.strip()

        # Remove rows where title is missing or empty
        title_col = "title" if "title" in df_clean.columns else "Title"
        if title_col in df_clean.columns:
            df_clean = df_clean[df_clean[title_col].notna()]
            df_clean = df_clean[df_clean[title_col] != ""]
            df_clean = df_clean[df_clean[title_col] != "nan"]

        return df_clean

    def get_basic_stats(self, df: pd.DataFrame) -> dict:
        """Get basic statistics about the loaded dataset."""
        stats = {
            "total_papers": len(df),
            "date_range": {},
            "citation_stats": {},
            "top_sources": {},
        }

        # Year statistics
        year_col = "year" if "year" in df.columns else "Year"
        if year_col in df.columns and not df[year_col].isna().all():
            valid_years = df[year_col].dropna()
            stats["date_range"] = {
                "min_year": int(valid_years.min()),
                "max_year": int(valid_years.max()),
                "year_distribution": valid_years.value_counts().sort_index().to_dict(),
            }

        # Citation statistics
        cites_col = "citations" if "citations" in df.columns else "Cites"
        if cites_col in df.columns:
            stats["citation_stats"] = {
                "total_citations": int(df[cites_col].sum()),
                "mean_citations": float(df[cites_col].mean()),
                "median_citations": float(df[cites_col].median()),
                "max_citations": int(df[cites_col].max()),
            }

        # Top sources
        source_col = "source" if "source" in df.columns else "Source"
        if source_col in df.columns:
            stats["top_sources"] = df[source_col].value_counts().head(10).to_dict()

        return stats
