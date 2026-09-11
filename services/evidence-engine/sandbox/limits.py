"""Sandbox security limits and configuration parameters.

Enforces strict containment: non-root, read-only root, memory/CPU caps,
and hard timeouts.
"""

import sys
from dataclasses import dataclass
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from config import (
        PROBE_TIMEOUT_SECONDS,
        MAX_OUTPUT_BYTES,
        DOCKER_CPUS,
        DOCKER_MEMORY,
        DOCKER_NETWORK,
        DOCKER_USER,
        DOCKER_SECURITY_OPT,
    )
except ImportError:
    from ..config import (
        PROBE_TIMEOUT_SECONDS,
        MAX_OUTPUT_BYTES,
        DOCKER_CPUS,
        DOCKER_MEMORY,
        DOCKER_NETWORK,
        DOCKER_USER,
        DOCKER_SECURITY_OPT,
    )


@dataclass(frozen=True)
class SandboxLimits:
    timeout_seconds: float = PROBE_TIMEOUT_SECONDS
    max_output_bytes: int = MAX_OUTPUT_BYTES
    cpu_limit: str = DOCKER_CPUS
    memory_limit: str = DOCKER_MEMORY
    network: str = DOCKER_NETWORK
    user: str = DOCKER_USER
    security_opt: str = DOCKER_SECURITY_OPT
    read_only_root: bool = True
    cap_drop_all: bool = True
    privileged: bool = False


DEFAULT_LIMITS = SandboxLimits()
