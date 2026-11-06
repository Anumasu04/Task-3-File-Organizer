#!/usr/bin/env python3
"""
Comprehensive Test Suite for Automated File Organizer & Cleanup Utility
Python Programming Internship - Task 3

Tests all 11 requirements:
1. Documents organization
2. Images organization
3. Videos organization
4. Archives organization
5. Code organization
6. Unknown extension handling
7. Duplicate filename handling
8. Invalid directory handling
9. Permission error handling
10. Dry-run mode
11. Confirmation and cancellation
Plus: Script & log protection verification
"""

import os
import shutil
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

from organizer import (
    CATEGORIES,
    EXTENSION_MAP,
    LOG_FILENAME,
    OrganizationStats,
    execute_organization,
    generate_unique_filename,
    is_protected_file,
    run_organizer,
    scan_directory,
    setup_logger,
    validate_directory_input,
)


class TestRunner:
    def __init__(self):
        self.passed_tests = []
        self.failed_tests = []

    def run_test(self, test_name: str, test_func):
        print(f"\n[RUNNING] {test_name}...")
        try:
            test_func()
            print(f"[PASSED]  {test_name}")
            self.passed_tests.append(test_name)
        except AssertionError as e:
            print(f"[FAILED]  {test_name}: Assertion Error -> {e}")
            self.failed_tests.append((test_name, str(e)))
        except Exception as e:
            print(f"[FAILED]  {test_name}: Unexpected Exception -> {e}")
            self.failed_tests.append((test_name, str(e)))

    def print_summary(self):
        print("\n" + "=" * 70)
        print("                        TEST REPORT SUMMARY")
        print("=" * 70)
        print(f"Total Tests Run : {len(self.passed_tests) + len(self.failed_tests)}")
        print(f"Passed          : {len(self.passed_tests)}")
        print(f"Failed          : {len(self.failed_tests)}")
        print("-" * 70)
        for idx, name in enumerate(self.passed_tests, 1):
            print(f"  {idx}. [PASS] {name}")
        for idx, (name, err) in enumerate(self.failed_tests, 1):
            print(f"  {idx}. [FAIL] {name}: {err}")
        print("=" * 70)


