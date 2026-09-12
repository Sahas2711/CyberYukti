# ==============================================================================
# CyberYukti - Single Unified Production Container
# Multi-stage build combining Python 3.11 FastAPI Backend & Next.js 14 Frontend
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Frontend Assets
# ------------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

# Copy package descriptors and install dependencies
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

# Copy frontend source and build Next.js production bundle
COPY frontend/ ./
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Final Runtime Image (Python 3.11 + Node.js 20)
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS runner

LABEL maintainer="CyberYukti Team"
LABEL description="Autonomous Vulnerability Triage & Evidence Engine (PS16)"

WORKDIR /app

# Install system dependencies, curl, and Node.js 20 runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python backend dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend, services, fixtures, and runners
COPY backend/ ./backend/
COPY services/ ./services/
COPY docs/ ./docs/
COPY run_server.py run_standalone.py ./
COPY docker-entrypoint.sh ./
RUN chmod +x ./docker-entrypoint.sh

# Copy built frontend application and node_modules from builder
COPY --from=frontend-builder /app/frontend/package.json ./frontend/package.json
COPY --from=frontend-builder /app/frontend/package-lock.json ./frontend/package-lock.json
COPY --from=frontend-builder /app/frontend/node_modules ./frontend/node_modules
COPY --from=frontend-builder /app/frontend/.next ./frontend/.next
COPY --from=frontend-builder /app/frontend/public ./frontend/public
COPY --from=frontend-builder /app/frontend/next.config.js ./frontend/next.config.js

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Expose ports: 8000 (Backend API & Swagger) and 3000 (Frontend Web UI)
EXPOSE 8000 3000

# Container Healthcheck (verifies backend availability)
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -f http://localhost:8000/ || exit 1

# Launch unified entrypoint
ENTRYPOINT ["/bin/sh", "/app/docker-entrypoint.sh"]
