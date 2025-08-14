# Demo Contact Center AI Project

This is a comprehensive demonstration project for Papervisor, showcasing the complete workflow for conducting systematic literature reviews in the domain of AI applications in contact centers.

## Project Overview

**Project ID:** `demo_contact_center_ai`
**Title:** AI in Contact Centers - Demo Project
**Purpose:** Demonstration, testing, and onboarding for Papervisor users
**Domain:** Artificial Intelligence applications in Contact Center operations
**Status:** Demo project with realistic academic data

## Project Structure

```
demo_contact_center_ai/
├── README.md                    # This file - project documentation
├── search_queries.yaml          # Search configuration and metadata
├── results/                     # Search results in CSV format
│   ├── q1.csv                  # Real-time decision systems results
│   └── q2.csv                  # AI optimization results
├── pdfs/                       # PDF storage and processing
│   ├── README.md               # PDF directory documentation
│   ├── automatic/              # Automatically downloaded PDFs
│   ├── manual/                 # Manually uploaded PDFs
│   └── extracted_texts/        # Processed text content
├── analysis/                   # Analysis scripts and results
├── reports/                    # Generated reports and summaries
└── extraction_status.json     # Text extraction tracking (auto-generated)
```

## Search Queries

This demo project includes two carefully selected search queries from the broader contact center AI literature:

### Query 1: Real-Time Decision Systems in Contact Centers
- **Focus:** Machine learning and optimization for real-time operational decisions
- **Query String:** `"real-time decision making" AND ("machine learning" OR "optimization") AND ("call center" OR "contact center")`
- **Results:** 18 papers with realistic metadata and duplicates

### Query 2: Call Center Optimization with AI
- **Focus:** AI-based optimization approaches for contact center operations
- **Query String:** `("call center" OR "contact center") AND ("artificial intelligence" OR "machine learning" OR "AI") AND ("optimization" OR "decision support" OR "resource allocation")`
- **Results:** 17 papers including intentional duplicates for testing deduplication

## Demo Features

### 1. Realistic Academic Data
- **Authors:** Realistic academic author names and affiliations
- **Venues:** Mix of IEEE, ACM, Springer, and Elsevier publications
- **Years:** Range from 2015-2024 showing evolution of the field
- **DOIs:** Properly formatted DOI identifiers for academic papers
- **Abstracts:** Comprehensive abstracts reflecting actual research content

### 2. Duplicate Detection Testing
- **3-5 intentional duplicates** across both queries
- Demonstrates Papervisor's deduplication algorithms
- Includes variations in formatting and metadata completeness

### 3. Text Extraction Examples
Located in `pdfs/extracted_texts/`:
- **5 sample extractions** with full academic paper structure
- **Extraction metadata** including processing time, quality scores, warnings
- **Academic sections:** Introduction, Methodology, Results, Discussion, Conclusion
- **Mathematical content:** Equations, tables, figures metadata
- **Quality variations:** Examples of perfect and problematic extractions

### 4. Edge Case Handling
- Papers with **missing metadata** (testing robustness)
- **Special characters** in titles and author names
- **Very long titles** and extensive author lists
- **Mixed publication types** (journals, conferences, workshops)

## Sample Papers Included

### High-Quality Extractions
1. **Chen et al. (2023)** - Real-time AI decision making with comprehensive methodology
2. **Martinez et al. (2022)** - Systematic review with meta-analysis tables
3. **Zhang et al. (2021)** - Empirical study with detailed experimental setup

### Demonstration Scenarios
4. **Kumar et al. (2023)** - Deep reinforcement learning with some extraction warnings
5. **Brown et al. (2020)** - Comprehensive survey paper with extensive references

## Using This Demo Project

### For New Users (Onboarding)
1. **Explore** the project structure to understand Papervisor organization
2. **Review** search_queries.yaml to see how queries are configured
3. **Examine** CSV result files to understand metadata structure
4. **Read** extracted text samples to see processing outcomes
5. **Practice** with duplicate detection using known duplicates

