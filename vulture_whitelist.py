# vulture_whitelist.py
# This file is used to whitelist symbols that vulture incorrectly marks as unused.
# Each symbol below is referenced dynamically (e.g., in tests, templates, or via serialization),
# or is required for compatibility, and should not be removed.


# --- src/papervisor/core.py ---
def search_papers():
    pass  # Used in integration tests


# --- src/papervisor/project_manager.py ---
# Used in tests/unit/test_project_manager.py and/or templates, not directly referenced in main code.
def load_project_index():
    pass  # Used in tests and dynamic loading


def load_project_metadata():
    pass  # Used in tests and dynamic loading


class ProjectManager:
    def __init__(self):
        pass

    def get_project(self):
        pass  # Used in tests and templates

    def list_projects(self):
        pass  # Used in tests and templates


total_queries = 0  # Used in tests, templates, and YAML data files
tags = []  # Used in tests, templates, and YAML data files


def created_datetime():
    pass  # Used in tests


def get_projects_by_status(status):
    pass  # Used in tests


def get_projects_by_researcher(researcher):
    pass  # Used in tests


def get_project_analysis_directory(project_id):
    pass  # Used in tests


# --- src/papervisor/search_query.py ---
extractor_version = ""  # Used in YAML/data serialization
filters = {}  # Used in YAML/data serialization
_queries = []  # Private attribute, used internally in SearchQueryManager


# Used in YAML data files and dynamic loading.
class SearchQuery:
    def __init__(self):
        pass

    def from_yaml(self):
        pass  # Used in YAML loading


SearchQuery.from_yaml


# --- src/papervisor/web_server.py ---
current_paper = ""  # Used in Flask context and dynamic assignment
start_time = 0.0  # Used in Flask context and dynamic assignment
secret_key = ""  # Used for Flask app session management


def index():
    pass  # Flask endpoint, used in templates and redirects


def landing_page():
    pass  # Flask endpoint, used in templates and redirects


def consolidate_project():
    pass  # Flask endpoint, used in templates and redirects


def project_dashboard(project_id):
    pass  # Flask endpoint, used in templates and redirects


def review_papers_legacy():
    pass  # Flask endpoint, used in templates and redirects


def download_management_legacy():
    pass  # Flask endpoint, used in templates and redirects


def review_papers():
    pass  # Flask endpoint, used in templates and redirects


def render_landing_page():
    pass  # Used in templates and web tests


def download_management():
    pass  # Flask endpoint, used in templates and redirects


def submit_url():
    pass  # Flask endpoint, used in templates and redirects


def download_all_missing():
    pass  # Flask endpoint, used in templates and redirects


def api_paper_details():
    pass  # Flask endpoint, used in templates and redirects


def mark_duplicates():
    pass  # Flask endpoint, used in templates and redirects


def serve_pdf():
    pass  # Flask endpoint, used in templates and redirects


def text_extraction():
    pass  # Flask endpoint, used in templates and redirects


def start_text_extraction():
    pass  # Flask endpoint, used in templates and redirects


def extract_single_paper():
    pass  # Flask endpoint, used in templates and redirects


def retry_all_text_extraction():
    pass  # Flask endpoint, used in templates and redirects


def serve_extracted_text():
    pass  # Flask endpoint, used in templates and redirects


def save_screening_actions():
    pass  # Flask endpoint, used in templates and redirects


def retry_failed_downloads():
    pass  # Flask endpoint, used in templates and redirects


def api_download_progress():
    pass  # Flask endpoint, used in templates and redirects


def cancel_download():
    pass  # Flask endpoint, used in templates and redirects


def upload_pdf_legacy():
    pass  # Flask endpoint, used in templates and redirects


def project_upload_pdf():
    pass  # Flask endpoint, used in templates and redirects


def screening():
    pass  # Flask endpoint, used in templates and redirects


def start_screening():
    pass  # Flask endpoint, used in templates and redirects


def screening_legacy():
    pass  # Flask endpoint, used in templates and redirects


def stop_download():
    pass  # Used as a method in the class, referenced in code


def _get_downloaded_files():
    pass  # Used as a method in the class, referenced in code


def _detect_sections():
    pass  # Used as a method in the class, referenced in code


section_key = ""  # Used as a loop variable in code


def create_app():
    pass  # Imported and used in tests


# --- vulture whitelist references ---
search_papers
load_project_index
load_project_metadata
ProjectManager.get_project
ProjectManager.list_projects
total_queries
tags
created_datetime
get_projects_by_status
get_projects_by_researcher
get_project_analysis_directory
extractor_version
filters
_queries
SearchQuery
render_landing_page
current_paper
start_time
secret_key
index
landing_page
consolidate_project
project_dashboard
review_papers_legacy
download_management_legacy
review_papers
download_management
submit_url
download_all_missing
api_paper_details
mark_duplicates
serve_pdf
text_extraction
start_text_extraction
extract_single_paper
retry_all_text_extraction
serve_extracted_text
save_screening_actions
retry_failed_downloads
api_download_progress
cancel_download
upload_pdf_legacy
project_upload_pdf
screening
start_screening
screening_legacy
stop_download
_get_downloaded_files
_detect_sections
section_key
create_app
