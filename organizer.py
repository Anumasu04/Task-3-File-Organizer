#!/usr/bin/env python3
"""
Automated File Organizer & Cleanup Utility
Python Programming Internship - Task 3

Author: Internship Candidate
Technologies: Python 3, os, shutil, pathlib, logging

Description:
A reliable desktop automation utility that organizes files in a selected directory
into categorized folders based on their file extensions.
Includes dry-run preview, collision handling, comprehensive logging,
and execution summary.
"""

import argparse
import logging
import os
import shutil
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

# ==============================================================================
# CONFIGURATION & CONSTANTS
# ==============================================================================

# Mapping of file extensions (lowercase) to their respective category folder names
EXTENSION_MAP: Dict[str, str] = {
    # Documents
    ".pdf": "Documents",
    ".doc": "Documents",
    ".docx": "Documents",
    ".txt": "Documents",
    ".ppt": "Documents",
    ".pptx": "Documents",
    ".xls": "Documents",
    ".xlsx": "Documents",
    # Images
    ".jpg": "Images",
    ".jpeg": "Images",
    ".png": "Images",
    ".gif": "Images",
    ".bmp": "Images",
    ".svg": "Images",
    # Videos
    ".mp4": "Videos",
    ".mkv": "Videos",
    ".avi": "Videos",
    ".mov": "Videos",
    # Archives
    ".zip": "Archives",
    ".rar": "Archives",
    ".7z": "Archives",
    ".tar": "Archives",
    ".gz": "Archives",
    # Code
    ".py": "Code",
    ".java": "Code",
    ".cpp": "Code",
    ".c": "Code",
    ".html": "Code",
    ".css": "Code",
    ".js": "Code",
    ".json": "Code",
}

DEFAULT_CATEGORY: str = "Other"

# Standard category folder names
CATEGORIES: List[str] = [
    "Documents",
    "Images",
    "Videos",
    "Archives",
    "Code",
    "Other",
]

LOG_FILENAME: str = "organizer.log"


# ==============================================================================
# DATA STRUCTURES
# ==============================================================================

@dataclass
class MovePlan:
    """Represents a planned file movement."""
    source_path: Path
    category: str
    target_dir: Path
    target_path: Path
    is_renamed: bool = False
    original_target_name: str = ""


@dataclass
class OrganizationStats:
    """Tracks statistics of files scanned, organized, skipped, and errors."""
    scanned_count: int = 0
    organized_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    category_counts: Dict[str, int] = field(
        default_factory=lambda: {cat: 0 for cat in CATEGORIES}
    )
    errors: List[Tuple[str, str]] = field(default_factory=list)


# ==============================================================================
# LOGGING SETUP
# ==============================================================================

def setup_logger(log_file_path: Optional[Path] = None) -> logging.Logger:
    """
    Configures and returns the application logger.
    Logs are recorded with timestamps, level, and messages in organizer.log.
    """
    logger = logging.getLogger("FileOrganizer")
    logger.setLevel(logging.INFO)

    # Determine default log file path
    if log_file_path is None:
        log_file_path = Path(__file__).resolve().parent / LOG_FILENAME

    # Avoid adding duplicate handlers to the same logger
    has_target_handler = any(
        isinstance(h, logging.FileHandler) and Path(h.baseFilename) == log_file_path.resolve()
        for h in logger.handlers
    )

    if not has_target_handler:
        file_handler = logging.FileHandler(log_file_path, encoding="utf-8")
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def close_logger(logger: logging.Logger) -> None:
    """Flushes and closes all handlers of the logger."""
    for handler in list(logger.handlers):
        handler.flush()
        handler.close()
        logger.removeHandler(handler)


# ==============================================================================
# CORE LOGIC FUNCTIONS
# ==============================================================================

