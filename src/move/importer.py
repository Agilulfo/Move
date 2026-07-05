import shutil
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import logging
from typing import TypedDict, Dict, List

logger = logging.getLogger(__name__)


class ImportResult(TypedDict):
    imported: List[str]
    errors: Dict[str, str]


class InvalidTimestampError(ValueError):
    """Exception raised when a GPX timestamp is invalid."""

    def __init__(self, raw_value: str):
        super().__init__(f"The timestamp found is not supported: '{raw_value}'")
        self.raw_value = raw_value


class InvalidPath(ValueError):
    def __init__(self, path: Path):
        super().__init__(f"The path: {Path} is not valid.")
        self.path = path


class InvalidGpxFile(Exception):
    def __init__(self, path: Path):
        super().__init__(f"The file: {Path} is not valid.")
        self.path = path


class GPXTimestampNotFoundError(ValueError):
    """Exception raised when no timestamp is found in a GPX file."""

    def __init__(self, filepath: Path):
        super().__init__(f"No timestamp could be located in: {filepath}")
        self.filepath = filepath


def extract_first_timestamp(gpx_path: Path) -> str:
    """Extracts the first timestamp found in a GPX file."""
    try:
        tree = ET.parse(gpx_path)
        root = tree.getroot()
    except ET.ParseError as e:
        raise ValueError("Corrupted file") from e

    def local_name(elem) -> str:
        return elem.tag.split("}")[-1]

    for elem in root.iter():
        if local_name(elem) in ["trkpt", "rtept"]:
            for child in elem:
                if local_name(child) == "time" and child.text:
                    val = child.text.strip()
                    if val:
                        return val

    raise GPXTimestampNotFoundError(gpx_path)


def parse_year_month(time_str: str) -> tuple[str, str]:
    """Parses year and month from a GPX timestamp string.

    Currently expecting a ISO 8601 timestamp"""

    # datetime.fromisoformat supports Z natively starting with Python 3.11.
    # Manual replacement is kept to support older Python versions.
    t_str = time_str.strip()
    if t_str.endswith("Z"):
        t_str = t_str[:-1] + "+00:00"

    try:
        dt = datetime.fromisoformat(t_str)
        return f"{dt.year:04d}", f"{dt.month:02d}"
    except ValueError as e:
        raise InvalidTimestampError(time_str) from e


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
            logger.debug(
                "Filename collision for '%s' in '%s'. Renaming to '%s'",
                filename,
                target_dir,
                new_name,
            )
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


def has_gpx_extension(path):
    return path.is_file() and path.suffix.lower() == ".gpx"


def list_gpx_files(source_path: Path) -> List[Path]:
    if not source_path.exists():
        raise InvalidPath(source_path)

    if has_gpx_extension(source_path):
        return [source_path]
    elif source_path.is_dir():
        return [p for p in source_path.glob("*") if has_gpx_extension(p)]
    else:
        raise InvalidGpxFile(source_path)
    return []


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

    if not source_path.exists():
        logger.error("Source path does not exist: '%s'", source)
        result["errors"][source] = "Source path does not exist"
    try:
        files_to_process = list_gpx_files(source_path)

    except InvalidPath:
        logger.warning(f"the provided path is invalid: {source}")
        result["errors"][source] = "Invalid Path"
        return result

    if not files_to_process:
        logger.warning(f"No valid files found in: {source}")
        result["errors"][source] = "No supported file found"
        return result

    # Process each file
    for file_path in files_to_process:
        try:
            timestamp = extract_first_timestamp(file_path)
            year, month = parse_year_month(timestamp)
            dest_path = save_to_storage(file_path, storage_path, year, month)
            logger.info("Successfully imported '%s' -> '%s'", file_path, dest_path)
            result["imported"].append(str(dest_path.absolute()))
        except (GPXTimestampNotFoundError, ValueError) as e:
            logger.warning("Failed to parse timestamp in '%s': %s", file_path, e)
            result["errors"][str(file_path)] = "No timestamp found"
            continue
    return result
