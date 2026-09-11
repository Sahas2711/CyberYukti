"""Configuration module for Evidence Validation Engine.

Defines timeouts, sandbox resource limits, lab root directory, and payload bounds.
"""

import os
from pathlib import Path

# Base directory for the evidence engine service
BASE_DIR = Path(__file__).resolve().parent

# Lab root directory (contains vulnerable and patched target environments)
LAB_ROOT_DIR = (BASE_DIR / "lab").resolve()

# Timeouts (seconds)
PROBE_TIMEOUT_SECONDS: float = float(os.getenv("PROBE_TIMEOUT_SECONDS", "5.0"))
CONNECT_TIMEOUT_SECONDS: float = float(os.getenv("CONNECT_TIMEOUT_SECONDS", "2.0"))

# Request and output size boundaries
MAX_PAYLOAD_SIZE_BYTES: int = int(os.getenv("MAX_PAYLOAD_SIZE_BYTES", "65536"))  # 64 KB
MAX_OUTPUT_BYTES: int = int(os.getenv("MAX_OUTPUT_BYTES", "10000"))  # 10 KB

# Docker sandbox configuration
DOCKER_IMAGE: str = os.getenv("DOCKER_IMAGE", "python:3.12-slim")
DOCKER_USER: str = os.getenv("DOCKER_USER", "10001:10001")
DOCKER_NETWORK: str = os.getenv("DOCKER_NETWORK", "lab-net")
DOCKER_CPUS: str = os.getenv("DOCKER_CPUS", "0.5")
DOCKER_MEMORY: str = os.getenv("DOCKER_MEMORY", "256m")
DOCKER_SECURITY_OPT: str = "no-new-privileges"
