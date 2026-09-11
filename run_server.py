"""CyberYukti Backend Server Launcher with Dual-Stack (IPv4 + IPv6) support for instant Windows responses."""

import os
import socket
import sys
from pathlib import Path
import uvicorn

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.main import app


def create_dual_stack_socket(host: str = "::", port: int = 8000) -> socket.socket:
    """Creates a dual-stack socket that accepts both IPv4 and IPv6 traffic without delays."""
    try:
        sock = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
        # Enable dual-stack (allow IPv4-mapped IPv6 addresses)
        sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.listen(128)
        return sock
    except Exception:
        # Fallback to standard IPv4 socket if IPv6 is unavailable
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(("0.0.0.0", port))
        sock.listen(128)
        return sock


def main():
    port = int(os.environ.get("PORT", 8000))
    sock = create_dual_stack_socket("::", port)

    print(f"[*] CyberYukti API starting on http://localhost:{port} & http://127.0.0.1:{port}")
    print(f"[*] Swagger Documentation available at: http://localhost:{port}/docs")

    config = uvicorn.Config(
        app=app,
        log_level="info",
        access_log=True,
    )
    server = uvicorn.Server(config)
    server.run(sockets=[sock])


if __name__ == "__main__":
    main()
