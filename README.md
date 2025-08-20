# papervisor
Papervisor is a modular, open-source pipeline for accelerating systematic literature reviews. It combines automation, NLP, and human-in-the-loop screening to help researchers move from raw academic search results to a curated, thematically structured review — fast and reproducibly.

**Tags:**
`literature-review` `systematic-review` `research` `open-source` `automation` `NLP` `PDF` `academic` `workflow` `bibliometrics` `data-extraction` `python` `web-dashboard`

## 🚀 Main Features (Step-by-Step, User-Guided)
Papervisor is designed as a stepwise, user-in-the-loop workflow. At each stage, you control, review, and refine the results before moving to the next step:

- 📁 **Multiple Project Management**: Create and manage multiple literature research projects, each with its own data and workflow.
- 🌐 **Web Dashboard for Search Results**: Import and view CSV search results (e.g., from Publish or Perish/Google Scholar) in a friendly web interface.
- 🔄 **Deduplication Across Queries**: Automatically detect and suggest deduplication of documents from different search queries, with user review and override.
- 📥 **PDF Download Automation**: Download PDFs for your references automatically, with options to manually add links or upload files for failed downloads.
- 📝 **Text Extraction & Metrics**: Extract text from PDFs, calculate extraction metrics, display extracted chapters, and select papers for the next step—all with user review.
- 🤖 **(Upcoming) LLM-Powered PDF Filtering**: This step will leverage large language models (LLMs) to analyze extracted PDF abstracts and flag candidates to keep or exclude from the literature review, providing an explanation for each outcome.

Each step is transparent and user-driven, so you always know what’s happening and can intervene as needed.

## 🛠️ Installation

Papervisor requires Python 3.12+ and pip. To get started:

```bash
# Clone the repository
git clone https://github.com/yourusername/papervisor.git
cd papervisor

# Install core dependencies
pip install .

# (Recommended) Install development tools and extras
pip install .[dev]
```

- For best results, use a virtual environment (e.g., `python -m venv .venv && source .venv/bin/activate`).
- See the [CI/CD section](#continuous-integration--code-quality) for details on running tests and code quality checks.

### 🚦 Launch the Web Server

After installing, you can launch the Papervisor web server with:

```bash
./launch_server_simple.sh
```

This script checks your Python version and starts the web dashboard. By default, the server will be available at:
- http://127.0.0.1:5000 (local only)
- http://0.0.0.0:5000 (network, if allowed by your firewall)

## 🧑‍💻 Quick Start User Guide

Follow these steps to get started with Papervisor:

1. **Define your search queries**: Use Publish or Perish (or another academic database) to create and execute your literature search queries.
2. **Export results as CSV**: Save the search results as CSV files from your chosen tool.
3. **Create a new literature review project**: In your Papervisor data directory, create a new folder for your project (see documentation for structure).
4. **Import CSV files**: Place your exported CSV files into the designated folder for your new project.
5. **Launch the server**: Run `./launch_server_simple.sh` and open the web dashboard. On the landing page, confirm that your project and search queries are listed.
6. **Continue in the UI**: After these steps, you can use the Papervisor workflow through the web UI to:
   - Review and deduplicate search results
   - Download and manage PDFs
   - Extract text and metrics from PDFs
   - (Soon) Use LLM-powered screening for abstracts
   - Track progress and manage your literature review pipeline

*Note: The initial project and CSV import steps are currently manual, but all subsequent workflow steps are managed through the Papervisor web interface.*

---

> 💡 **Want to contribute?**
>
> See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to participate, the contribution workflow, and our CI/code quality process.

---

## 📊 Feature Comparison: Papervisor vs. Other Tools

Papervisor fills a unique space in the literature review ecosystem by combining open-source transparency, automation, and user-in-the-loop control. Here’s how it compares to other tools:

| Feature / Tool                | Papervisor (OSS) | Publish or Perish (OSS) | Rayyan (Proprietary) | Covidence (Proprietary) | ResearchRabbit (Proprietary) |
|-------------------------------|:----------------:|:----------------------:|:--------------------:|:-----------------------:|:----------------------------:|
| Multi-project management      |       ✅         |           ❌           |         ✅           |           ✅            |             ✅               |
| Web dashboard                 |       ✅         |           ❌           |         ✅           |           ✅            |             ✅               |
| Import CSV search results     |       ✅         |           ✅           |         ✅           |           ✅            |             ✅               |
| Deduplication (auto/suggest)  |       ✅         |           ❌           |         ✅           |           ✅            |             ❌               |
| PDF download automation       |       ✅         |           ❌           |         ❌           |           ❌            |             ❌               |
| Manual PDF upload/fix         |       ✅         |           ❌           |         ✅           |           ✅            |             ❌               |
| Text extraction from PDFs     |       ✅         |           ❌           |         ❌           |           ❌            |             ❌               |
| Extraction metrics            |       ✅         |           ❌           |         ❌           |           ❌            |             ❌               |
| LLM-powered screening         |   (WIP) 🤖       |           ❌           |         ❌           |           ❌            |             ❌               |
| Bibliometric analytics        |   (Planned) 📊   |           ✅           |         ❌           |           ❌            |             ✅               |
| User-in-the-loop workflow     |       ✅         |           ❌           |         ✅           |           ✅            |             ❌               |
| Open source                   |       ✅         |           ✅           |         ❌           |           ❌            |             ❌               |
| Free to use                   |       ✅         |           ✅           |         ❌           |           ❌            |             ❌               |

*Want to see more features compared? Suggest or track additional features (e.g., advanced analytics, integrations, export formats) by opening an issue or PR!*

**Why Papervisor?**
- 🛠️  100% open source and extensible: no vendor lock-in, full transparency.
- 🧑‍💻  Designed for researchers who want automation but also full control at every step.
- 🔄  Handles the full pipeline: from search result import, deduplication, PDF download, extraction, and (soon) LLM-powered screening.
- 💸  Free to use, with no paywalls or data lock-in.
- 🧩  Easily integrates with other tools and workflows.

Papervisor is ideal for researchers, labs, and teams who want a transparent, customizable, and automated literature review pipeline—without sacrificing control or paying for proprietary platforms.