def get_category_for_file(file_path: Path) -> str:
    """
    Returns the folder category corresponding to a file.
    Supports compound extensions (e.g. .tar.gz) and single extensions.
    If the extension is unrecognized or missing, returns DEFAULT_CATEGORY ('Other').
    """
    name_lower = file_path.name.lower()

    # Handle common compound archive extensions
    if name_lower.endswith(".tar.gz") or name_lower.endswith(".tar.bz2"):
        return "Archives"

    suffix = file_path.suffix.lower()
    return EXTENSION_MAP.get(suffix, DEFAULT_CATEGORY)


def generate_unique_filename(
    destination_dir: Path,
    filename: str,
    existing_planned: Optional[Set[str]] = None,
) -> Tuple[Path, bool]:
    """
    Generates a unique destination path in destination_dir to prevent overwriting existing files.
    If 'document.pdf' already exists (on disk or in existing_planned), generates
    'document_1.pdf', 'document_2.pdf', etc.

    Returns:
        Tuple[Path, bool]: (unique_path, was_renamed)
    """
    planned_set = existing_planned if existing_planned is not None else set()
    target_path = destination_dir / filename

    # Resolve key for case-insensitive lookup
    target_key = str(target_path.resolve()).lower()

    # If the file does not exist on disk and is not planned for another move
    if not target_path.exists() and target_key not in planned_set:
        return target_path, False

    source_p = Path(filename)
    stem = source_p.stem
    suffix = source_p.suffix

    # Special handling for compound extensions like .tar.gz
    if filename.lower().endswith(".tar.gz"):
        stem = filename[:-7]
        suffix = ".tar.gz"
    elif filename.lower().endswith(".tar.bz2"):
        stem = filename[:-8]
        suffix = ".tar.bz2"

    counter = 1
    while True:
        candidate_name = f"{stem}_{counter}{suffix}"
        candidate_path = destination_dir / candidate_name
        candidate_key = str(candidate_path.resolve()).lower()

        if not candidate_path.exists() and candidate_key not in planned_set:
            return candidate_path, True
        counter += 1


def is_protected_file(entry_path: Path, script_path: Path, log_file_path: Path) -> bool:
    """
    Checks if a file should be protected from being moved.
    Protects:
      - The organizer script itself (organizer.py)
      - The organizer log file (organizer.log)
    """
    try:
        resolved_entry = entry_path.resolve()
        if resolved_entry == script_path.resolve():
            return True
        if resolved_entry == log_file_path.resolve():
            return True
    except Exception:
        pass

    # Fallback name check
    if entry_path.name.lower() in (script_path.name.lower(), LOG_FILENAME.lower()):
        return True

    return False


def scan_directory(
    target_dir: Path,
    script_path: Optional[Path] = None,
    log_file_path: Optional[Path] = None,
) -> Tuple[List[MovePlan], List[Path]]:
    """
    Scans the given directory using os.scandir().
    - Identifies files and their extensions.
    - Ignores subdirectories (including destination category folders).
    - Ignores organizer.py and organizer.log.

    Returns:
        Tuple of (list of MovePlan objects, list of skipped Paths).
    """
    if script_path is None:
        script_path = Path(__file__).resolve()
    if log_file_path is None:
        log_file_path = script_path.parent / LOG_FILENAME

    plans: List[MovePlan] = []
    skipped_files: List[Path] = []
    planned_destinations: Set[str] = set()

    with os.scandir(target_dir) as entries:
        for entry in entries:
            entry_path = Path(entry.path)

            # Requirement C: Ignore directories (category folders and subfolders are untouched)
            if entry.is_dir():
                continue

            # Requirement C & F: Do not move the script itself or its log file
            if is_protected_file(entry_path, script_path, log_file_path):
                skipped_files.append(entry_path)
                continue

            # Requirement B: Determine category
            category = get_category_for_file(entry_path)
            dest_dir = target_dir / category

            # Requirement E: Safe unique filename generation to prevent overwrite
            unique_path, was_renamed = generate_unique_filename(
                dest_dir, entry_path.name, planned_destinations
            )
            planned_destinations.add(str(unique_path.resolve()).lower())

            plan = MovePlan(
                source_path=entry_path,
                category=category,
                target_dir=dest_dir,
                target_path=unique_path,
                is_renamed=was_renamed,
                original_target_name=entry_path.name,
            )
            plans.append(plan)

    return plans, skipped_files


