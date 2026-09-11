# CyberYukti — Deployability Audit

Status: FRESH CLONE CAN RUN — YES, manual, 2 terminals. Judge reproducibility: YES (fixture UI walkthrough), NO (real-world E2E).

Ruthless clean-machine checklist

| Q | A | Notes / evidence |
|---|---|---|
| Any Docker one-liner? | NO | No Dockerfile/compose/Makefile/scripts (DOCKER.md). |
| Can a fresh clone run? | YES (manual) | Verified path (Phase 26.14): two terminals, backend from repo root. |
| Terminals required? | 2 | terminal 1 = uvicorn (8000), terminal 2 = `next dev` (3000). |
| Backend from any cwd? | NO | Must run from repo root — imports are `backend.app.*`; running from `backend/` fails `ModuleNotFoundError` (branches_docs.md:223). Undocumented in repo. |
| Ports | 8000 + 3000 | CORS allow-list is exactly `http://localhost:3000` (`main.py:13-19`). |
| Env needed for run? | NO | `USE_MOCK_AI` / `NEXT_PUBLIC_USE_MOCK` default to mock both sides (CONFIGURATION.md). |
| Deps will install? | YES | `pip install -e backend` (FastAPI/uvicorn/pydantic + optional SDKs); `npm install` (Next 14/React 18/Tailwind/Vitest). Both dependency sets stable (Phase 11). |
| .env required? | NO | `.env` never loaded by `main.py`; `.env.example` optional (CONFIGURATION.md). |
| Data survives restart? | NO | All stores in-memory; a judge that restarts the backend loses every decision/audit (Phase 26.4). |
| Demo today? | YES | 6 pre-baked cases, workbench, approve/reject/override, audit, AI mock analysis (Phase 16). |

Blocker inventory (deployability-specific)
- No Dockerfile / no docker-compose / no Makefile / no shell scripts — no orchestration.
- Root-run requirement undocumented in repo — a fresh judge has no in-repo signal.
- Unused deps `httpx`, `python-dotenv` — misleading install surface; no harm to startup.
- Assumption differences: backend assumes fixtures as truth; frontend duplicates the fixtures (`mockProvider.ts`), so a judge runs against TWO copies of the same hand-typed data that are known to diverge (CASE-005 0.82 vs 0.90).
- `.env.example` at repo root only, not in `frontend/` — frontend-only judge may not see mock/no-key guidance.

Judge reproduction checklist (step-by-step, VERIFIED unless stated NOT EXECUTED)
1. Clone `https://github.com/Sahas2711/CyberYukti` and check out `person4`.
2. Terminal 1: `python -m pip install -e backend` (installs FastAPI/uvicorn/pydantic; openai/anthropic optional).
3. Terminal 1: `python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000` — must be repo root.
4. Terminal 2: `cd frontend && npm install && npm run dev` — Next.js on port 3000.
5. Browser: open `http://localhost:3000` — dashboard loads with 6 cases.
6. Click any case → detail view; click "Analyze" button → `POST /api/ai/analyze/{id}` → mock analysis appears.
7. Approve CASE-001 (double-click confirm) → 200; audit trail shows `approve` event.
8. Override CASE-005 to P1 → 200; audit shows `override` with `old_priority`/`new_priority`/`reason`.
- What would break: stopping backend mid-demo → all in-memory state wiped; frontend still shows stale (or falls back to mock on next fetch).
- What cannot be tested: ingestion of scanner output, risk scoring from factors, evidence probe execution, persistence across restart.

Assumption differences (clean-machine gotchas)
- `starlette==0.37.2` pinned exact (`pyproject.toml:7`) — harmless but fragile if any transitive dep requires a different Starlette version.
- The frontend `package-lock.json` is committed (standard for apps); `pyproject.toml` has no lock file — `pip install -e backend` resolves latest minor versions within constraints.
- `httpx` is declared as required (`pyproject.toml:10`) but never imported in any route; its presence in the dependency list is misleading to anyone auditing attack surfaces (it is not used).
- `next-env.d.ts` is `.gitignore`d (`frontend/.gitignore`); Next regenerates it at build time — no issue, but some teams track it and this repo does not.

Can a judge reproduce it? (truthful, Phase 26.15)
- **YES for the fixture UI walkthrough**: clone → install → 2 terminals → browser → open dashboard, click `CASE-001`, analyze, approve, override CASE-005, read audit. Genuine, functional Person 4 demo (branches_docs.md:378).
- **NO for real-world E2E**: "scan real vulnerability → finding → case → analyst approves" does not exist. No ingestion endpoint, no target, no sandbox, no scoring (branches_docs.md:380; Phase 26.15).

Verdict
- Deployability is PARTIAL by every honest measure: install-and-run is real, orchestration is absent, and runtime state is ephemeral. The deployment story is a demo runner, not a platform.