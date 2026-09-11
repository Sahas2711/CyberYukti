# syntax=docker/dockerfile:1
###########################################################################
# CyberYukti — ONE production image: static web UI + FastAPI backend.
#
# Build:  docker build -t cyberyukti:latest .
# Run:    docker run --rm -p 8000:8000 cyberyukti:latest
#         -> UI + API on http://localhost:8000  (docs at /docs)
#
# Stage 1 builds the Next.js frontend to fully static files
# (BUILD_STATIC_EXPORT=true -> frontend/out). Stage 2 installs backend
# production dependencies and copies in the app + static UI. One process,
# one port, demo mode by default (USE_MOCK_AI=true).
###########################################################################

# --- Stage 1: build static web UI -----------------------------------------
FROM node:20-alpine AS webbuilder

WORKDIR /build/frontend

# Deterministic install from the lockfile
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
# Static export for embedding behind the FastAPI app (one image, one port);
# demo data source is baked in (safe default for the packaged demo).
RUN BUILD_STATIC_EXPORT=true NEXT_PUBLIC_USE_MOCK=true npm run build
# The static export must live at <root>/static-ui for the backend to serve it
RUN mv out /build/static-ui

# --- Stage 2: runtime -------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000 \
    USE_MOCK_AI=true

WORKDIR /app

# Backend production dependencies only (root requirements.txt lists
# pydantic/pytest/rich/fastapi/uvicorn; the runtime needs fastapi/uvicorn/
# pydantic plus the backend extras pinned in backend/pyproject.toml).
COPY requirements.txt backend/pyproject.toml ./
RUN grep -vE '^(pytest|rich)' requirements.txt > requirements.runtime.txt \
    && pip install --no-cache-dir -r requirements.runtime.txt \
    && pip install --no-cache-dir "httpx>=0.25.0" "python-dotenv>=1.0.0"

# Application code
COPY backend/ ./backend/
COPY services/ ./services/
COPY run_cyberyukti.py ./

# Packaged static UI from stage 1
COPY --from=webbuilder /build/static-ui ./static-ui

# Build metadata (overwritten by CI with real values)
ARG BUILD_VERSION=dev
ARG BUILD_COMMIT_SHA=unknown
ARG BUILD_TIMESTAMP=unknown
ENV CYBERYUKTI_VERSION=${BUILD_VERSION} \
    CYBERYUKTI_COMMIT_SHA=${BUILD_COMMIT_SHA} \
    CYBERYUKTI_BUILD_TIMESTAMP=${BUILD_TIMESTAMP} \
    CYBERYUKTI_ENV=container

# Version file where the backend's build-info endpoint looks for it
# (backend/VERSION.json, resolved relative to backend/app/main.py)
RUN printf '{"version": "%s", "commit_sha": "%s", "build_timestamp": "%s", "environment": "container"}\n' \
      "$BUILD_VERSION" "$BUILD_COMMIT_SHA" "$BUILD_TIMESTAMP" > /app/backend/VERSION.json

# Non-root user; store must be writable only where needed (in-memory app)
RUN useradd --create-home --uid 10001 cyber && chown -R cyber:cyber /app
USER cyber

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/', timeout=4).status < 500 else 1)"

# One process serves UI + API (existing run_server.py dual-stack launcher)
CMD ["python", "run_cyberyukti.py"]
