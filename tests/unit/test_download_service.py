from papervisor.web.services.download_service import DownloadService


class DummyPapervisor:
    def get_project(self, project_id):
        return None


def test_resolve_pdf_url_unpaywall(monkeypatch):
    # Simulate Unpaywall OA PDF
    service = DownloadService(DummyPapervisor(), ".")
    paper = {"DOI": "10.1038/s41586-020-2649-2"}

    def fake_get(url, timeout=10):
        class R:
            status_code = 200

            def json(self):
                return {
                    "best_oa_location": {"url_for_pdf": "https://example.com/test.pdf"}
                }

        return R()

    monkeypatch.setattr("requests.get", fake_get)
    url = service.resolve_pdf_url(paper)
    assert url == "https://example.com/test.pdf"


def test_resolve_pdf_url_openalex(monkeypatch):
    service = DownloadService(DummyPapervisor(), ".")
    paper = {"DOI": "10.1038/s41586-020-2649-2"}

    def fake_get(url, timeout=10):
        class R:
            status_code = 200

            def json(self):
                return {
                    "primary_location": {"pdf_url": "https://openalex.org/test.pdf"},
                    "alternate_locations": [],
                }

        return R()

    monkeypatch.setattr("requests.get", fake_get)
    url = service.resolve_pdf_url(paper)
    assert url == "https://openalex.org/test.pdf"


def test_resolve_pdf_url_semanticscholar(monkeypatch):
    service = DownloadService(DummyPapervisor(), ".")
    paper = {"DOI": "10.1038/s41586-020-2649-2"}

    def fake_get(url, timeout=10):
        class R:
            status_code = 200

            def json(self):
                return {
                    "openAccessPdf": {"url": "https://semanticscholar.org/test.pdf"}
                }

        return R()

    monkeypatch.setattr("requests.get", fake_get)
    url = service.resolve_pdf_url(paper)
    assert url == "https://semanticscholar.org/test.pdf"


def test_resolve_pdf_url_springer():
    service = DownloadService(DummyPapervisor(), ".")
    paper = {
        "article_url": "https://link.springer.com/article/10.1007/s00134-020-06294-x"
    }
    url = service.resolve_pdf_url(paper)
    assert url.endswith("/content/pdf/10.1007/s00134-020-06294-x.pdf")


def test_resolve_pdf_url_sciencedirect():
    service = DownloadService(DummyPapervisor(), ".")
    paper = {
        "article_url": "https://www.sciencedirect.com/science/article/pii/S0167739X20320997"
    }
    url = service.resolve_pdf_url(paper)
    assert url.startswith(
        "https://www.sciencedirect.com/science/article/pii/S0167739X20320997/pdfft"
    )


def test_resolve_pdf_url_ieee():
    service = DownloadService(DummyPapervisor(), ".")
    paper = {"article_url": "https://ieeexplore.ieee.org/document/1234567/"}
    url = service.resolve_pdf_url(paper)
    assert url.startswith(
        "https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=1234567"
    )


def test_resolve_pdf_url_fallback():
    service = DownloadService(DummyPapervisor(), ".")
    paper = {"FullTextURL": "https://fallback.org/test.pdf"}
    url = service.resolve_pdf_url(paper)
    assert url == "https://fallback.org/test.pdf"
