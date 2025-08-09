"""Test PDF downloader functionality."""

from pathlib import Path
import tempfile

from papervisor.pdf_downloader import PDFDownloader, DownloadStatus


def test_pdf_downloader_initialization() -> None:
    """Test PDF downloader initialization."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir()

        downloader = PDFDownloader(project_path)

        # Check that directories are created
        assert (project_path / "pdfs" / "automatic").exists()
        assert (project_path / "pdfs" / "manual").exists()
        assert (project_path / "pdfs" / "reports").exists()

        # Ensure downloader is initialized properly
        assert downloader.project_path == project_path


def test_filename_generation() -> None:
    """Test PDF filename generation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir()

        downloader = PDFDownloader(project_path)

        # Test normal case
        filename = downloader._generate_filename(
            "123", "Smith, John; Doe, Jane", "2023"
        )
        assert filename == "123_Smith_2023.pdf"

        # Test with messy author names
        filename = downloader._generate_filename("456", "Dr. Jane Doe-Smith", "2022")
        assert filename == "456_DoeSmith_2022.pdf"

        # Test with unknown values
        filename = downloader._generate_filename("789", "", "Unknown")
        assert filename == "789_Unknown_Unknown.pdf"


def test_download_urls_generation() -> None:
    """Test download URL generation."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir()

        downloader = PDFDownloader(project_path)

        # Test with DOI
        urls = downloader._get_download_urls("10.1000/test", "", "", "")
        assert any("https://doi.org/10.1000/test" in url for _, url in urls)

        # Test with arXiv URL
        urls = downloader._get_download_urls(
            "", "https://arxiv.org/abs/2301.12345", "", ""
        )
        arxiv_urls = [url for source, url in urls if "arxiv.org/pdf" in url]
        assert len(arxiv_urls) > 0
        assert "2301.12345.pdf" in arxiv_urls[0]


def test_arxiv_id_extraction() -> None:
    """Test arXiv ID extraction."""
    with tempfile.TemporaryDirectory() as temp_dir:
        project_path = Path(temp_dir) / "test_project"
        project_path.mkdir()

        downloader = PDFDownloader(project_path)

        # Test various arXiv URL formats
        arxiv_id = downloader._extract_arxiv_id("https://arxiv.org/abs/2301.12345", "")
        assert arxiv_id == "2301.12345"

        arxiv_id = downloader._extract_arxiv_id("", "arXiv:2301.12345")
        assert arxiv_id == "2301.12345"

        arxiv_id = downloader._extract_arxiv_id("no arxiv here", "")
        assert arxiv_id is None


def test_download_result_serialization() -> None:
    """Test download result serialization."""
    from papervisor.pdf_downloader import PaperDownloadResult

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
    test_filename_generation()
    test_download_urls_generation()
    test_arxiv_id_extraction()
    test_download_result_serialization()
    print("All PDF downloader tests passed!")
