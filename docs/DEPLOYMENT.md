# CyberYukti — Deployment

Status: MANUAL PATH ONLY — no Docker, no scripts, two terminals required.

Verified clean-room procedure (from Phase 11, MASTER_SYSTEM_DOCUMENTATION.md:272-280):

```bash
git clone https://github.com/Sahas2711/CyberYukti
cd CyberYukti
python -m pip install -e backend
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000   # MUST run from repo root
cd frontend && npm install && npm run dev                              # second terminal
```

Hard requirements
- Python >= 3.11 (verified 3.11.9 during audit); Node >= 18 (verified 20.x).
- Backend MUST start from repo root. `backend/app/main.py` imports `backend.app.*`; running `uvicorn` from `backend/` fails with `ModuleNotFoundError: No module named 'backend.app'`.
- Two terminals: uvicorn (port 8000) + `next dev` (port 3000).
- Frontend reads backend at `http://localhost:8000` (`client.ts:1`); backend CORS trusts `http://localhost:3000` only (`main.py:13-19`). Allow-listed port swap to anything else silently breaks frontend fetches.
- No env vars needed to run: `USE_MOCK_AI` defaults to true → all AI analysis is mock (`engine.py:18`).

Verified behavior (live probes during audit)
- `GET /health` → 200 `{"status":"ok"}`.
- `GET /api/cases` → 200 with 6 fixture cases.
- All 9 endpoints return verified 200/400/404/409 timelines (branches_docs.md:294-306).

Blocker inventory
- No Dockerfile / docker-compose.yml / Makefile / shell scripts anywhere (glob-verified — see DOCKER.md).
- Repo-root-run requirement is UNDOCUMENTED in-repo: no README, no Makefile target, no comment in `pyproject.toml` states it; only this audit records it.
- `httpx>=0.25.0` and `python-dotenv>=1.0.0` in `pyproject.toml:10-11` are unused; `.env` is never loaded by `main.py` (Phase 11).
- No `make dev` / `make test` / `make demo` targets exist.
- Persistence is in-memory only: all approvals, audit events, and analyses vanish on restart (Phase 26).
- `.env.example` sits at repo root, not in `frontend/`; frontend-only developers may miss it.

Optional commands (also NOT EXECUTED-vs-verified separately, per Phase 25)
- Backend tests: `python -m pytest -q` from repo root → 16/16 pass (mock provider only).
- Frontend tests: `npm test` in `frontend/` → 8/8 pass (UI injection rendering only).
- Frontend build: `npm run build` in `frontend/` → completes clean (gate PASS, Phase 25).
- No automated start test exists for the server; startup was verified via live probes during the audit.

Runtime truth table
- Backend up, frontend idle: API is fully usable via curl on 8000.
- Both up: full workbench on http://localhost:3000.
- Backend restarted mid-demo: every approval, audit event, and `ai_analysis` in memory is wiped; fixtures reload pristine (Phase 26.4).
- Mock vs real AI: with no keys, BOTH providers fall back to MockProvider — the "real" path is unreachable without secrets (`USE_MOCK_AI=false` + valid `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`).

Pre-flight checklist for a clean machine (each step VERIFIED or its status stated)
1. `python --version` >= 3.11, `node --version` >= 18.
2. Ports 8000 and 3000 free (or expect CORS/connection failure on the frontend).
3. `pip install -e backend` succeeds per `pyproject.toml` (starlette pinned `==0.37.2` is the only version-locked dep).
4. `.env` optional — no runtime key required for demos.