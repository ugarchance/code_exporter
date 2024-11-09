from enum import Enum, auto
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Dict

class GitFileStatus(Enum):
    """Git dosya durumları."""
    UNMODIFIED = auto()
    MODIFIED = auto()
    ADDED = auto()
    DELETED = auto()
    RENAMED = auto()
    COPIED = auto()
    UNTRACKED = auto()

@dataclass
class GitDiff:
    """Git diff sonucu."""
    file_path: Path
    content: str
    status: GitFileStatus
    
@dataclass
class GitConfig:
    """Git yapılandırması."""
    enabled: bool = True
    cache_timeout: int = 300
    max_diff_size: int = 1024 * 1024
    auto_scan: bool = True
    excluded_branches: list = None
    diff_context_lines: int = 3
    
    def __post_init__(self):
        if self.excluded_branches is None:
            self.excluded_branches = ['gh-pages', 'release'] 