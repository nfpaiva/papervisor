"""Papervisor: A modular pipeline for systematic literature reviews."""

__version__ = "0.1.0"

from .core import Papervisor
from .search_query import SearchQuery, SearchQueryManager
from .data_loader import PublishOrPerishLoader

__all__ = ["Papervisor", "SearchQuery", "SearchQueryManager", "PublishOrPerishLoader"]
