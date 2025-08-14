"""Unit tests for data loader functionality."""

from pathlib import Path
import tempfile
import pandas as pd

from papervisor.data_loader import PublishOrPerishLoader


def test_publish_or_perish_loader_with_demo_project() -> None:
    """Test PublishOrPerishLoader with the demo project."""
    # Use the main data directory which contains the demo project
    main_data_dir = Path(__file__).parent.parent.parent / "data"

    # Test loading demo project data
    project_path = main_data_dir / "literature_reviews" / "demo_contact_center_ai"
    results_path = project_path / "results"

    if not results_path.exists():
        print("⚠️  Demo project results not found, skipping test")
        return

    # Test loading query results file
    q1_file = results_path / "q1.csv"
    if q1_file.exists():
        loader = PublishOrPerishLoader(main_data_dir)
        df = loader.load_csv(str(q1_file))

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

        # Should have expected columns after normalization
        expected_columns = ["title", "authors", "year", "citations"]
        for col in expected_columns:
            assert col in df.columns, f"Missing column: {col}"


def test_publish_or_perish_loader_column_mapping() -> None:
    """Test column mapping functionality."""
    with tempfile.TemporaryDirectory() as temp_dir:
        loader = PublishOrPerishLoader(Path(temp_dir))

        # Test that column mapping exists
        assert hasattr(loader, "STANDARD_COLUMNS")
        assert "Cites" in loader.STANDARD_COLUMNS
        assert loader.STANDARD_COLUMNS["Cites"] == "citations"
        assert loader.STANDARD_COLUMNS["Authors"] == "authors"


def test_publish_or_perish_loader_initialization() -> None:
    """Test PublishOrPerishLoader initialization."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Should initialize without error
        loader = PublishOrPerishLoader(Path(temp_dir))
        assert loader.STANDARD_COLUMNS is not None
        assert loader.data_dir == Path(temp_dir)


def test_publish_or_perish_loader_with_empty_file() -> None:
    """Test loader with empty or missing file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_file = Path(temp_dir) / "empty.csv"
        temp_file.write_text("Title,Authors,Year,Cites\n")  # Header only

        loader = PublishOrPerishLoader(Path(temp_dir))
        df = loader.load_csv(str(temp_file))

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0  # Should be empty but valid DataFrame


if __name__ == "__main__":
    test_publish_or_perish_loader_with_demo_project()
    test_publish_or_perish_loader_column_mapping()
    test_publish_or_perish_loader_initialization()
    test_publish_or_perish_loader_with_empty_file()
    print("All data loader unit tests passed!")


if __name__ == "__main__":
    test_publish_or_perish_loader_with_demo_project()
    test_publish_or_perish_loader_column_mapping()
    test_publish_or_perish_loader_initialization()
    test_publish_or_perish_loader_with_empty_file()
    print("All data loader unit tests passed!")
