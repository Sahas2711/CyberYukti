"""Package Version Probe.

Inspects the installed version of a named package on a controlled lab target.
Enforces strict input regex sanitization, never uses shell=True, and performs
read-only metadata inspection.
"""

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from models import CanonicalFinding, InvalidInputException
    from validator.target_registry import resolve_target
except ImportError:
    from ..models import CanonicalFinding, InvalidInputException
    from ..validator.target_registry import resolve_target

# Mandatory strict regex sanitization per Section 11:
PACKAGE_NAME_REGEX = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.\-]{0,127}$")


def sanitize_package_name(package_name: str) -> str:
    """Validate package name against strict character allowlist.

    Prevents shell metacharacter injection, whitespace injection, and traversal.
    Raises InvalidInputException on violation.
    """
    if not package_name or not isinstance(package_name, str):
        raise InvalidInputException("Package name must be a non-empty string.")

    cleaned = package_name.strip()
    if not PACKAGE_NAME_REGEX.match(cleaned):
        raise InvalidInputException(
            f"Invalid package name '{cleaned}'. Must match pattern ^[A-Za-z0-9][A-Za-z0-9_.\\-]{{0,127}}$"
        )
    return cleaned


def run_package_version_probe(
    finding: CanonicalFinding,
    target_config: Dict[str, Any],
) -> Tuple[str, Dict[str, Any], str]:
    """Execute PACKAGE_VERSION probe on controlled target.

    Returns (execution_status, observed_data, error_detail).
    """
    pkg_raw = finding.location.package
    if not pkg_raw:
        return "ERROR", {}, "Finding location did not specify package name"

    # Strict sanitization: raises InvalidInputException if metacharacters present
    pkg_name = sanitize_package_name(pkg_raw)

    lab_path_str = target_config.get("lab_path")
    if not lab_path_str:
        return "TARGET_UNAVAILABLE", {}, "No lab directory configured for target asset"

    lab_path = Path(lab_path_str)
    packages_file = lab_path / "packages.json"

    if not packages_file.is_file():
        return "TARGET_UNAVAILABLE", {}, f"Target packages metadata missing at {packages_file}"

    try:
        with open(packages_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        packages_dict = data.get("packages", {})
    except Exception as exc:
        return "ERROR", {}, f"Failed to parse target package metadata: {exc}"

    if pkg_name in packages_dict:
        observed_version = packages_dict[pkg_name]
        observed = {
            "package": pkg_name,
            "version": observed_version,
            "target": finding.asset.id,
            "inspection_method": "controlled_manifest",
        }
        return "SUCCESS", observed, ""
    else:
        # Package not present on target
        observed = {
            "package": pkg_name,
            "version": None,
            "target": finding.asset.id,
            "inspection_method": "controlled_manifest",
        }
        return "SUCCESS", observed, f"Package {pkg_name} is not installed on target"
