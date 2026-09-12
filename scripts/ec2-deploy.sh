#!/usr/bin/env bash
###########################################################################
# ec2-deploy.sh — RUNS ON THE EC2 INSTANCE.
# Clones/pulls the GitHub repo, builds the Docker image on-instance,
# and (re)deploys the container with a real health check + rollback to
# the previously-running image. Invoked by SSM (from update-ec2.sh or
# UserData on bootstrap).
#
# Env:
#   BRANCH    git branch to deploy          (default: github-dockerhub-analysis)
#   APP_PORT  host port -> container 8000   (default: 80)
#   REPO      git remote URL                (default: https://github.com/Sahas2711/CyberYukti)
#   APP_DIR   checkout location             (default: /opt/cyberyukti)
###########################################################################
set -uo pipefail

BRANCH="${BRANCH:-github-dockerhub-analysis}"
APP_PORT="${APP_PORT:-80}"
REPO="${REPO:-https://github.com/Sahas2711/CyberYukti}"
APP_DIR="${APP_DIR:-/opt/cyberyukti}"
HEALTH="FAIL"

log() { echo "[ec2-deploy] $(date -u +%FT%TZ) $*"; }

# 0. Docker must be present
if ! command -v docker >/dev/null 2>&1; then
  dnf install -y docker && systemctl enable --now docker
fi
systemctl is-active --quiet docker || systemctl start docker

# 1. Checkout / update code
if [ -d "$APP_DIR/.git" ]; then
  log "updating existing checkout at $APP_DIR"
  git -C "$APP_DIR" fetch origin "$BRANCH" --tags || true
  git -C "$APP_DIR" reset --hard "origin/$BRANCH"
else
  log "fresh clone of $REPO (branch $BRANCH) -> $APP_DIR"
  rm -rf "$APP_DIR"
  git clone --depth 1 --branch "$BRANCH" "$REPO" "$APP_DIR"
fi
COMMIT=$(git -C "$APP_DIR" rev-parse --short HEAD)
log "deploying commit $COMMIT"

# 2. Record currently running image for rollback
OLD_IMAGE=$(docker inspect --format '{{.Config.Image}}' cyberyukti 2>/dev/null || true)
log "rollback target: ${OLD_IMAGE:-<none>}"

# 3. Build image from the checkout (tag by commit; reuse as :latest)
NEW_IMAGE="cyberyukti:${COMMIT}"
log "building $NEW_IMAGE (this takes ~5-8 min on t3.micro)..."
if ! docker build -t "$NEW_IMAGE" -t cyberyukti:latest "$APP_DIR"; then
  log "ERROR: docker build failed"
  exit 1
fi

# 4. Swap container
docker rm -f cyberyukti 2>/dev/null || true
log "starting container on host port $APP_PORT -> container 8000"
docker run -d \
  --name cyberyukti \
  --restart unless-stopped \
  --memory 900m \
  --cpus 1.5 \
  -p "${APP_PORT}:8000" \
  "$NEW_IMAGE"

# 5. Real health check (inside the instance)
for i in $(seq 1 30); do
  if curl -fsS "http://127.0.0.1:${APP_PORT}/api/health" >/dev/null 2>&1; then
    HEALTH="OK"
    log "HEALTH CHECK PASSED on attempt $i"
    break
  fi
  log "waiting for app... attempt $i"
  sleep 5
done

# 6. Rollback if unhealthy
if [ "$HEALTH" != "OK" ]; then
  log "ERROR: health check failed — rolling back to ${OLD_IMAGE:-nothing}"
  docker rm -f cyberyukti 2>/dev/null || true
  if [ -n "$OLD_IMAGE" ]; then
    docker run -d \
      --name cyberyukti \
      --restart unless-stopped \
      --memory 900m \
      --cpus 1.5 \
      -p "${APP_PORT}:8000" \
      "$OLD_IMAGE"
    for i in $(seq 1 12); do
      curl -fsS "http://127.0.0.1:${APP_PORT}/api/health" >/dev/null 2>&1 && { log "rollback healthy"; break; }
      sleep 5
    done
  fi
  docker ps -a
  docker logs --tail 30 cyberyukti || true
  exit 1
fi

# 7. Housekeeping: drop old dangling images (keep last 3 tagged)
docker image prune -f >/dev/null 2>&1 || true

log "SUCCESS: commit $COMMIT live on port $APP_PORT"
docker ps
exit 0