def execute_organization(
    plans: List[MovePlan],
    dry_run: bool = False,
    logger: Optional[logging.Logger] = None,
) -> OrganizationStats:
    """
    Executes the file organization based on the supplied MovePlan list.
    If dry_run is True, simulates the process without modifying the filesystem.

    Returns:
        OrganizationStats with complete execution counts and errors.
    """
    stats = OrganizationStats()
    stats.scanned_count = len(plans)

    for plan in plans:
        if dry_run:
            # Dry run simulation: no filesystem changes
            stats.organized_count += 1
            stats.category_counts[plan.category] += 1
            rename_info = (
                f" (renamed to avoid collision with '{plan.original_target_name}')"
                if plan.is_renamed
                else ""
            )
            if logger:
                logger.info(
                    f"[DRY-RUN] Would move: '{plan.source_path.name}' -> "
                    f"'{plan.category}/{plan.target_path.name}'{rename_info}"
                )
            continue

        # Live run: execute moves safely
        try:
            # Requirement D: Automatically create category folder when needed
            plan.target_dir.mkdir(parents=True, exist_ok=True)

            # Ensure final destination does not collide at execution time
            final_dest, was_re_renamed = generate_unique_filename(
                plan.target_dir, plan.target_path.name
            )
            is_renamed = plan.is_renamed or was_re_renamed

            # Requirement E: Move file safely with shutil.move
            shutil.move(str(plan.source_path), str(final_dest))

            stats.organized_count += 1
            stats.category_counts[plan.category] += 1

            rename_info = (
                f" (renamed to '{final_dest.name}' to prevent overwrite)"
                if is_renamed
                else ""
            )
            if logger:
                logger.info(
                    f"Moved: '{plan.source_path.name}' -> "
                    f"'{plan.category}/{final_dest.name}'{rename_info}"
                )

        except PermissionError as pe:
            stats.error_count += 1
            err_msg = f"Permission denied for '{plan.source_path.name}': {pe}"
            stats.errors.append((plan.source_path.name, err_msg))
            if logger:
                logger.error(err_msg)
        except FileExistsError as fee:
            stats.error_count += 1
            err_msg = f"File already exists '{plan.target_path.name}': {fee}"
            stats.errors.append((plan.source_path.name, err_msg))
            if logger:
                logger.error(err_msg)
        except shutil.Error as se:
            stats.error_count += 1
            err_msg = f"Shutil error moving '{plan.source_path.name}': {se}"
            stats.errors.append((plan.source_path.name, err_msg))
            if logger:
                logger.error(err_msg)
        except OSError as oe:
            stats.error_count += 1
            err_msg = f"OS error moving '{plan.source_path.name}': {oe}"
            stats.errors.append((plan.source_path.name, err_msg))
            if logger:
                logger.error(err_msg)
        except Exception as ex:
            stats.error_count += 1
            err_msg = f"Unexpected error moving '{plan.source_path.name}': {ex}"
            stats.errors.append((plan.source_path.name, err_msg))
            if logger:
                logger.error(err_msg)

    return stats


# ==============================================================================
# USER INTERFACE & PRESENTATION HELPERS
# ==============================================================================

def print_banner() -> None:
    """Displays the application title banner."""
    banner = r"""
================================================================
          AUTOMATED FILE ORGANIZER & CLEANUP UTILITY
================================================================
 Organize directory files into categorized folders by extension.
 Safety Guaranteed: No Deletions | Overwrite Protection | Dry-Run
================================================================
"""
    print(banner)


