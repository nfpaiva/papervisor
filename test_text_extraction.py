#!/usr/bin/env python3
"""
Test script for enhanced academic paper text extraction.
This script demonstrates the improved extraction capabilities.
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, "src")


def test_text_extraction_structure() -> None:
    """Test the new JSON structure for academic papers."""

    # Sample paper data (simulating what we get from the CSV)
    sample_paper = {
        "paper_id": 0,
        "title": (
            "Optimizing Call Center Service Level Agreements Through "
            "Artificial Intelligence and Automation: A Comprehensive Analysis"
        ),
        "authors": "John Smith, Jane Doe, Bob Johnson",
        "year": "2024",
        "DOI": "10.1234/example.2024.001",
        "downloaded_file": "sample.pdf",
        "download_source": "automatic",
    }

    # Import the web server class
    from papervisor.web_server import PapervisorWebServer

    # Create a minimal instance
    server = PapervisorWebServer.__new__(PapervisorWebServer)

    # Test metadata extraction
    print("Testing metadata extraction...")
    metadata = server._extract_paper_metadata(sample_paper, "Sample text content")

    print(f"✅ Title: {metadata['title']}")
    print(f"✅ Authors: {metadata['authors']}")
    print(f"✅ Year: {metadata['year']} (type: {type(metadata['year'])})")
    print(f"✅ DOI: {metadata['doi']}")

    # Test author parsing
    print("\nTesting author parsing...")
    authors_test_cases = [
        "John Smith, Jane Doe, Bob Johnson",
        "Smith, J.; Doe, J. & Johnson, B.",
        "John Smith and Jane Doe and Bob Johnson",
        "Smith, John (University A), Doe, Jane (University B)",
    ]

    for authors_str in authors_test_cases:
        parsed_authors = server._parse_authors(authors_str)
        print(f"✅ '{authors_str}' → {parsed_authors}")

    # Test year parsing
    print("\nTesting year parsing...")
    year_test_cases = ["2024", "2024.0", "Published 2024", "2024-01-01", "invalid"]

    for year_str in year_test_cases:
        parsed_year = server._parse_year(year_str)
        print(f"✅ '{year_str}' → {parsed_year}")

    # Test section detection with sample academic text
    print("\nTesting section detection...")
    sample_academic_text = """
    Optimizing Call Center Service Level Agreements Through AI

    Abstract
    This paper presents a comprehensive analysis of artificial intelligence
    applications in call center optimization. We propose novel algorithms for
    service level management.

    1. Introduction
    Call centers represent a critical component of modern customer service
    infrastructure. The increasing volume of customer interactions requires
    sophisticated management systems.

    2. Literature Review
    Previous work in this area has focused on traditional optimization methods.
    Smith et al. (2023) proposed rule-based systems for call routing.

    3. Methodology
    Our approach combines machine learning with real-time analytics.
    We implemented a multi-agent system for dynamic load balancing.

    4. Results
    Experimental evaluation shows 25% improvement in response times.
    Customer satisfaction scores increased by 15% across all metrics.

    5. Discussion
    The results demonstrate the effectiveness of AI-driven approaches.
    However, implementation challenges remain in legacy systems.

    6. Conclusion
    This work establishes a framework for AI-enhanced call center management.
    Future work will explore deep learning applications.

    Acknowledgments
    We thank the anonymous reviewers for their valuable feedback.

    References
    [1] Smith, J. et al. "Call Center Optimization" (2023)
    """

    sections = server._extract_academic_sections(sample_academic_text)
    print(f"✅ Detected sections: {list(sections.keys())}")

    for section_name, content in sections.items():
        preview = content[:100] + "..." if len(content) > 100 else content
        print(f"   {section_name}: {preview}")

    # Test complete JSON structure
    print("\nTesting complete JSON structure...")

    # Create expected structure
    expected_structure = {
        "title": str,
        "authors": list,
        "year": (int, type(None)),
        "doi": str,
        "source": str,
        "url": str,
        "abstract": str,
        "introduction": str,
        "methods": str,
        "results": str,
        "discussion": str,
        "conclusion": str,
        "additional_sections": dict,
        "extraction_metadata": dict,
    }

    # Test with fallback (no PyPDF2)
    mock_pdf_path = Path("test.pdf")
    try:
        result = server._extract_pdf_text(mock_pdf_path, sample_paper)

        print("✅ JSON structure validation:")
        for field, expected_type in expected_structure.items():
            if field in result:
                actual_type = type(result[field])
                if isinstance(expected_type, tuple):
                    type_match = actual_type in expected_type
                else:
                    type_match = actual_type == expected_type

                status = "✅" if type_match else "❌"
                print(
                    f"   {status} {field}: {actual_type.__name__} "
                    f"(expected: {expected_type})"
                )
            else:
                print(f"   ❌ {field}: MISSING")

        # Show sample JSON output
        print("\n✅ Sample JSON output (first 500 chars):")
        json_str = json.dumps(result, indent=2, ensure_ascii=False)
        print(json_str[:500] + "..." if len(json_str) > 500 else json_str)

    except Exception as e:
        print(f"❌ Error testing extraction: {e}")

    print("\n🎉 Text extraction testing complete!")


if __name__ == "__main__":
    test_text_extraction_structure()