def create_empty_file(file_path: Path, content: str = "sample content") -> Path:
    """Helper to create a file with optional content."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path


# ==============================================================================
# TEST CASES
# ==============================================================================

def test_1_documents_organization():
    """Test 1: Documents organization (.pdf, .doc, .docx, .txt, .ppt, .pptx, .xls, .xlsx)"""
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)
        doc_files = [
            "report.pdf", "letter.doc", "contract.docx", "notes.txt",
            "slides.ppt", "deck.pptx", "data.xls", "budget.xlsx"
        ]
        for f in doc_files:
            create_empty_file(dir_path / f)

        stats = run_organizer(directory_path=str(dir_path), auto_confirm=True)
        assert stats is not None, "Organizer returned None"
        assert stats.organized_count == len(doc_files), f"Expected {len(doc_files)} organized, got {stats.organized_count}"
        assert stats.category_counts["Documents"] == len(doc_files), "Not all documents were counted in Documents category"

        doc_dir = dir_path / "Documents"
        assert doc_dir.exists() and doc_dir.is_dir(), "Documents directory was not created"
        for f in doc_files:
            dest_file = doc_dir / f
            assert dest_file.exists(), f"Expected document {dest_file} to exist in Documents/"
            assert not (dir_path / f).exists(), f"Original file {dir_path / f} should no longer be at root"


def test_2_images_organization():
    """Test 2: Images organization (.jpg, .jpeg, .png, .gif, .bmp, .svg)"""
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)
        img_files = ["photo.jpg", "portrait.jpeg", "logo.png", "meme.gif", "icon.bmp", "vector.svg"]
        for f in img_files:
            create_empty_file(dir_path / f)

        stats = run_organizer(directory_path=str(dir_path), auto_confirm=True)
        assert stats is not None
        assert stats.organized_count == len(img_files)
        assert stats.category_counts["Images"] == len(img_files)

        img_dir = dir_path / "Images"
        assert img_dir.exists() and img_dir.is_dir()
        for f in img_files:
            assert (img_dir / f).exists()
            assert not (dir_path / f).exists()


def test_3_videos_organization():
    """Test 3: Videos organization (.mp4, .mkv, .avi, .mov)"""
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)
        vid_files = ["movie.mp4", "clip.mkv", "film.avi", "recording.mov"]
        for f in vid_files:
            create_empty_file(dir_path / f)

        stats = run_organizer(directory_path=str(dir_path), auto_confirm=True)
        assert stats is not None
        assert stats.organized_count == len(vid_files)
        assert stats.category_counts["Videos"] == len(vid_files)

        vid_dir = dir_path / "Videos"
        assert vid_dir.exists() and vid_dir.is_dir()
        for f in vid_files:
            assert (vid_dir / f).exists()
            assert not (dir_path / f).exists()


def test_4_archives_organization():
    """Test 4: Archives organization (.zip, .rar, .7z, .tar, .gz, .tar.gz)"""
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)
        archive_files = ["backup.zip", "package.rar", "data.7z", "source.tar", "logs.gz", "release.tar.gz"]
        for f in archive_files:
            create_empty_file(dir_path / f)

        stats = run_organizer(directory_path=str(dir_path), auto_confirm=True)
        assert stats is not None
        assert stats.organized_count == len(archive_files)
        assert stats.category_counts["Archives"] == len(archive_files)

        arch_dir = dir_path / "Archives"
        assert arch_dir.exists() and arch_dir.is_dir()
        for f in archive_files:
            assert (arch_dir / f).exists()
            assert not (dir_path / f).exists()


def test_5_code_organization():
    """Test 5: Code organization (.py, .java, .cpp, .c, .html, .css, .js, .json)"""
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)
        code_files = [
            "script.py", "App.java", "main.cpp", "algo.c",
            "index.html", "style.css", "bundle.js", "config.json"
        ]
        for f in code_files:
            create_empty_file(dir_path / f)

        stats = run_organizer(directory_path=str(dir_path), auto_confirm=True)
        assert stats is not None
        assert stats.organized_count == len(code_files)
        assert stats.category_counts["Code"] == len(code_files)

        code_dir = dir_path / "Code"
        assert code_dir.exists() and code_dir.is_dir()
        for f in code_files:
            assert (code_dir / f).exists()
            assert not (dir_path / f).exists()


def test_6_unknown_extension_handling():
    """Test 6: Unknown extension handling (unknown extensions placed in Other folder)"""
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)
        unknown_files = ["random.xyz", "custom.dat", "LICENSE", "binary.iso"]
        for f in unknown_files:
            create_empty_file(dir_path / f)

        stats = run_organizer(directory_path=str(dir_path), auto_confirm=True)
        assert stats is not None
        assert stats.organized_count == len(unknown_files)
        assert stats.category_counts["Other"] == len(unknown_files)

        other_dir = dir_path / "Other"
        assert other_dir.exists() and other_dir.is_dir()
        for f in unknown_files:
            assert (other_dir / f).exists()
            assert not (dir_path / f).exists()


def test_7_duplicate_filename_handling():
    """Test 7: Duplicate filename handling (document_1.pdf, document_2.pdf without overwriting)"""
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)
        doc_dir = dir_path / "Documents"

        # Pre-create existing files in Documents/
        create_empty_file(doc_dir / "document.pdf", "Original content")
        create_empty_file(doc_dir / "document_1.pdf", "First collision content")

        # Now place a new document.pdf in the root directory to organize
        create_empty_file(dir_path / "document.pdf", "New document to move")

        stats = run_organizer(directory_path=str(dir_path), auto_confirm=True)
        assert stats is not None
        assert stats.organized_count == 1

        # Verify original files were preserved without overwrite
        with open(doc_dir / "document.pdf", "r", encoding="utf-8") as f:
            assert f.read() == "Original content", "Original file was overwritten!"
        with open(doc_dir / "document_1.pdf", "r", encoding="utf-8") as f:
            assert f.read() == "First collision content", "First duplicate file was overwritten!"

        # Verify the new file was renamed to document_2.pdf
        assert (doc_dir / "document_2.pdf").exists(), "New file was not renamed to document_2.pdf"
        with open(doc_dir / "document_2.pdf", "r", encoding="utf-8") as f:
            assert f.read() == "New document to move"


def test_8_invalid_directory_handling():
    """Test 8: Invalid directory handling (validation, non-existent path, file path)"""
    # 1. Non-existent path
    is_valid, msg, path = validate_directory_input("non_existent_folder_xyz_12345")
    assert not is_valid, "Expected non-existent path to be invalid"
    assert "does not exist" in msg.lower(), f"Unexpected error message: {msg}"

    # 2. Empty path
    is_valid, msg, path = validate_directory_input("   ")
    assert not is_valid, "Expected empty path to be invalid"
    assert "cannot be empty" in msg.lower(), f"Unexpected error message: {msg}"

    # 3. Path pointing to a file instead of directory
    with tempfile.NamedTemporaryFile(delete=False) as tf:
        tf_name = tf.name
    try:
        is_valid, msg, path = validate_directory_input(tf_name)
        assert not is_valid, "Expected file path to be invalid as directory"
        assert "not a directory" in msg.lower(), f"Unexpected error message: {msg}"
    finally:
        os.remove(tf_name)


def test_9_permission_errors_handling():
    """Test 9: Permission errors handling (graceful catch, error logged, no crash)"""
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)
        create_empty_file(dir_path / "protected.txt")
        create_empty_file(dir_path / "normal.txt")

        # Mock shutil.move to raise PermissionError specifically for protected.txt
        original_move = shutil.move

        def mock_move(src, dst):
            if "protected.txt" in str(src):
                raise PermissionError("Access denied by system lock simulation")
            return original_move(src, dst)

        with patch("shutil.move", side_effect=mock_move):
            stats = run_organizer(directory_path=str(dir_path), auto_confirm=True)

        assert stats is not None
        assert stats.error_count == 1, f"Expected 1 error, got {stats.error_count}"
        assert stats.organized_count == 1, f"Expected 1 file successfully organized, got {stats.organized_count}"
        assert len(stats.errors) == 1
        assert "protected.txt" in stats.errors[0][0]
        # Normal file should still have moved successfully
        assert (dir_path / "Documents" / "normal.txt").exists()


def test_10_dry_run_mode():
    """Test 10: Dry-run mode (previews actions without modifying filesystem)"""
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)
        create_empty_file(dir_path / "document.pdf")
        create_empty_file(dir_path / "image.png")
        create_empty_file(dir_path / "code.py")

        stats = run_organizer(directory_path=str(dir_path), dry_run=True, auto_confirm=True)
        assert stats is not None
        assert stats.scanned_count == 3
        assert stats.organized_count == 3

        # Verify that NO category folders were created
        assert not (dir_path / "Documents").exists(), "Documents folder should NOT be created in dry-run"
        assert not (dir_path / "Images").exists(), "Images folder should NOT be created in dry-run"
        assert not (dir_path / "Code").exists(), "Code folder should NOT be created in dry-run"

        # Verify that files remain in the root directory untouched
        assert (dir_path / "document.pdf").exists(), "document.pdf should remain untouched"
        assert (dir_path / "image.png").exists(), "image.png should remain untouched"
        assert (dir_path / "code.py").exists(), "code.py should remain untouched"


def test_11_confirmation_and_cancellation():
    """Test 11: Confirmation and cancellation (user inputs 'n' -> operations aborted)"""
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)
        create_empty_file(dir_path / "test1.pdf")
        create_empty_file(dir_path / "test2.png")

        # Simulate user entering 'n' at confirmation prompt
        with patch("builtins.input", return_value="n"):
            stats = run_organizer(directory_path=str(dir_path), auto_confirm=False)

        assert stats is not None
        assert stats.organized_count == 0, "No files should be organized when cancelled"
        assert stats.skipped_count == 2, "Files should be marked as skipped when cancelled"

        # Verify files were NOT moved
        assert (dir_path / "test1.pdf").exists()
        assert (dir_path / "test2.png").exists()
        assert not (dir_path / "Documents").exists()


def test_12_script_and_log_protection():
    """Test 12 (Bonus Safety): Protection of organizer.py and organizer.log when inside target dir"""
    with tempfile.TemporaryDirectory() as temp_dir:
        dir_path = Path(temp_dir)
        # Create a file named organizer.py and organizer.log inside the target directory
        create_empty_file(dir_path / "organizer.py", "# Script code")
        create_empty_file(dir_path / LOG_FILENAME, "Log entries")
        create_empty_file(dir_path / "actual_file.pdf", "PDF content")

        stats = run_organizer(directory_path=str(dir_path), auto_confirm=True)
        assert stats is not None
        assert stats.organized_count == 1
        assert stats.skipped_count == 2, "organizer.py and organizer.log should be skipped"

        # organizer.py and organizer.log should still be at root
        assert (dir_path / "organizer.py").exists(), "organizer.py should NOT be moved"
        assert (dir_path / LOG_FILENAME).exists(), "organizer.log should NOT be moved"
        # actual_file.pdf should be in Documents/
        assert (dir_path / "Documents" / "actual_file.pdf").exists()


# ==============================================================================
# MAIN TEST EXECUTION
# ==============================================================================

if __name__ == "__main__":
    runner = TestRunner()

    print("======================================================================")
    print("      AUTOMATED FILE ORGANIZER - UNIT & INTEGRATION TEST SUITE        ")
    print("======================================================================")

    runner.run_test("1. Documents Organization (.pdf, .doc, .docx, .txt, .ppt, .pptx, .xls, .xlsx)", test_1_documents_organization)
    runner.run_test("2. Images Organization (.jpg, .jpeg, .png, .gif, .bmp, .svg)", test_2_images_organization)
    runner.run_test("3. Videos Organization (.mp4, .mkv, .avi, .mov)", test_3_videos_organization)
    runner.run_test("4. Archives Organization (.zip, .rar, .7z, .tar, .gz, .tar.gz)", test_4_archives_organization)
    runner.run_test("5. Code Organization (.py, .java, .cpp, .c, .html, .css, .js, .json)", test_5_code_organization)
    runner.run_test("6. Unknown Extension Handling (Other category)", test_6_unknown_extension_handling)
    runner.run_test("7. Duplicate Filename Handling (name_1, name_2 preservation)", test_7_duplicate_filename_handling)
    runner.run_test("8. Invalid Directory Handling (non-existent, empty, file path)", test_8_invalid_directory_handling)
    runner.run_test("9. Permission Errors Handling (graceful exception handling)", test_9_permission_errors_handling)
    runner.run_test("10. Dry-Run Mode (simulation without moving)", test_10_dry_run_mode)
    runner.run_test("11. Confirmation and Cancellation (user aborts with 'n')", test_11_confirmation_and_cancellation)
    runner.run_test("12. Script & Log Protection (self-preservation safety)", test_12_script_and_log_protection)

    runner.print_summary()
    if runner.failed_tests:
        sys.exit(1)
    else:
        sys.exit(0)
