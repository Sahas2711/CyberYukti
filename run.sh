#!/usr/bin/env bash
# =================================================================
# CyberYukti - Unified Project Launcher
# Starts both FastAPI Backend (port 8000) & Next.js Frontend (port 3000)
# =================================================================

set -e

# Resolve repository root directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load environment variables if .env exists
if [ -f "$SCRIPT_DIR/.env" ]; then
  set -a
  # shellcheck disable=SC1091
  source "$SCRIPT_DIR/.env"
  set +a
fi

BACKEND_PORT="${PORT:-8000}"

# Detect Python command
if command -v python3 >/dev/null 2>&1; then
  PYTHON_CMD="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_CMD="python"
else
  echo "[!] Error: Neither python3 nor python found in PATH." >&2
  exit 1
fi

# Detect npm command
if ! command -v npm >/dev/null 2>&1; then
  echo "[!] Error: npm not found in PATH. Please install Node.js." >&2
  exit 1
fi

echo "================================================================="
echo "  Starting CyberYukti Platform                                   "
echo "  Backend API:      http://localhost:${BACKEND_PORT}             "
echo "  Swagger Docs:     http://localhost:${BACKEND_PORT}/docs        "
echo "  Frontend Web UI:  http://localhost:3000                        "
echo "================================================================="

# Ensure frontend dependencies are installed if missing
if [ ! -d "$SCRIPT_DIR/frontend/node_modules" ]; then
  echo "[*] node_modules not found in frontend. Installing dependencies..."
  (cd "$SCRIPT_DIR/frontend" && npm install)
fi

# Cleanup handler for graceful shutdown on Ctrl+C or kill
cleanup() {
  trap - INT TERM EXIT
  echo ""
  echo "[*] Shutting down CyberYukti services..."
  if [ -n "$BACKEND_PID" ]; then
    kill "$BACKEND_PID" 2>/dev/null || true
  fi
  if [ -n "$FRONTEND_PID" ]; then
    kill "$FRONTEND_PID" 2>/dev/null || true
  fi
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  echo "[*] All services stopped cleanly."
  exit 0
}

trap cleanup INT TERM EXIT

# Start Backend API Server
echo "[*] Launching Backend API server on port ${BACKEND_PORT}..."
"$PYTHON_CMD" "$SCRIPT_DIR/run_server.py" &
BACKEND_PID=$!

# Start Frontend Dev Server
echo "[*] Launching Next.js Frontend on port 3000..."
(cd "$SCRIPT_DIR/frontend" && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "[+] CyberYukti is running!"
echo "    - Backend:  http://localhost:${BACKEND_PORT}"
echo "    - Docs:     http://localhost:${BACKEND_PORT}/docs"
echo "    - Frontend: http://localhost:3000"
echo ""
echo "[i] Press Ctrl+C at any time to stop all services."
echo ""

# Keep running and wait for background jobs
wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || wait
