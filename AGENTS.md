# Agentic Coding Guidelines

This document provides instructions and guidelines for AI agents working on this codebase.

## Project Overview

This repository contains a collection of Python utilities for processing Android screenshots, converting images to SVG/PDF, and optimizing SVG files. The tools rely on ADB (Android Debug Bridge) for device interaction and various Python libraries for image and vector processing.

## Build, Lint, and Test Commands

There is no formal build system or test suite. Scripts are executed directly.

### dependencies

Ensure the following system dependencies are installed:
- `python3`
- `adb` (Android Debug Bridge)
- `fontforge` (e.g., `sudo apt install fontforge python3-fontforge`)

Install Python dependencies manually using `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Running Scripts

Scripts are standalone and executable.

**Example: Taking screenshots**
```bash
python screenshot.py output_dir
```

**Example: Converting PNG to SVG**
```bash
python png2svg.py input_dir
```

**Example: Deduplicating SVG paths**
```bash
python deduplicate.py input_dir output_dir
```

### Testing

There are currently no unit tests.
- **Manual Testing**: Verify changes by running the modified script against a sample set of images/files.
- **New Tests**: If adding significant logic, create a companion test file (e.g., `test_deduplicate.py`) using `unittest`.

**Running a single test (if created):**
```bash
python -m unittest test_filename.TestClassName.test_method_name
```

### Linting

No formal linter is configured. Agents should ensure code is syntactically correct and follows PEP 8.
- **Recommendation**: Use `pylint` or `flake8` locally if available to catch errors before finalizing changes.

## Code Style Guidelines

Follow established patterns in the codebase.

### General Formatting
- **Indentation**: Use **4 spaces**. Do not use tabs.
- **Line Length**: Keep lines under 100 characters where possible, but clarity is prioritized over strict limits.
- **Shebang**: Include `#!/usr/bin/env python` at the top of executable scripts.

### Naming Conventions
- **Variables & Functions**: `snake_case` (e.g., `process_image`, `svg_file`).
- **Classes**: `CamelCase` (e.g., `ImageProcessor`).
- **Constants**: `UPPER_CASE` (e.g., `SVG_NAMESPACE`, `DEFAULT_CROP`).
- **Files**: `snake_case.py` (e.g., `png2svg.py`).

### Imports
Group imports in the following order:
1.  **Standard Library** (`os`, `sys`, `argparse`, `subprocess`)
2.  **Third-Party Libraries** (`PIL`, `reportlab`, `vtracer`)
3.  **Local Modules** (`from deduplicate import ...`)

**Example:**
```python
import os
import argparse
from PIL import Image
import vtracer
from deduplicate import deduplicate_svg
```

### Type Hinting
- The codebase uses minimal type hinting.
- **New Code**: Add type hints for complex functions or where ambiguity exists, but do not aggressively refactor existing code to add them unless requested.
- **Example**: `def create_svg(width: int, height: int, paths: dict):`

### Documentation
- **Docstrings**: Use triple double-quotes `"""` for function and class docstrings.
- **Content**: Briefly explain the purpose of the function and its arguments.

**Example:**
```python
def crop_and_convert(directory, crop_top):
    """
    Crops images in the directory and converts them to SVG.
    
    :param directory: Path to image directory
    :param crop_top: Pixels to crop from top
    """
```

### Error Handling
- Use `try...except` blocks for operations that interact with the filesystem, external processes (ADB), or image parsing.
- Print descriptive error messages to stdout/stderr.
- Avoid bare `except:` clauses; catch specific exceptions (`IOError`, `subprocess.CalledProcessError`) when possible, or `Exception` if a catch-all is needed for top-level loops.

**Example:**
```python
try:
    with Image.open(file_path) as img:
        # process image
        pass
except IOError as e:
    print(f"Failed to open image {file_path}: {e}")
```

### CLI Arguments
- Use `argparse` for handling command-line arguments.
- Provide `help` strings for all arguments.
- Set reasonable `default` values where appropriate.

**Example:**
```python
parser = argparse.ArgumentParser(description="Process images.")
parser.add_argument("input_dir", help="Input directory")
parser.add_argument("--crop", type=int, default=0, help="Pixels to crop")
args = parser.parse_args()
```

### File Operations
- Use `os.path.join` for path manipulation to ensure cross-platform compatibility (though Linux is the primary environment).
- Ensure output directories exist using `os.makedirs(path, exist_ok=True)`.

### Local Dependencies
- When importing local files, ensure circular dependencies are avoided.
- Local modules often assume they are run from the project root.

## Specific Tooling Notes

### ADB Wrapper
When writing code that interacts with ADB, use the `@adb_wrapper` decorator (found in `screenshot.py`) or implement similar error handling to manage device connection issues gracefully.

### SVG Processing
- Use `xml.etree.ElementTree` for XML/SVG manipulation.
- Register namespaces before parsing:
  ```python
  ET.register_namespace("", "http://www.w3.org/2000/svg")
  ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")
  ```

## Repository Structure
- `*.py`: Main utility scripts.
- `*.sh`: Shell helper scripts.
- `requirements.txt`: List of Python dependencies.
