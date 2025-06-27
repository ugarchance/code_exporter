from pathlib import Path
from typing import Callable, Dict, Optional, Iterable

class ExtensionManager:
    """Manage file extensions and their optional content processors."""

    def __init__(self, supported_extensions: Optional[Iterable[str]] = None):
        self._processors: Dict[str, Optional[Callable[[str], str]]] = {}
        if supported_extensions:
            for ext in supported_extensions:
                self.register_extension(ext)

        # Register default processors
        self.register_extension('.java', self._process_java_content)

    def register_extension(self, extension: str, processor: Optional[Callable[[str], str]] = None) -> None:
        self._processors[extension.lower()] = processor

    def supported_extensions(self) -> set:
        return set(self._processors.keys())

    def is_supported(self, extension: str) -> bool:
        return extension.lower() in self._processors

    def process_content(self, file_path: Path, content: str) -> str:
        processor = self._processors.get(file_path.suffix.lower())
        if processor:
            return processor(content)
        return content

    @staticmethod
    def _process_java_content(content: str) -> str:
        lines = content.splitlines()
        filtered = [
            line for line in lines
            if not line.strip().startswith(('import ', 'package '))
        ]
        return "\n".join(filtered)
