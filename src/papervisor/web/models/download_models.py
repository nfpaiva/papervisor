"""Data models for PDF download operations."""

from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict, Any
from pathlib import Path
from datetime import datetime


class DownloadStatus(Enum):
    """Enumeration of possible download statuses for papers."""

    SUCCESS = "success"
    FAILED = "failed"
    ALREADY_EXISTED = "already_existed"
    MANUAL_REQUIRED = "manual_required"
    # Add other statuses as needed


@dataclass
class PaperDownloadResult:
    """Result object for paper download operations."""

    paper_id: str
    status: DownloadStatus
    title: Optional[str] = None
    file_path: Optional[Path] = None
    download_source: Optional[str] = None
    file_size: Optional[int] = None
    error: Optional[str] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self) -> None:
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "paper_id": self.paper_id,
            "status": self.status,
            "title": self.title,
            "file_path": str(self.file_path) if self.file_path else None,
            "download_source": self.download_source,
            "file_size": self.file_size,
            "error": self.error,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