def validate_directory_input(user_input: str) -> Tuple[bool, str, Optional[Path]]:
    """
    Validates the directory path provided by the user.

    Returns:
        Tuple[bool, str, Optional[Path]]: (is_valid, error_message, resolved_path)
    """
    raw_path = user_input.strip()

    # Strip enclosing quotes if user pasted path with quotes
    if (raw_path.startswith('"') and raw_path.endswith('"')) or (
        raw_path.startswith("'") and raw_path.endswith("'")
    ):
        raw_path = raw_path[1:-1].strip()

    if not raw_path:
        return False, "Directory path cannot be empty.", None

    target_path = Path(raw_path).expanduser()

    if not target_path.exists():
        return False, f"Directory does not exist: '{raw_path}'", None

    if not target_path.is_dir():
        return False, f"The specified path is a file, not a directory: '{raw_path}'", None

    # Safety check: avoid organizing root drive directory directly
    resolved = target_path.resolve()
    if resolved == resolved.anchor or resolved == resolved.parent:
        return (
            False,
            f"Safety warning: Cannot organize the root drive directory directly ('{resolved}'). "
            "Please select a specific subfolder.",
            None,
        )

    return True, "", resolved


def display_preview(plans: List[MovePlan], dry_run: bool = False) -> None:
    """Displays a clean preview of planned file movements."""
    mode_text = "[DRY-RUN PREVIEW]" if dry_run else "[PLANNED MOVEMENTS]"
    print(f"\n{mode_text} - {len(plans)} file(s) found to organize:")
    print("-" * 80)
    print(f"{'Source File':<35} -> {'Category':<12} -> {'Destination Filename'}")
    print("-" * 80)

    for plan in plans:
        rename_tag = " (renamed)" if plan.is_renamed else ""
        print(
            f"{plan.source_path.name:<35} -> {plan.category:<12} -> "
            f"{plan.target_path.name}{rename_tag}"
        )
    print("-" * 80)


def display_summary(stats: OrganizationStats, dry_run: bool = False) -> None:
    """
    Requirement H: Formatted execution summary displaying:
    - Total files scanned
    - Total files organized
    - Documents count
    - Images count
    - Videos count
    - Archives count
    - Code files count
    - Other files count
    - Files skipped
    - Errors encountered
    """
    title = "DRY-RUN EXECUTION SUMMARY" if dry_run else "EXECUTION SUMMARY"
    print("\n" + "=" * 60)
    print(f"             {title}")
    print("=" * 60)
    print(f"  Total files scanned   : {stats.scanned_count}")
    print(f"  Total files organized : {stats.organized_count}")
    print("  " + "-" * 56)
    print(f"  * Documents count     : {stats.category_counts.get('Documents', 0)}")
    print(f"  * Images count        : {stats.category_counts.get('Images', 0)}")
    print(f"  * Videos count        : {stats.category_counts.get('Videos', 0)}")
    print(f"  * Archives count      : {stats.category_counts.get('Archives', 0)}")
    print(f"  * Code files count    : {stats.category_counts.get('Code', 0)}")
    print(f"  * Other files count   : {stats.category_counts.get('Other', 0)}")
    print("  " + "-" * 56)
    print(f"  Files skipped         : {stats.skipped_count}")
    print(f"  Errors encountered    : {stats.error_count}")
    print("=" * 60)

    if stats.errors:
        print("\n[!] Errors details:")
        for fname, err in stats.errors:
            print(f"  - {fname}: {err}")
        print("=" * 60)


def prompt_user_confirmation(prompt_text: str = "Proceed with organizing files? [y/N]: ") -> bool:
    """Prompts user for confirmation before moving files."""
    try:
        response = input(prompt_text).strip().lower()
        return response in ("y", "yes")
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled by user.")
        return False


# ==============================================================================
# MAIN APPLICATION CONTROLLER
# ==============================================================================

