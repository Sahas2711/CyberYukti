#!/bin/sh
set -e

echo "=========================================================="
echo " Starting CyberYukti Autonomous Triage & Evidence Engine  "
echo " Backend API:     http://0.0.0.0:8000                     "
echo " Frontend Web UI: http://0.0.0.0:3000                     "
echo " Docs (Swagger):  http://0.0.0.0:8000/docs                "
echo "=========================================================="

# Start backend server in the background on internal port 8000
PORT=8000 python run_server.py &
BACKEND_PID=$!

# Start frontend server in the background (default port 3000)
FRONTEND_PORT=${FRONTEND_PORT:-3000}
cd /app/frontend && npm start -- -p "$FRONTEND_PORT" &
FRONTEND_PID=$!

# Trap termination signals to gracefully stop both processes
cleanup() {
  echo "Received termination signal. Shutting down CyberYukti..."
  kill -TERM "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  wait "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
  exit 0
}

trap cleanup INT TERM

# Wait for any process to exit
wait -n "$BACKEND_PID" "$FRONTEND_PID"
