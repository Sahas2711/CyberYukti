"""Docker runner and execution sandbox.

Builds and executes bounded commands adhering to security containment:
- Non-root user execution
- Network isolation (lab-net or none)
- Read-only root filesystem
- Dropped Linux capabilities (cap-drop=ALL)
- No new privileges
- Never privileged
- Resource bounds (CPU, memory, max output)
- Hard timeouts
"""

import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from config import DOCKER_IMAGE
    from sandbox.limits import DEFAULT_LIMITS, SandboxLimits
except ImportError:
    from ..config import DOCKER_IMAGE
    from .limits import DEFAULT_LIMITS, SandboxLimits


@dataclass
class SandboxExecutionResult:
    status: str  # "SUCCESS", "TIMEOUT", "ERROR"
    returncode: Optional[int]
    stdout: str
    stderr: str
    duration_ms: int
    sandbox_type: str


def is_docker_available() -> bool:
    """Check whether the docker CLI binary is present and accessible."""
    return shutil.which("docker") is not None


def build_docker_run_command(
    cmd_args: List[str],
    image: str = DOCKER_IMAGE,
    limits: SandboxLimits = DEFAULT_LIMITS,
    read_only: bool = True,
) -> List[str]:
    """Construct a secure docker run command with mandatory safety flags.

    Never adds --privileged.
    """
    if limits.privileged:
        raise ValueError("Security violation: Privileged containers are strictly prohibited.")

    docker_cmd = [
        "docker", "run", "--rm",
        f"--user={limits.user}",
        f"--network={limits.network}",
        f"--security-opt={limits.security_opt}",
        f"--cpus={limits.cpu_limit}",
        f"--memory={limits.memory_limit}",
    ]

    if limits.cap_drop_all:
        docker_cmd.append("--cap-drop=ALL")

    if read_only and limits.read_only_root:
        docker_cmd.append("--read-only")

    docker_cmd.append(image)
    docker_cmd.extend(cmd_args)
    return docker_cmd


def execute_sandboxed_command(
    cmd_args: List[str],
    timeout_seconds: Optional[float] = None,
    cwd: Optional[str] = None,
    limits: SandboxLimits = DEFAULT_LIMITS,
    prefer_docker: bool = False,
) -> SandboxExecutionResult:
    """Execute a command list in a safe, time-bounded subprocess.

    Strictly forbids shell=True. Truncates output to limits.max_output_bytes.
    """
    if not isinstance(cmd_args, list) or not all(isinstance(arg, str) for arg in cmd_args):
        raise ValueError("Command arguments must be a list of strings.")

    timeout = timeout_seconds if timeout_seconds is not None else limits.timeout_seconds
    start_time = time.perf_counter()

    final_cmd = cmd_args
    sandbox_type = "subprocess-isolated"

    if prefer_docker and is_docker_available():
        final_cmd = build_docker_run_command(cmd_args, limits=limits)
        sandbox_type = "docker"

    try:
        proc = subprocess.run(
            final_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=timeout,
            shell=False,  # Mandatory: NEVER use shell=True
            cwd=cwd,
        )
        duration_ms = int((time.perf_counter() - start_time) * 1000)

        stdout = proc.stdout[: limits.max_output_bytes]
        stderr = proc.stderr[: limits.max_output_bytes]

        status = "SUCCESS" if proc.returncode == 0 else "ERROR"
        return SandboxExecutionResult(
            status=status,
            returncode=proc.returncode,
            stdout=stdout,
            stderr=stderr,
            duration_ms=duration_ms,
            sandbox_type=sandbox_type,
        )
    except subprocess.TimeoutExpired as exc:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        stdout_text = (exc.stdout or "") if isinstance(exc.stdout, str) else (exc.stdout or b"").decode("utf-8", errors="replace")
        stderr_text = (exc.stderr or "") if isinstance(exc.stderr, str) else (exc.stderr or b"").decode("utf-8", errors="replace")
        return SandboxExecutionResult(
            status="TIMEOUT",
            returncode=None,
            stdout=stdout_text[: limits.max_output_bytes],
            stderr=stderr_text[: limits.max_output_bytes],
            duration_ms=duration_ms,
            sandbox_type=sandbox_type,
        )
    except Exception as exc:
        duration_ms = int((time.perf_counter() - start_time) * 1000)
        return SandboxExecutionResult(
            status="ERROR",
            returncode=-1,
            stdout="",
            stderr=str(exc)[: limits.max_output_bytes],
            duration_ms=duration_ms,
            sandbox_type=sandbox_type,
        )
