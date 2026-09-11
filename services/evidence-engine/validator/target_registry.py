"""Target registry and lab resolution module.

Maintains strict allowlist of registered lab assets to prevent SSRF,
arbitrary port scanning, and untrusted network connections.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from config import LAB_ROOT_DIR
except ImportError:
    from ..config import LAB_ROOT_DIR

# Explicit, hardcoded lab targets registry
# Any asset not present in this dictionary MUST be rejected or marked INCONCLUSIVE.
LAB_TARGETS: Dict[str, Dict[str, Any]] = {
    "shop-api-01": {
        "host": "127.0.0.1",
        "container_name": "lab-shop-api",
        "allowed_ports": [8080, 8081],
        "network": "lab-net",
        "lab_env": "vulnerable",
        "lab_path": str(LAB_ROOT_DIR / "vulnerable"),
    },
    "shop-api-01-patched": {
        "host": "127.0.0.1",
        "container_name": "lab-shop-api-patched",
        "allowed_ports": [8080, 8081],
        "network": "lab-net",
        "lab_env": "patched",
        "lab_path": str(LAB_ROOT_DIR / "patched"),
    },
    "db-cluster-01": {
        "host": "127.0.0.1",
        "container_name": "lab-db-cluster",
        "allowed_ports": [5432],
        "network": "lab-net",
        "lab_env": "vulnerable",
        "lab_path": str(LAB_ROOT_DIR / "vulnerable"),
    },
}


def resolve_target(asset_id: str) -> Optional[Dict[str, Any]]:
    """Resolve an asset ID strictly against the controlled lab registry.

    Returns None if asset is not explicitly registered.
    """
    if not asset_id or not isinstance(asset_id, str):
        return None
    return LAB_TARGETS.get(asset_id.strip())


def is_port_allowed(asset_id: str, port: int) -> bool:
    """Verify if a specific port is permitted for the given asset."""
    target = resolve_target(asset_id)
    if not target:
        return False
    try:
        port_num = int(port)
        return port_num in target.get("allowed_ports", [])
    except (ValueError, TypeError):
        return False


def get_registered_asset_ids() -> List[str]:
    """Return list of all registered asset identifiers."""
    return list(LAB_TARGETS.keys())
