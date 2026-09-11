# CyberYukti — Docker

Status: NOT PRESENT — no containerization artifacts exist in the repository.

Static verification (glob scan, VERIFIED)
- `**/Dockerfile*` → no files found.
- `**/docker-compose*.{yml,yaml}` → no files found.
- `**/{Makefile,makefile,*.sh}` → no files found.
- No `.dockerignore`, no container healthcheck, no CI/CD config.

Execution status
- `docker compose build` / `docker compose up` → **NOT EXECUTED — static verification only**. No compose file exists to run; one-command demo is impossible (Phase 12, MASTER_SYSTEM_DOCUMENTATION.md:284-291).
- No image was ever built or inspected in this audit.

Impact
- Two-terminal manual deployment is the only runtime (see DEPLOYMENT.md).
- A judge cannot stand the system up with a single command.

What a Docker harness must add (required services)
1. Backend service — build `backend/`, run `uvicorn backend.app.main:app` from the WORKDIR `/app` at the repo root so `backend.app.*` imports resolve (root-run requirement, Phase 11).
2. Frontend service — Node build of `frontend/`; `NEXT_PUBLIC_API_URL` must point at backend service name, not `localhost`.
3. Controlled vulnerable target — PS16 requires a real demoable target; a fixture-only image would not change the "demo, not pipeline" verdict.
4. Healthchecks — backend `GET /health`; frontend HTTP 200 probe; target reachability probe.
5. Resource limits — CPU/memory caps on backend (uvicorn) and frontend (next); the sandbox (Person 2) must be a separate, network-isolated, k3s/time-boxed unit with no host mount when it is added.

Honest note
- Containerizing today's code would only containerize the demo. Docker does not supply ingestion, dedup, validation, or scoring — it is one of the 8 merge blockers, not a fix for the missing engine (Phase 25).

Recommended compose topology (for when it is added — design note, NOT EXECUTED)
```
networks: app-net (internal), target-net (PS16 vulnerable target, isolated)
services:
  backend:   WORKDIR /app  → python -m uvicorn backend.app.main:app --port 8000
             healthcheck: GET /health → 200; volumes: none (in-memory state)
  frontend:  build frontend/ → next start :3000
             env NEXT_PUBLIC_API_URL=http://backend:8000, NEXT_PUBLIC_USE_MOCK (build-time)
             depends_on: backend (condition: service_healthy)
  target:    PS16-controlled-vulnerable-app only on target-net
             NOT reachable from frontend; reachable from backend sandbox when Person 2 exists
```

Why the harness must respect these four constraints (each VERIFIED against current code)
- **Root-run inside image**: uvicorn must run from a WORKDIR that is the repo root, because all imports are `backend.app.*` (`main.py`); a `pip install -e backend` inside the image gives the editable package, but the CWD still decides importability.
- **Frontend URL is server-side**: the browser fetches via `NEXT_PUBLIC_API_URL` baked at build time (`client.ts:1`) — it must resolve inside the browser, so the real answer is `http://localhost:8000` with host port mapping, not the service name.
- **CORS restricts cross-origin**: backend only allows `http://localhost:3000` (`main.py:13-19`); a different compose port (e.g. 8080) needs a CORS change.
- **No mount of host filesystem** into any service in a demo: keeps the sandbox-escape surface at zero until Person 2's isolation model is defined.