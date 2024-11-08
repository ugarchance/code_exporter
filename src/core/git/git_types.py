from enum import Enum, auto
from typing import TypedDict, List, Optional
from pathlib import Path

class GitFileStatus(Enum):
    UNMODIFIED = auto()
    MODIFIED = auto()
    ADDED = auto()
    DELETED = auto()
    RENAMED = auto()
    COPIED = auto()
    UNTRACKED = auto()

class GitDiff(TypedDict):
    file_path: Path
    old_content: str
    new_content: str
    changes: List['GitChange']

class GitChange(TypedDict):
    line_number: int
    type: str  # 'added', 'deleted', 'modified'
    content: str