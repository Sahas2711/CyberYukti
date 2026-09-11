"""Probe registry and deterministic dispatcher.

Maps canonical finding location types strictly to safe, predefined probes.
Enforces that no LLM or arbitrary command influences probe selection.
"""

import sys
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from models import CanonicalFinding
    from probes.file_check import run_file_check_probe
    from probes.http_endpoint import run_http_endpoint_probe
    from probes.package_version import run_package_version_probe
    from probes.port_check import run_port_check_probe
except ImportError:
    from ..models import CanonicalFinding
    from ..probes.file_check import run_file_check_probe
    from ..probes.http_endpoint import run_http_endpoint_probe
    from ..probes.package_version import run_package_version_probe
    from ..probes.port_check import run_port_check_probe

ProbeFunction = Callable[[CanonicalFinding, Dict[str, Any]], Tuple[str, Dict[str, Any], str]]

# Supported registered probes
PROBES: Dict[str, ProbeFunction] = {
    "PACKAGE_VERSION": run_package_version_probe,
    "HTTP_ENDPOINT": run_http_endpoint_probe,
    "PORT_CHECK": run_port_check_probe,
    "FILE_EXISTS": run_file_check_probe,
}

# Deterministic lookup table per Section 17 (no LLM, no exceptions)
LOCATION_TYPE_TO_PROBE: Dict[str, str] = {
    "package": "PACKAGE_VERSION",
    "endpoint": "HTTP_ENDPOINT",
    "port": "PORT_CHECK",
    "file": "FILE_EXISTS",
}


def get_registered_probes() -> List[str]:
    """Return list of all registered probe names."""
    return list(PROBES.keys())


def select_probe_for_finding(finding: CanonicalFinding) -> Optional[Tuple[str, ProbeFunction]]:
    """Deterministically select probe based solely on finding.location.type.

    Returns (probe_type, probe_func) or None if unmapped.
    """
    loc_type = finding.location.type.lower() if finding.location and finding.location.type else ""
    probe_name = LOCATION_TYPE_TO_PROBE.get(loc_type)
    if not probe_name or probe_name not in PROBES:
        return None
    return probe_name, PROBES[probe_name]
