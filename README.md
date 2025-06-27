# Code Exporter

Code Exporter scans project folders and lets you export selected source files in a single text file. It ships with a PyQt6 based interface and integrates with Git.

## Features

- Multi-threaded directory scanning
- Configurable list of supported file extensions
- Optional content processors per extension
- Export groups by folder or as a single bundle
- Git change tracking

## Running

```bash
python -m code_exporter --dir /path/to/project
```

## Extension Manager

File types are managed through `ExtensionManager`. Both the scanner and exporter share this manager so you only register an extension once.

### Register a new extension

```python
from src.core.extension_manager import ExtensionManager

ext_mgr = ExtensionManager()
ext_mgr.register_extension('.css')  # basic support
```

Provide a processor if the content needs modification:

```python
def process_css(content: str) -> str:
    # custom cleanup logic
    return content

ext_mgr.register_extension('.css', process_css)
```

Use the same instance when creating the scanner and exporter:

```python
ext_mgr = ExtensionManager(['.py', '.css'])
scanner = FileScanner(extension_manager=ext_mgr)
exporter = FileExporter(extension_manager=ext_mgr)
```

You can also manage extensions through the settings dialog.

## Development

Run a simple syntax check for all modules:

```bash
python -m py_compile $(git ls-files '*.py')
```