### For Developers (Testing)
1. **End-to-End Testing:** Complete workflow from search to analysis
2. **Deduplication Testing:** Known duplicates for algorithm validation
3. **Edge Case Testing:** Unusual metadata formats and missing data
4. **Performance Testing:** Realistic dataset size for benchmarking
5. **Integration Testing:** Compatibility with all Papervisor modules

### For Demonstrations
1. **Quick Overview:** Show complete project in 5 minutes
2. **Detailed Walkthrough:** 30-minute comprehensive demonstration
3. **Interactive Features:** Let audience explore search results
4. **Success Stories:** Point to realistic performance improvements
5. **Problem Scenarios:** Demonstrate handling of extraction issues

## Key Demo Scenarios

### Scenario 1: Basic Literature Review Workflow
1. Start with search query configuration
2. Show simulated search results
3. Demonstrate paper review and screening
4. Explore text extraction and analysis
5. Generate summary reports

### Scenario 2: Duplicate Detection
1. Identify the 3-5 duplicate papers across queries
2. Show how deduplication algorithms work
3. Demonstrate metadata reconciliation
4. Show final consolidated results

### Scenario 3: Quality Assessment
1. Compare high-quality vs. problematic extractions
2. Show extraction metadata and quality scores
3. Demonstrate troubleshooting workflow
4. Show how to handle extraction warnings

### Scenario 4: Analysis and Reporting
1. Generate descriptive statistics from results
2. Create topic analysis and trends
3. Identify research gaps and opportunities
4. Export results for external analysis

## Technical Details

### Data Characteristics
- **Total Papers:** ~35 (18 + 17 with 3-5 duplicates)
- **Publication Span:** 2015-2024
- **Venues:** 15+ different academic venues
- **Missing Data:** ~15% of papers have incomplete metadata
- **Text Length:** Varies from 8-22 pages (realistic range)

### File Formats
- **Search Results:** CSV with standardized academic metadata
- **Text Extractions:** Plain text with markdown formatting
- **Configuration:** YAML for human readability
- **Status Tracking:** JSON for automated processing

### Quality Assurance
- All CSV files validate against Papervisor schema
- Extraction examples include realistic processing metadata
- Duplicate papers have sufficient similarity for detection
- Edge cases test system robustness

## Demo Success Metrics

After using this demo project, users should be able to:
- [ ] Understand Papervisor project structure and organization
- [ ] Configure search queries for their research domain
- [ ] Interpret search results and metadata formats
- [ ] Use duplicate detection and paper screening features
- [ ] Understand text extraction process and quality assessment
- [ ] Generate analysis reports and export results
- [ ] Complete a full literature review workflow in under 30 minutes

## Maintenance and Updates

### Regenerating Demo Data
To update or regenerate this demo project:
1. Modify search_queries.yaml for different research focus
2. Update CSV files with current academic papers
3. Refresh extracted text examples with recent publications
4. Ensure duplicate papers remain detectable
5. Update this README with any structural changes

### Version Information
- **Created:** January 15, 2025
- **Demo Version:** 1.0
- **Compatible with:** Papervisor v2.0+
- **Last Updated:** January 15, 2025

## Related Documentation

- [Papervisor User Guide](../../README.md)
- [Search Query Configuration](../../../docs/search_queries.md)
- [Text Extraction Guide](../../../docs/text_extraction.md)
- [Duplicate Detection](../../../docs/deduplication.md)
- [Analysis and Reporting](../../../docs/analysis.md)

## Support and Feedback

This demo project is designed to showcase Papervisor capabilities and support user onboarding. For questions, suggestions, or issues:

- **GitHub Issues:** Report bugs or request enhancements
- **Documentation:** Comprehensive guides available in `/docs`
- **Community:** Join discussions and share experiences
- **Contact:** Reach out to the development team

---

**Note:** This is a demonstration project with simulated data. For actual literature reviews, create a new project following the same structure with your specific research domain and search queries.
