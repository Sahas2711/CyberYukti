"""CyberYukti unified launcher — serves the web UI and the API in one process.

Used by the Windows EXE (PyInstaller) and the Docker image. It starts the
existing FastAPI application (backend.app.main:app) unchanged; if a packaged
static UI exists (static-ui/), it is served on the same port.

Defaults are the safe demo configuration:
  USE_MOCK_AI=true         -> offline demo AI provider
  NEXT_PUBLIC_USE_MOCK=true -> frontend uses bundled demo data (baked in at
                              build time for the EXE)

Environment:
  PORT=8000                HTTP port
"""

import os
import sys
import tempfile
from pathlib import Path


def _project_root() -> Path:
    """Project root in dev; _MEIPASS payload dir when frozen by PyInstaller."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


def main() -> None:
    root = _project_root()
    for p in (str(root), str(root / "backend"), str(root / "services")):
        if p not in sys.path:
            sys.path.insert(0, p)

    # uvicorn[standard] uses uvloop; its loop-control setup may need a
    # writable temp dir when running as a non-root container user.
    os.environ.setdefault("TMPDIR", tempfile.gettempdir())

    from backend.app.main import app  # noqa: E402  (after sys.path setup)

    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")

    demo_mode = os.environ.get("USE_MOCK_AI", "true").lower() in ("true", "1", "yes")
    print("=" * 60)
    print("  CyberYukti — Autonomous Vulnerability Triage (PS16)")
    print("=" * 60)
    print(f"  UI + API : http://localhost:{port}")
    print(f"  API docs : http://localhost:{port}/docs")
    print(f"  Mode     : {'DEMO (mock data + mock AI)' if demo_mode else 'API-configured AI'}")
    print("  Stop     : Ctrl+C")
    print("=" * 60)

    import uvicorn

    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
