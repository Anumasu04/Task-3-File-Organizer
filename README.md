# Automated File Organizer & Cleanup Utility

[![Python 3.x](https://img.shields.io/badge/Python-3.x-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Standard Library](https://img.shields.io/badge/Dependencies-Standard%20Library-green.svg)](requirements.txt)

A safe, beginner-friendly desktop automation utility built in Python to organize cluttered directories (such as Downloads, Desktop, or Project folders) into clean, categorized subfolders based on file extensions.

Developed for **Python Programming Internship – Task 3**.

---

## Table of Contents
- [Project Introduction](#project-introduction)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Project Structure](#project-structure)
- [Installation Instructions](#installation-instructions)
- [How to Run](#how-to-run)
  - [Interactive Mode](#1-interactive-mode-recommended)
  - [Command-Line Mode](#2-command-line-mode)
  - [Dry-Run Mode](#3-dry-run-preview-mode)
- [File Extension Mapping](#file-extension-mapping)
- [Safety Features](#safety-features)
- [Logging & Audit Trail](#logging--audit-trail)
- [Example Execution](#example-execution)
- [Testing & Verification](#testing--verification)

---

## Project Introduction

Cluttered directories (like default Downloads folders) often accumulate hundreds of disorganized files: documents, images, installers, zip archives, and scripts. Manually sorting these files is tedious and prone to errors.

The **Automated File Organizer & Cleanup Utility** scans any user-specified directory, categorizes files by extension, creates destination category subfolders on demand, and safely relocates files with collision protection.

It operates strictly on user confirmation, provides a dry-run preview mode, and never deletes or overwrites existing files.

---

## Features

- **Extension-Based Categorization**: Automatically groups files into 6 predefined categories: `Documents`, `Images`, `Videos`, `Archives`, `Code`, and `Other`.
- **Compound Extension Support**: Correctly handles multi-part extensions like `.tar.gz` and `.tar.bz2`.
- **Case-Insensitive Matching**: Matches extensions regardless of case (e.g., `.PDF`, `.Jpg`, `.PNG`).
- **Duplicate Name Protection**: Automatically detects existing files and renames colliding files sequentially (e.g., `document.pdf` &rarr; `document_1.pdf` &rarr; `document_2.pdf`) without overwriting.
- **Zero-Data-Loss Safety**: Moves files using `shutil.move()`; never deletes any files.
- **Self-Preservation**: Automatically ignores the script itself (`organizer.py`) and its active log file (`organizer.log`) even when run directly inside the target directory.
- **Dry-Run Mode**: Full simulation capability to preview all actions without touching the filesystem.
- **Comprehensive Logging**: Automatically logs all operations, moves, collision renames, and errors with ISO timestamps in `organizer.log`.
- **Formatted Summary**: Displays a detailed console summary of total files scanned, organized, category breakdowns, skipped files, and encountered errors.
- **Pure Standard Library**: Zero external third-party dependencies required.

---

## Technologies Used

| Technology | Purpose |
| :--- | :--- |
| **Python 3** | Core runtime environment (compatible with Python 3.8+) |
| **`os`** | Directory traversal via `os.scandir()` for high-performance file inspection |
| **`shutil`** | Safe file relocation via `shutil.move()` |
| **`pathlib`** | Cross-platform, object-oriented filesystem path manipulation |
| **`logging`** | Automated timestamped event and audit recording in `organizer.log` |
| **`argparse`** | Command-line option parsing (`--dir`, `--dry-run`, `--yes`) |
| **`dataclasses`** | Structured data modeling for move plans and execution statistics |

---

## Project Structure

```
Task-3-File-Organizer/
│
├── organizer.py         # Main file organizer utility script
├── test_organizer.py    # Automated test suite covering all 11+ test scenarios
├── requirements.txt     # Standard library dependencies declaration
├── .gitignore           # Git ignore patterns for logs, cache, and test folders
├── README.md            # Comprehensive project documentation
└── organizer.log        # Generated runtime activity and audit log
```

---

## Installation Instructions

### Prerequisites
- Python 3.8 or higher installed on your computer.
- Verify Python installation:
  ```bash
  python --version
  ```

### Clone or Download
Navigate to your project directory:
```bash
cd d:\Python-Intership\Task-3-File-Organizer
```

### Install Dependencies
No third-party packages are required! The utility uses Python built-in modules exclusively.
```bash
# Optional verification of requirements file
pip install -r requirements.txt
```

---

## How to Run

### 1. Interactive Mode (Recommended)
Launch the tool interactively:
```bash
python organizer.py
```
You will be guided through:
1. Entering the target folder path (with instant validation).
2. Choosing whether to run in Dry-Run mode.
3. Reviewing a formatted table of planned file movements.
4. Confirming execution before any files are moved.

### 2. Command-Line Mode
You can specify the directory path directly via the `-d` or `--dir` option:
```bash
python organizer.py --dir "C:\Users\YourUser\Downloads"
```

To skip the interactive confirmation prompt (useful for automated scripts):
```bash
python organizer.py --dir "C:\Users\YourUser\Downloads" -y
```

### 3. Dry-Run (Preview) Mode
Simulate organization without modifying or moving any files:
```bash
python organizer.py --dir "C:\Users\YourUser\Downloads" --dry-run
```

To view all CLI arguments:
```bash
python organizer.py --help
```

---

## File Extension Mapping

| Category Folder | Recognized Extensions |
| :--- | :--- |
| **`Documents/`** | `.pdf`, `.doc`, `.docx`, `.txt`, `.ppt`, `.pptx`, `.xls`, `.xlsx` |
| **`Images/`** | `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.svg` |
| **`Videos/`** | `.mp4`, `.mkv`, `.avi`, `.mov` |
| **`Archives/`** | `.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.tar.gz`, `.tar.bz2` |
| **`Code/`** | `.py`, `.java`, `.cpp`, `.c`, `.html`, `.css`, `.js`, `.json` |
| **`Other/`** | Any unknown extension or files without extensions (e.g. `LICENSE`, `.xyz`, `.dat`) |

*Subdirectories and existing category folders inside the target directory are ignored and left untouched.*

---

## Safety Features

1. **Explicit User Selection Required**:
   The organizer never automatically selects or modifies whole system drives (`C:\`, `/`) or the actual user Downloads directory without explicit confirmation.
2. **Anti-Overwrite Collision Protection**:
   If a destination folder already contains a file with the same name, the new file is automatically given a unique suffixed name (e.g., `invoice_1.pdf`, `invoice_2.pdf`). Existing files are never overwritten.
3. **Non-Destructive Operations**:
   The script does not invoke `os.remove()` or delete files under any condition.
4. **Self-Preservation**:
   The active script (`organizer.py`) and log file (`organizer.log`) are guarded so they are never moved, even when the user runs the utility directly inside the target directory.
5. **Confirmation Step**:
   A prompt requires explicit user approval (`[y/N]`) before relocating files.
6. **Graceful Exception Handling**:
   Catches `PermissionError`, `FileExistsError`, and `OSError` without terminating the process, logging the exact error and continuing with the remaining files.

---

## Logging & Audit Trail

All operations are recorded in `organizer.log` in the following format:
```text
2026-11-06 16:58:52 - INFO - Target directory selected: C:\Users\Username\Downloads
2026-11-06 16:58:52 - INFO - Moved: 'resume.pdf' -> 'Documents/resume.pdf'
2026-11-06 16:58:52 - INFO - Moved: 'photo.png' -> 'Images/photo.png'
2026-11-06 16:58:52 - INFO - Moved: 'document.pdf' -> 'Documents/document_1.pdf' (renamed to 'document_1.pdf' to prevent overwrite)
2026-11-06 16:58:52 - INFO - Organization complete. Scanned: 3, Organized: 3, Errors: 0
```

---

## Example Execution

```text
================================================================================
           AUTOMATED FILE ORGANIZER & CLEANUP UTILITY
================================================================================
  Organize cluttered directories into categorized folders by extension.
  Safety Guaranteed: No file deletions | Collision protection | Dry-run mode
================================================================================

Enter the directory path to organize (or 'q' to quit): C:\Users\Demo\Downloads

Target Directory: C:\Users\Demo\Downloads
Run in Dry-Run mode (preview only without moving files)? [y/N]: n

[PLANNED MOVEMENTS] - 6 file(s) found to organize:
--------------------------------------------------------------------------------
Source File                         -> Category     -> Destination Filename
--------------------------------------------------------------------------------
annual_report.pdf                   -> Documents    -> annual_report.pdf
vacation.jpg                        -> Images       -> vacation.jpg
clip.mp4                            -> Videos       -> clip.mp4
project_archive.zip                 -> Archives     -> project_archive.zip
app.py                              -> Code         -> app.py
custom_data.bin                     -> Other        -> custom_data.bin
--------------------------------------------------------------------------------

Are you sure you want to organize 6 file(s)? [y/N]: y

[*] Organizing files...

============================================================
             EXECUTION SUMMARY
============================================================
  Total files scanned   : 6
  Total files organized : 6
  --------------------------------------------------------
  * Documents count     : 1
  * Images count        : 1
  * Videos count        : 1
  * Archives count      : 1
  * Code files count    : 1
  * Other files count   : 1
  --------------------------------------------------------
  Files skipped         : 0
  Errors encountered    : 0
============================================================

[SUCCESS] File organization complete. Log saved to 'organizer.log'.
```

---

## Testing & Verification

An automated test suite is provided in `test_organizer.py`. It uses temporary directories and mocks to test all requirements without altering any real files.

### Running the Test Suite
```bash
python test_organizer.py
```

### Verified Test Cases
| # | Test Scenario | Status |
| :---: | :--- | :---: |
| 1 | **Documents organization** (`.pdf`, `.doc`, `.docx`, `.txt`, `.ppt`, `.pptx`, `.xls`, `.xlsx`) | **PASSED** |
| 2 | **Images organization** (`.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.svg`) | **PASSED** |
| 3 | **Videos organization** (`.mp4`, `.mkv`, `.avi`, `.mov`) | **PASSED** |
| 4 | **Archives organization** (`.zip`, `.rar`, `.7z`, `.tar`, `.gz`, `.tar.gz`) | **PASSED** |
| 5 | **Code organization** (`.py`, `.java`, `.cpp`, `.c`, `.html`, `.css`, `.js`, `.json`) | **PASSED** |
| 6 | **Unknown extension handling** (unrecognized extensions & no-extension files to `Other/`) | **PASSED** |
| 7 | **Duplicate filename handling** (`document_1.pdf`, `document_2.pdf` collision preservation) | **PASSED** |
| 8 | **Invalid directory handling** (non-existent paths, empty input, file paths rejected) | **PASSED** |
| 9 | **Permission error handling** (simulated locks caught gracefully without application crash) | **PASSED** |
| 10 | **Dry-run mode** (simulates actions without modifying filesystem or creating folders) | **PASSED** |
| 11 | **Confirmation and cancellation** (cancels operations safely if user declines confirmation) | **PASSED** |
| 12 | **Self-protection** (script itself and log file are skipped even inside target directory) | **PASSED** |

---

## License
This project is open-source and created for educational and internship demonstration purposes.
