"""Test PDF downloader functionality."""

from pathlib import Path
import tempfile

from papervisor.pdf_downloader import PDFDownloader
from papervisor.web.models.download_models import (
    DownloadStatus,
    PaperDownloadResult,
)


def test_pdf_downloader_initialization() -> None:
    """Test PDF downloader initialization."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir()

        downloader = PDFDownloader(project_path)

        # Check that directories are created
        assert (project_path / "pdfs" / "automatic").exists()
        assert (project_path / "pdfs" / "manual").exists()
        # Updated to match code: reports is under automatic
        assert (project_path / "pdfs" / "automatic" / "reports").exists()

        # Ensure downloader is initialized properly
        assert downloader.project_path == project_path


# def test_filename_generation() -> None:
#     """Test PDF filename generation."""
#     # TODO: Update test to use current DownloadService API
#     # The _generate_filename method has been integrated into the download logic
#     pass


# def test_download_urls_generation() -> None:
#     """Test download URL generation."""
#     # TODO: Update test to use current DownloadService.resolve_pdf_url API
#     # The _get_download_urls method has been integrated into resolve_pdf_url
#     pass


# def test_arxiv_id_extraction() -> None:
#     """Test arXiv ID extraction."""
#     # TODO: Update test to use current DownloadService.resolve_pdf_url API
#     # The arXiv ID extraction logic has been integrated into resolve_pdf_url
#     pass


def test_download_result_serialization() -> None:
    """Test download result serialization."""
    result = PaperDownloadResult(
        paper_id="123",
        title="Test Paper",
        status=DownloadStatus.SUCCESS,
        file_path=Path("/test/path.pdf"),
        download_source="test_source",
        file_size=1024,
    )

    result_dict = result.to_dict()

    assert result_dict["paper_id"] == "123"
    assert result_dict["title"] == "Test Paper"
    assert result_dict["status"] == DownloadStatus.SUCCESS
    assert result_dict["file_path"] == "/test/path.pdf"
    assert result_dict["download_source"] == "test_source"
    assert result_dict["file_size"] == 1024
    assert "timestamp" in result_dict


if __name__ == "__main__":
    # Run basic tests
    test_pdf_downloader_initialization()
    # test_filename_generation()  # TODO: Update for new API
    # test_download_urls_generation()  # TODO: Update for new API
    # test_arxiv_id_extraction()  # TODO: Update for new API
    test_download_result_serialization()
    print("Available PDF downloader tests passed!")
