"""Port Check Probe.

Executes non-destructive TCP connectivity checks against allowlisted lab targets.
Enforces target allowlist and allowed_ports whitelist to prevent arbitrary network/port scanning.
"""

import socket
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from config import CONNECT_TIMEOUT_SECONDS
    from models import CanonicalFinding, InvalidInputException
    from validator.target_registry import is_port_allowed
except ImportError:
    from ..config import CONNECT_TIMEOUT_SECONDS
    from ..models import CanonicalFinding, InvalidInputException
    from ..validator.target_registry import is_port_allowed


def run_port_check_probe(
    finding: CanonicalFinding,
    target_config: Dict[str, Any],
) -> Tuple[str, Dict[str, Any], str]:
    """Execute PORT_CHECK probe with port whitelist enforcement.

    Returns (execution_status, observed_data, error_detail).
    """
    raw_port = finding.location.port
    if raw_port is None:
        raise InvalidInputException("Port check requires a valid port number.")

    try:
        port = int(raw_port)
    except (ValueError, TypeError):
        raise InvalidInputException(f"Invalid port specification: '{raw_port}'. Must be an integer.")

    if port < 1 or port > 65535:
        raise InvalidInputException(f"Port number {port} is out of valid range (1-65535).")

    # Guardrail: port must be in target's allowed_ports whitelist
    asset_id = finding.asset.id
    if not is_port_allowed(asset_id, port):
        raise InvalidInputException(
            f"Port {port} is not in the allowed_ports whitelist for asset '{asset_id}'."
        )

    # Host derived strictly from target registry
    host = target_config.get("host")
    if not host:
        return "TARGET_UNAVAILABLE", {}, f"No valid host registered for asset '{asset_id}'"

    # Perform safe TCP connection check
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(CONNECT_TIMEOUT_SECONDS)

    try:
        result = sock.connect_ex((host, port))
        if result == 0:
            state = "OPEN"
        else:
            state = "CLOSED"

        observed = {
            "host": host,
            "port": port,
            "state": state,
            "raw_result": result,
        }
        return "SUCCESS", observed, ""
    except socket.timeout:
        observed = {
            "host": host,
            "port": port,
            "state": "TIMEOUT",
        }
        return "TIMEOUT", observed, f"TCP connection to {host}:{port} timed out"
    except Exception as exc:
        observed = {
            "host": host,
            "port": port,
            "state": "ERROR",
        }
        return "ERROR", observed, f"TCP socket error on {host}:{port}: {str(exc)}"
    finally:
        sock.close()
