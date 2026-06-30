import os
import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
import re
from pathlib import Path
import logging
from typing import TypedDict, Dict, List

logger = logging.getLogger(__name__)


class ImportResult(TypedDict):
    imported: List[str]
    errors: Dict[str, str]


class InvalidTimestampError(ValueError):
    """Exception raised when a GPX timestamp is invalid."""
    def __init__(self, message: str, raw_value: str):
        super().__init__(f"{message}: '{raw_value}'")
        self.raw_value = raw_value
    
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

    # [1] only look into tkrpt and rtept do not look elsewhere
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

   #  [2] use custom exception here and add the filename
   # [3] does it make sense to log in here?
    raise ValueError("No timestamp found")


def parse_year_month(time_str: str) -> tuple[str, str]:
    """Parses year and month from a GPX timestamp string.

    Currently expecting a ISO 8601 timestamp"""


    # datetime.fromisoformat supports Z natively starting with Python 3.11.
    # Manual replacement is kept to support older Python versions.
    t_str = time_str.strip()
    if t_str.endswith('Z'):
        t_str = t_str[:-1] + '+00:00'

    try:
        dt = datetime.fromisoformat(t_str)
        return f"{dt.year:04d}", f"{dt.month:02d}"
    except ValueError as e:
        raise InvalidTimestampError("Invalid timestamp format", time_str) from e


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
            logger.debug("Filename collision for '%s' in '%s'. Renaming to '%s'", filename, target_dir, new_name)
            return new_dest
        counter += 1


def save_to_storage(file_path: Path, storage_path: Path, year: str, month: str) -> Path:
    """Creates the target directory structure and copies the file to the destination.
    
    Returns:
        The Path to the copied file.
    """
    target_dir = storage_path / year / month
    target_dir.mkdir(parents=True, exist_ok=True)

    # [4] first call a function to check if the file exist
    # if it exist check if the hash of the file is identical. If so return an error that the file si already in in storage
    # if there is a name collision but the file content is different, then add a suffix. as it happen now
    
    dest_path = get_unique_path(target_dir, file_path.name)
    shutil.copy2(file_path, dest_path)
    return dest_path


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

    # [5] move the preparation of the file list in a separate function
    # Check if source exists
    if not source_path.exists():
        logger.error("Source path does not exist: '%s'", source)
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
            logger.warning("No supported file found in source directory: '%s'", source)
            result["errors"][source] = "No supported file found"
            return result
    else:
        logger.error("Unsupported source path type for: '%s'", source)
        result["errors"][source] = "Unsupported source path type"
        return result

    # Process each file
    for file_path in files_to_process:
        # [6] create a separate function that import a single file
        src_str = str(file_path.absolute())
        
        # Verify file extension (if file was explicitly passed and not .gpx)
        if file_path.suffix.lower() != ".gpx":
            logger.warning("File is not a GPX file (missing .gpx suffix): '%s'", src_str)
            result["errors"][src_str] = "No supported file found"
            continue

        try:
            timestamp = extract_first_timestamp(file_path)
            year, month = parse_year_month(timestamp)
        except ValueError as e:
            logger.warning("Failed to parse timestamp in '%s': %s", src_str, e)
            result["errors"][src_str] = str(e)
            continue
        except Exception as e:
            logger.warning("Error parsing file '%s': %s", src_str, e)
            result["errors"][src_str] = f"Error parsing file: {str(e)}"
            continue

        # [7] make this a separate function 
        try:
            dest_path = save_to_storage(file_path, storage_path, year, month)
            logger.info("Successfully imported '%s' -> '%s'", src_str, dest_path)
            result["imported"].append(str(dest_path.absolute()))
        except Exception as e:
            logger.error("Failed to copy file '%s' to storage: %s", src_str, e)
            result["errors"][src_str] = f"Failed to copy file to storage: {str(e)}"

    return result
