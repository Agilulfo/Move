import os
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
import re
from pathlib import Path
from typing import TypedDict, Dict, List

class ImportResult(TypedDict):
    imported: List[str]
    errors: Dict[str, str]


def extract_first_timestamp(gpx_path: Path) -> str:
    """Extracts the first timestamp found in a GPX file.
    
    Looks in trkpt elements first, then rtept, wpt, and fallback to any time elements.
    Raises ValueError if file is corrupted or no timestamp is found.
    """
    try:
        tree = ET.parse(gpx_path)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError("Corrupted file") from e

    def local_name(elem) -> str:
        return elem.tag.split('}')[-1]

    # 1. Search for first trkpt time
    for elem in root.iter():
        if local_name(elem) == 'trkpt':
            for child in elem:
                if local_name(child) == 'time' and child.text:
                    val = child.text.strip()
                    if val:
                        return val

    # 2. Search for first rtept time
    for elem in root.iter():
        if local_name(elem) == 'rtept':
            for child in elem:
                if local_name(child) == 'time' and child.text:
                    val = child.text.strip()
                    if val:
                        return val

    # 3. Search for first wpt time
    for elem in root.iter():
        if local_name(elem) == 'wpt':
            for child in elem:
                if local_name(child) == 'time' and child.text:
                    val = child.text.strip()
                    if val:
                        return val

    # 4. Search for any time element
    for elem in root.iter():
        if local_name(elem) == 'time' and elem.text:
            val = elem.text.strip()
            if val:
                return val

    raise ValueError("No timestamp found")


def parse_year_month(time_str: str) -> tuple[str, str]:
    """Parses year and month from a GPX timestamp string."""
    t_str = time_str.strip()
    if t_str.endswith('Z'):
        t_str = t_str[:-1] + '+00:00'

    try:
        dt = datetime.fromisoformat(t_str)
        return f"{dt.year:04d}", f"{dt.month:02d}"
    except ValueError:
        pass

    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(t_str, fmt)
            return f"{dt.year:04d}", f"{dt.month:02d}"
        except ValueError:
            continue

    # Regex fallback for YYYY-MM prefix
    match = re.match(r'^(\d{4})-(\d{2})', t_str)
    if match:
        year, month = match.group(1), match.group(2)
        if 1 <= int(month) <= 12:
            return year, month

    raise ValueError("Invalid timestamp format")


def get_unique_path(target_dir: Path, filename: str) -> Path:
    """Generates a unique path in the target directory to avoid overwriting existing files."""
    dest = target_dir / filename
    if not dest.exists():
        return dest
        
    stem = dest.stem
    suffix = dest.suffix
    counter = 1
    while True:
        new_name = f"{stem}_{counter}{suffix}"
        new_dest = target_dir / new_name
        if not new_dest.exists():
            return new_dest
        counter += 1


def import_gpx(source: str, storage: str) -> ImportResult:
    """Imports GPX files from a file or directory into a storage path.
    
    Files are copied into storage/YEAR/MONTH/ subfolders based on their first timestamp.
    
    Returns:
        A dictionary containing:
            - 'imported': list of paths to successfully imported files in the storage.
            - 'errors': dictionary mapping source file paths to error descriptions.
    """
    result: ImportResult = {"imported": [], "errors": {}}
    
    source_path = Path(source)
    storage_path = Path(storage)
    
    # Check if source exists
    if not source_path.exists():
        result["errors"][source] = "Source path does not exist"
        return result

    # Identify all files to process
    files_to_process: List[Path] = []
    if source_path.is_file():
        files_to_process.append(source_path)
    elif source_path.is_dir():
        # Find all files with .gpx extension (case-insensitive) recursively
        for p in source_path.rglob("*"):
            if p.is_file() and p.suffix.lower() == ".gpx":
                files_to_process.append(p)
        if not files_to_process:
            result["errors"][source] = "No supported file found"
            return result
    else:
        result["errors"][source] = "Unsupported source path type"
        return result

    # Process each file
    for file_path in files_to_process:
        src_str = str(file_path.absolute())
        
        # Verify file extension (if file was explicitly passed and not .gpx)
        if file_path.suffix.lower() != ".gpx":
            result["errors"][src_str] = "No supported file found"
            continue

        try:
            timestamp = extract_first_timestamp(file_path)
            year, month = parse_year_month(timestamp)
        except ValueError as e:
            result["errors"][src_str] = str(e)
            continue
        except Exception as e:
            result["errors"][src_str] = f"Error parsing file: {str(e)}"
            continue

        try:
            # Create target subdirectory storage_path/YEAR/MONTH/
            target_dir = storage_path / year / month
            target_dir.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            dest_path = get_unique_path(target_dir, file_path.name)
            shutil.copy2(file_path, dest_path)
            
            result["imported"].append(str(dest_path.absolute()))
        except Exception as e:
            result["errors"][src_str] = f"Failed to copy file to storage: {str(e)}"

    return result
