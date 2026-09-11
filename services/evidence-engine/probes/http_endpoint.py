"""HTTP Endpoint Probe.

Performs safe, non-destructive GET/HEAD requests against controlled lab targets only.
Enforces SSRF boundary: host is strictly derived from target registry.
Never follows redirects, never sends exploits.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import httpx

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from config import CONNECT_TIMEOUT_SECONDS, PROBE_TIMEOUT_SECONDS
    from models import CanonicalFinding, InvalidInputException
except ImportError:
    from ..config import CONNECT_TIMEOUT_SECONDS, PROBE_TIMEOUT_SECONDS
    from ..models import CanonicalFinding, InvalidInputException


def sanitize_endpoint_path(endpoint_path: Optional[str]) -> str:
    """Sanitize and normalize endpoint path.

    Prevents SSRF protocol smuggling or host redirection inside path strings.
    """
    if not endpoint_path or not isinstance(endpoint_path, str):
        return "/"

    raw = endpoint_path.strip()

    # Reject attempts to smuggle protocol or alternate host in the path
    lower = raw.lower()
    if lower.startswith("http://") or lower.startswith("https://") or lower.startswith("//"):
        raise InvalidInputException("Endpoint path cannot specify arbitrary host or scheme.")

    if "\x00" in raw or "\r" in raw or "\n" in raw:
        raise InvalidInputException("Endpoint path contains illegal control characters.")

    # Ensure leading slash
    if not raw.startswith("/"):
        raw = "/" + raw

    return raw


def run_http_endpoint_probe(
    finding: CanonicalFinding,
    target_config: Dict[str, Any],
) -> Tuple[str, Dict[str, Any], str]:
    """Execute HTTP_ENDPOINT probe against an allowlisted lab target.

    Returns (execution_status, observed_data, error_detail).
    """
    # Host comes strictly from target registry, NEVER from untrusted finding
    host = target_config.get("host")
    if not host:
        return "TARGET_UNAVAILABLE", {}, "Target asset has no registered host"

    # Select port: default to first allowed port or 8080
    allowed_ports = target_config.get("allowed_ports", [8080])
    target_port = allowed_ports[0] if allowed_ports else 8080

    raw_path = finding.location.endpoint or finding.location.path or "/"
    try:
        path = sanitize_endpoint_path(raw_path)
    except InvalidInputException as e:
        raise e

    target_url = f"http://{host}:{target_port}{path}"

    timeout = httpx.Timeout(
        timeout=PROBE_TIMEOUT_SECONDS,
        connect=CONNECT_TIMEOUT_SECONDS,
    )

    try:
        # Mandatory safety flags: follow_redirects=False, GET only
        with httpx.Client(follow_redirects=False, timeout=timeout) as client:
            resp = client.get(target_url, headers={"User-Agent": "Evidence-Validation-Engine/1.0"})
            observed = {
                "url": path,
                "full_url": target_url,
                "reachable": True,
                "status_code": resp.status_code,
                "headers": dict(resp.headers),
            }
            return "SUCCESS", observed, ""
    except (httpx.ConnectTimeout, httpx.ReadTimeout, httpx.WriteTimeout, httpx.PoolTimeout):
        observed = {
            "url": path,
            "reachable": False,
            "status_code": None,
        }
        return "TIMEOUT", observed, f"Connection to {target_url} timed out"
    except (httpx.ConnectError, httpx.NetworkError):
        observed = {
            "url": path,
            "reachable": False,
            "status_code": None,
        }
        return "TARGET_UNAVAILABLE", observed, f"Target service at {target_url} is unreachable or offline"
    except Exception as exc:
        observed = {
            "url": path,
            "reachable": False,
            "status_code": None,
        }
        return "ERROR", observed, f"HTTP probe error: {str(exc)}"