def run_organizer(
    directory_path: Optional[str] = None,
    dry_run: bool = False,
    auto_confirm: bool = False,
    logger: Optional[logging.Logger] = None,
) -> Optional[OrganizationStats]:
    """
    Main controller to organize files in a directory.
    Can be run interactively or non-interactively via arguments.
    """
    if logger is None:
        logger = setup_logger()

    # Step 1: Directory Selection & Validation
    target_path: Optional[Path] = None
    if directory_path:
        is_valid, err_msg, target_path = validate_directory_input(directory_path)
        if not is_valid:
            print(f"\n[ERROR] {err_msg}")
            return None
    else:
        while True:
            try:
                user_input = input("\nEnter the directory path to organize (or 'q' to quit): ").strip()
                if user_input.lower() in ("q", "quit", "exit"):
                    print("Exiting organizer. Goodbye!")
                    return None

                is_valid, err_msg, resolved_path = validate_directory_input(user_input)
                if not is_valid:
                    print(f"[ERROR] {err_msg}")
                    continue

                target_path = resolved_path
                break
            except (KeyboardInterrupt, EOFError):
                print("\nOperation cancelled.")
                return None

    print(f"\nTarget Directory: {target_path}")
    logger.info(f"Target directory selected: {target_path}")

    # Ask for dry-run if not passed as CLI argument
    if directory_path is None:
        try:
            dry_run_choice = input("Run in Dry-Run mode (preview only without moving files)? [y/N]: ").strip().lower()
            dry_run = dry_run_choice in ("y", "yes")
        except (KeyboardInterrupt, EOFError):
            print("\nOperation cancelled.")
            return None

    # Step 2: Scan Directory
    try:
        plans, skipped = scan_directory(target_path)
    except Exception as e:
        err_msg = f"Failed to scan directory '{target_path}': {e}"
        print(f"\n[ERROR] {err_msg}")
        logger.error(err_msg)
        return None

    total_scanned = len(plans) + len(skipped)

    if not plans:
        print("\nNo loose files found to organize in the selected directory.")
        if skipped:
            print(f"({len(skipped)} protected/script file(s) skipped).")
        stats = OrganizationStats(scanned_count=total_scanned, skipped_count=len(skipped))
        display_summary(stats, dry_run=dry_run)
        return stats

    # Step 3: Preview Planned Movements
    display_preview(plans, dry_run=dry_run)

    # Step 4: User Confirmation (unless auto_confirm or dry_run is enabled)
    if not dry_run and not auto_confirm:
        confirmed = prompt_user_confirmation(
            f"Are you sure you want to organize {len(plans)} file(s)? [y/N]: "
        )
        if not confirmed:
            print("\n[CANCELLED] Operation aborted by user. No files were moved.")
            logger.info("Operation aborted by user during confirmation.")
            stats = OrganizationStats(
                scanned_count=total_scanned,
                skipped_count=len(plans) + len(skipped),
            )
            display_summary(stats, dry_run=False)
            return stats

    # Step 5: Execute Organization
    action_type = "Simulating organization" if dry_run else "Organizing files"
    print(f"\n[*] {action_type}...")
    stats = execute_organization(plans, dry_run=dry_run, logger=logger)
    stats.scanned_count = total_scanned
    stats.skipped_count = len(skipped)

    # Step 6: Execution Summary
    display_summary(stats, dry_run=dry_run)

    if dry_run:
        print("\n[NOTE] Dry run complete. No files were modified or moved.")
        logger.info(
            f"Dry run complete. Scanned: {stats.scanned_count}, "
            f"Would organize: {stats.organized_count}"
        )
    else:
        print(f"\n[SUCCESS] File organization complete. Log saved to '{LOG_FILENAME}'.")
        logger.info(
            f"Organization complete. Scanned: {stats.scanned_count}, "
            f"Organized: {stats.organized_count}, "
            f"Errors: {stats.error_count}"
        )

    return stats


def parse_arguments() -> argparse.Namespace:
    """Configures and parses CLI arguments."""
    parser = argparse.ArgumentParser(
        description="Automated File Organizer & Cleanup Utility"
    )
    parser.add_argument(
        "-d",
        "--dir",
        dest="directory",
        type=str,
        help="Target directory path to organize",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview file movements without actually moving files",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation prompt and organize immediately",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for command line execution."""
    print_banner()
    args = parse_arguments()
    run_organizer(
        directory_path=args.directory,
        dry_run=args.dry_run,
        auto_confirm=args.yes,
    )


if __name__ == "__main__":
    main()
