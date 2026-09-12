#!/usr/bin/env bash
###########################################################################
# CyberYukti — run the entire project with one script.
#
# Usage:
#   ./start.sh            # dev mode (default): FastAPI :8000 + Next.js :3000
#   ./start.sh dev        # same as above
#   ./start.sh prod       # static-export frontend, served by the backend on :8000
#   ./start.sh backend    # backend only on :8000
#   ./start.sh frontend   # frontend dev server only on :3000
#   ./start.sh build      # build frontend (static export) only, no servers
#
# Ports can be overridden: PORT=9000 ./start.sh dev
###########################################################################
set -euo pipefail

# Always run from the repo root (directory containing this script)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

MODE="${1:-dev}"
BACKEND_PORT="${PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

log()  { printf '\033[1;36m[start.sh]\033[0m %s\n' "$*"; }
fail() { printf '\033[1;31m[start.sh] ERROR:\033[0m %s\n' "$*" >&2; exit 1; }

# --- Preflight: required tools ---------------------------------------------
command -v python >/dev/null 2>&1 || command -v python3 >/dev/null 2>&1 \
  || fail "Python 3.11+ is required (https://www.python.org/)"
command -v node >/dev/null 2>&1 || fail "Node.js 20+ is required (https://nodejs.org/)"

PYTHON_BIN="$(command -v python3 || command -v python)"

# --- Backend setup -----------------------------------------------------------
setup_backend() {
  log "Checking backend dependencies..."
  if ! "$PYTHON_BIN" -c "import fastapi, uvicorn, pydantic" >/dev/null 2>&1; then
    log "Installing backend dependencies (pip install -r requirements.txt)..."
    "$PYTHON_BIN" -m pip install -r requirements.txt \
      "httpx>=0.25.0" "python-dotenv>=1.0.0" || fail "Backend dependency install failed"
  fi
}

run_backend() {
  setup_backend
  log "Starting backend API on http://localhost:${BACKEND_PORT} (docs at /docs)"
  PORT="$BACKEND_PORT" "$PYTHON_BIN" run_server.py
}

# --- Frontend setup ----------------------------------------------------------
setup_frontend() {
  command -v npm >/dev/null 2>&1 || fail "npm is required for the frontend"
  cd "$ROOT_DIR/frontend"
  if [ ! -d node_modules ]; then
    log "Installing frontend dependencies (npm ci)..."
    npm ci || fail "Frontend dependency install failed"
  fi
  cd "$ROOT_DIR"
}

run_frontend_dev() {
  setup_frontend
  log "Starting frontend dev server on http://localhost:${FRONTEND_PORT}"
  cd "$ROOT_DIR/frontend"
  NEXT_PUBLIC_API_URL="${NEXT_PUBLIC_API_URL:-http://localhost:${BACKEND_PORT}}" \
    npm run dev -- --port "$FRONTEND_PORT"
}

# Prod: static export (like the Docker image), then serve from FastAPI
build_static_frontend() {
  setup_frontend
  log "Building static frontend export (BUILD_STATIC_EXPORT=true)..."
  cd "$ROOT_DIR/frontend"
  BUILD_STATIC_EXPORT=true NEXT_PUBLIC_USE_MOCK="${NEXT_PUBLIC_USE_MOCK:-true}" \
    npm run build || fail "Frontend static build failed"
  cd "$ROOT_DIR"
  log "Copying frontend/out -> backend/static-ui"
  rm -rf "$ROOT_DIR/backend/static-ui"
  cp -r "$ROOT_DIR/frontend/out" "$ROOT_DIR/backend/static-ui"
  cd "$ROOT_DIR"
}

run_prod() {
  build_static_frontend
  log "Serving UI + API from a single process on http://localhost:${BACKEND_PORT}"
  PORT="$BACKEND_PORT" USE_MOCK_AI="${USE_MOCK_AI:-true}" \
    "$PYTHON_BIN" run_cyberyukti.py
}

# --- Mode dispatch ------------------------------------------------------------
case "$MODE" in
  build)
    build_static_frontend
    log "Static build complete: frontend/out (copied to backend/static-ui)"
    ;;
  backend)
    trap 'kill 0' EXIT INT TERM
    run_backend
    ;;
  frontend)
    trap 'kill 0' EXIT INT TERM
    run_frontend_dev
    ;;
  prod)
    trap 'kill 0' EXIT INT TERM
    run_prod
    ;;
  dev)
    setup_backend
    setup_frontend
    trap 'kill 0' EXIT INT TERM
    log "Dev mode: backend on :${BACKEND_PORT}, frontend on :${FRONTEND_PORT}"
    log "Press Ctrl+C to stop both."
    run_backend &
    BACKEND_PID=$!
    # Wait for the backend health endpoint before starting the frontend
    for _ in $(seq 1 30); do
      if curl -sf "http://localhost:${BACKEND_PORT}/api/health" >/dev/null 2>&1; then
        break
      fi
      sleep 1
    done
    run_frontend_dev &
    FRONTEND_PID=$!
    log "Open http://localhost:${FRONTEND_PORT} (API docs: http://localhost:${BACKEND_PORT}/docs)"
    wait "$BACKEND_PID" "$FRONTEND_PID"
    ;;
  *)
    fail "Unknown mode: $MODE (use: dev | prod | backend | frontend | build)"
    ;;
esac
