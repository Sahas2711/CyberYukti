"""File Check Probe.

Performs read-only existence and size checks on files within the controlled lab environment.
Enforces strict canonicalization and path containment to prevent directory traversal attacks (e.g. ../../etc/passwd).
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from config import LAB_ROOT_DIR
    from models import CanonicalFinding, InvalidInputException
except ImportError:
    from ..config import LAB_ROOT_DIR
    from ..models import CanonicalFinding, InvalidInputException


def sanitize_and_resolve_file_path(raw_path: str, lab_root: Path) -> Path:
    """Canonicalize path and ensure it strictly resides within lab_root.

    Raises InvalidInputException on directory traversal attempts or invalid characters.
    """
    if not raw_path or not isinstance(raw_path, str):
        raise InvalidInputException("File path must be a non-empty string.")

    # Check for null bytes or illegal characters
    if "\x00" in raw_path or "\r" in raw_path or "\n" in raw_path:
        raise InvalidInputException("File path contains illegal control characters.")

    clean_rel = raw_path.strip().lstrip("/\\")

    # Construct target path relative to lab root
    target_path = (lab_root / clean_rel).resolve()
    resolved_root = lab_root.resolve()

    # Path traversal guardrail: verify resolved path starts with resolved lab root
    try:
        common = os.path.commonpath([str(target_path), str(resolved_root)])
        if common != str(resolved_root):
            raise InvalidInputException(
                f"Directory traversal detected: path '{raw_path}' escapes lab root boundaries."
            )
    except ValueError:
        # Handles Windows drive mismatch or path resolution errors
        raise InvalidInputException(
            f"Invalid path traversal: path '{raw_path}' is outside lab root."
        )

    return target_path


def run_file_check_probe(
    finding: CanonicalFinding,
    target_config: Dict[str, Any],
) -> Tuple[str, Dict[str, Any], str]:
    """Execute FILE_EXISTS probe on controlled target.

    Returns (execution_status, observed_data, error_detail).
    """
    raw_path = finding.location.path
    if not raw_path:
        raise InvalidInputException("File check requires a location path.")

    # Target lab root
    lab_path_str = target_config.get("lab_path")
    lab_root = Path(lab_path_str) if lab_path_str else LAB_ROOT_DIR

    # Canonicalize and verify containment (raises InvalidInputException if it escapes)
    resolved_file = sanitize_and_resolve_file_path(raw_path, lab_root)

    exists = resolved_file.is_file()
    size = resolved_file.stat().st_size if exists else 0

    observed = {
        "path": raw_path,
        "resolved_path": str(resolved_file),
        "exists": exists,
        "size_bytes": size,
    }
    return "SUCCESS", observed, ""
