"""Deterministic Evaluator for Evidence Validation Engine.

Strictly zero-LLM: implements deterministic comparison between claimed evidence
and observed evidence, returning CONFIRMED, NOT_CONFIRMED, or INCONCLUSIVE with
auditable confidence scores and explanations.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from packaging.specifiers import InvalidSpecifier, SpecifierSet
from packaging.version import InvalidVersion, Version

try:
    from models import EvidenceClaim, ValidationStatus
except ImportError:
    from ..models import EvidenceClaim, ValidationStatus


def evaluate_evidence_match(
    expected: EvidenceClaim,
    observed: Dict[str, Any],
    probe_type: str,
) -> Tuple[bool, List[str]]:
    """Compare claimed evidence against observed target evidence.

    Returns (is_match, reason_list).
    """
    reasons = []

    if probe_type == "PACKAGE_VERSION":
        claimed = expected.claimed_version
        observed_ver = observed.get("version")

        if not observed_ver:
            return False, ["Package version could not be detected on target"]

        if not claimed:
            return False, ["No claimed version specified in finding"]

        # Exact match check
        if claimed == observed_ver:
            reasons.append(f"Observed version ({observed_ver}) strictly matches claimed version ({claimed})")
            return True, reasons

        # Check if claimed version is a semver range (e.g. '< 1.2.4', '>= 1.0.0')
        try:
            spec = SpecifierSet(claimed)
            parsed_ver = Version(observed_ver)
            if parsed_ver in spec:
                reasons.append(f"Observed version ({observed_ver}) satisfies vulnerability range specifier ({claimed})")
                return True, reasons
            else:
                reasons.append(f"Observed version ({observed_ver}) does not satisfy claimed specifier ({claimed})")
                return False, reasons
        except (InvalidSpecifier, InvalidVersion):
            # Fallback to direct string equality mismatch
            pass

        reasons.append(f"Observed version ({observed_ver}) contradicts claimed version ({claimed})")
        return False, reasons

    elif probe_type == "HTTP_ENDPOINT":
        expected_status = expected.expected_status if expected.expected_status is not None else 200
        observed_status = observed.get("status_code")
        reachable = observed.get("reachable", False)

        if not reachable:
            reasons.append("Endpoint was unreachable on target")
            return False, reasons

        if observed_status == expected_status:
            reasons.append(f"Observed HTTP status ({observed_status}) matches expected status ({expected_status})")
            return True, reasons
        else:
            reasons.append(f"Observed HTTP status ({observed_status}) contradicts expected status ({expected_status})")
            return False, reasons

    elif probe_type == "PORT_CHECK":
        expected_state = (expected.expected_state or "OPEN").upper()
        observed_state = (observed.get("state") or "UNKNOWN").upper()

        if observed_state == expected_state:
            reasons.append(f"Port state ({observed_state}) matches expected claim ({expected_state})")
            return True, reasons
        else:
            reasons.append(f"Port state ({observed_state}) contradicts expected claim ({expected_state})")
            return False, reasons

    elif probe_type == "FILE_EXISTS":
        expected_exists = True if expected.expected_exists is None else bool(expected.expected_exists)
        observed_exists = bool(observed.get("exists", False))

        if observed_exists == expected_exists:
            status_text = "exists" if observed_exists else "does not exist"
            reasons.append(f"Observed file state ({status_text}) matches finding claim")
            return True, reasons
        else:
            reasons.append(f"Observed file existence ({observed_exists}) contradicts claim ({expected_exists})")
            return False, reasons

    reasons.append(f"Unsupported probe type {probe_type} in evaluator")
    return False, reasons


def evaluate(
    expected: EvidenceClaim,
    observed: Dict[str, Any],
    execution_status: str,
    probe_type: str,
    custom_reasons: List[str] = None,
) -> Tuple[ValidationStatus, float, List[str]]:
    """Pure deterministic evaluation function.

    Computes:
    - ValidationStatus (CONFIRMED / NOT_CONFIRMED / INCONCLUSIVE)
    - Confidence score (0.0 to 1.0)
    - Structured reasons list
    """
    reasons = list(custom_reasons) if custom_reasons else []

    # If execution failed or timed out, NEVER return NOT_CONFIRMED. Must be INCONCLUSIVE.
    if execution_status != "SUCCESS":
        if execution_status == "TIMEOUT":
            reasons.append("Probe execution timed out before evidence could be gathered")
            return ValidationStatus.INCONCLUSIVE, 0.20, reasons
        elif execution_status == "TARGET_UNAVAILABLE":
            reasons.append("Target asset is unreachable, offline, or unregistered")
            return ValidationStatus.INCONCLUSIVE, 0.10, reasons
        elif execution_status == "UNSUPPORTED_PROBE":
            reasons.append("No automated probe registered for the requested location type")
            return ValidationStatus.INCONCLUSIVE, 0.30, reasons
        else:
            reasons.append(f"Probe execution completed with status: {execution_status}")
            return ValidationStatus.INCONCLUSIVE, 0.15, reasons

    # If execution succeeded, evaluate evidence match
    is_match, match_reasons = evaluate_evidence_match(expected, observed, probe_type)
    reasons.extend(match_reasons)

    if is_match:
        reasons.append("Claimed vulnerability evidence verified by controlled probe")
        return ValidationStatus.CONFIRMED, 0.96, reasons
    else:
        reasons.append("Observed evidence contradicts finding claim")
        return ValidationStatus.NOT_CONFIRMED, 0.96, reasons
