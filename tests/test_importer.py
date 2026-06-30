import os
from pathlib import Path
import pytest
from move.importer import import_gpx, extract_first_timestamp, parse_year_month

# Sample GPX templates
VALID_GPX_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <name>Morning Run</name>
    <trkseg>
      <trkpt lat="45.0" lon="9.0">
        <ele>100</ele>
        <time>{timestamp}</time>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
"""

WPT_GPX_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test" xmlns="http://www.topografix.com/GPX/1/1">
  <wpt lat="45.0" lon="9.0">
    <time>{timestamp}</time>
  </wpt>
</gpx>
"""

NO_TIME_GPX = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test" xmlns="http://www.topografix.com/GPX/1/1">
  <trk>
    <trkseg>
      <trkpt lat="45.0" lon="9.0">
        <ele>100</ele>
      </trkpt>
    </trkseg>
  </trk>
</gpx>
"""

CORRUPTED_GPX = """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Test"
"""


def test_parse_year_month():
    # UTC ISO format
    assert parse_year_month("2026-06-30T10:48:51Z") == ("2026", "06")
    # Timezone offset format
    assert parse_year_month("2025-12-25T18:30:00+01:00") == ("2025", "12")
    # Date only format
    assert parse_year_month("2024-01-15") == ("2024", "01")
    # Invalid formats
    with pytest.raises(ValueError, match="Invalid timestamp format"):
        parse_year_month("invalid-date")


def test_import_single_valid_file(tmp_path):
    # Setup source file
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    source_file = source_dir / "activity.gpx"
    source_file.write_text(VALID_GPX_TEMPLATE.format(timestamp="2026-06-30T10:48:51Z"))
    
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    
    # Import
    result = import_gpx(str(source_file), str(storage_dir))
    
    # Verify results
    expected_dest = storage_dir / "2026" / "06" / "activity.gpx"
    assert len(result["imported"]) == 1
    assert result["imported"][0] == str(expected_dest)
    assert len(result["errors"]) == 0
    assert expected_dest.exists()
    assert "Morning Run" in expected_dest.read_text()



def test_import_directory_with_mixed_files(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    
    # Create valid GPX files
    file1 = source_dir / "file1.gpx"
    file1.write_text(VALID_GPX_TEMPLATE.format(timestamp="2026-01-01T12:00:00Z"))
    
    file2 = source_dir / "file2.GPX"  # Case insensitivity check
    file2.write_text(VALID_GPX_TEMPLATE.format(timestamp="2026-02-01T12:00:00Z"))
    
    # Create invalid files
    no_time_file = source_dir / "no_time.gpx"
    no_time_file.write_text(NO_TIME_GPX)
    
    corrupted_file = source_dir / "corrupted.gpx"
    corrupted_file.write_text(CORRUPTED_GPX)
    
    txt_file = source_dir / "readme.txt"
    txt_file.write_text("not a gpx file")
    
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    
    # Import
    result = import_gpx(str(source_dir), str(storage_dir))
    
    # Verify imports
    assert len(result["imported"]) == 2
    imported_paths = [Path(p) for p in result["imported"]]
    assert (storage_dir / "2026" / "01" / "file1.gpx") in imported_paths
    assert (storage_dir / "2026" / "02" / "file2.GPX") in imported_paths
    
    # Verify errors
    assert len(result["errors"]) == 2
    assert result["errors"][str(no_time_file.absolute())] == "No timestamp found"
    assert result["errors"][str(corrupted_file.absolute())] == "Corrupted file"
    # Note: txt_file is skipped silently in directory search because it's not a GPX file.
    # That is correct behavior (we only process .gpx files in directories).


def test_import_non_existent_source(tmp_path):
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    
    result = import_gpx("non-existent-path", str(storage_dir))
    assert len(result["imported"]) == 0
    assert "Source path does not exist" in result["errors"]["non-existent-path"]


def test_import_unsupported_single_file(tmp_path):
    source_file = tmp_path / "notes.txt"
    source_file.write_text("Hello World")
    
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    
    result = import_gpx(str(source_file), str(storage_dir))
    assert len(result["imported"]) == 0
    assert result["errors"][str(source_file.absolute())] == "No supported file found"


def test_import_empty_directory(tmp_path):
    source_dir = tmp_path / "empty_dir"
    source_dir.mkdir()
    
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    
    result = import_gpx(str(source_dir), str(storage_dir))
    assert len(result["imported"]) == 0
    assert result["errors"][str(source_dir)] == "No supported file found"


def test_import_filename_collision(tmp_path):
    source_dir = tmp_path / "source"
    source_dir.mkdir()
    
    # Two source files with same name but different folders, or same content
    file_a = source_dir / "run.gpx"
    file_a.write_text(VALID_GPX_TEMPLATE.format(timestamp="2026-06-30T10:00:00Z"))
    
    storage_dir = tmp_path / "storage"
    storage_dir.mkdir()
    
    # First import
    result1 = import_gpx(str(file_a), str(storage_dir))
    assert len(result1["imported"]) == 1
    assert Path(result1["imported"][0]).name == "run.gpx"
    
    # Second import of the same file (or another file with same name to same YYYY/MM)
    result2 = import_gpx(str(file_a), str(storage_dir))
    assert len(result2["imported"]) == 1
    assert Path(result2["imported"][0]).name == "run_1.gpx"
    assert Path(result2["imported"][0]).exists()
