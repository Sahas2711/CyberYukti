# CyberYukti — Security Model

**Status:** ADEQUATE FOR LOCAL (fixture) DEMO, NOT PRODUCTION. No auth, no rate limiting; sanitizer protects only the AI path; no secrets in tree; no subprocess/network/file surfaces.

## Verified attack surface (all of it)
- **CORS** — `allow_origins=["http://localhost:3000"]`, `allow_credentials=True`, `allow_methods=["*"]`, `allow_headers=["*"]` (`backend/app/main.py:13-19`). Localhost-only trust; permissive methods acceptable locally, must be narrowed in production (master doc Phase 13, INFO).
- **Endpoints** — 9 routes, all unauthenticated (`main.py:21-30`; master doc Phase 10).
- **Rate limiting** — NONE on any endpoint (master doc Phase 10).
- **Secrets** — secret scan clean; only `.env.example` committed with empty placeholders (master doc Phase 1). Env reads use empty-string defaults: `OPENAI_API_KEY` (`openai_provider.py:24`), `ANTHROPIC_API_KEY` (`anthropic_provider.py:24`), `USE_MOCK_AI` default `true` (`engine.py:18`).
- **Runtime surfaces** — 0 hits for `subprocess`, `docker`, `os.system`, `socket`, file I/O, or outbound HTTP in `backend/app` (master doc Phase 13). Only middleware is CORS (`main.py:13-25`).

## Endpoint security quick table (all ratelimit/auth = none)
| Endpoint | Auth | Authz gate | Notes |
|---|---|---|---|
| `/health` | none | — | `main.py:28-30` |
| `/api/cases` + detail | none | — | `case_routes.py:22-41` |
| `/approve`,`/reject`,`/override` | none | 409 state machine (approx/reject only) | `approval_routes.py:39-134`; `analyst_id` self-asserted |
| `/api/ai/analyze/{id}` | none | — | 500 leaks `str(e)` (`ai_routes.py:21-22`) |
| `/api/dashboard/stats` | none | — | `dashboard_routes.py:8-33` |
| `/api/cases/{id}/audit` | none | — | `audit_routes.py:8-12` |

## Input validation surface
- **Sanitizer (AI path only):** 24 `UNTRUSTED_FIELDS` (`sanitizer.py:7-30`) + 3 `ASSET_FIELDS` (`sanitizer.py:34-36`); control-char strip + 2000-char truncation + `<UNTRUSTED>` wrapping (`sanitizer.py:40-44`).
- **Everything else is unvalidated:**
  - `analyst_id` — any string trusted verbatim (`approval_routes.py:46,76,106`).
  - `reason` — unbounded free text; `approve` stores it even when absent (`approval_routes.py:56-62`); reject/override require presence only (`:80-81,114-115`).
  - `override_priority` — enum-checked against P1–P4 (`:112`).
  - Approval bodies parsed via raw `await request.json()` (`:45,74,105`) — no Pydantic model, no body-size limit, no extra-key rejection.

## Attack-path analysis
```
POST body → request.json() → dict → store in memory → re-render in React
```
- No path executes user input: no subprocess, no eval, no `dangerouslySetInnerHTML`. Worst case is data corruption of the in-memory fixture store (no auth → any caller can approve/override).

## Web / XSS
- No `dangerouslySetInnerHTML`, no `eval`, no `new Function` anywhere in the frontend; React default text escaping (master doc Phase 13). 8 injection tests verify malicious payloads render as text, never as elements (`frontend/tests/injection-ui.test.tsx:35-61`).

## AppSec table (master doc Phase 13 — reproduced)
| Severity | File:Line | Finding | Impact | Fix |
|---|---|---|---|---|
| INFO | `main.py:13-19` | CORS localhost-only, credentials True, methods `*` | None locally | Restrict methods in prod; document |
| INFO | `approval_routes.py:46,76,106` | No auth; `analyst_id` trusted verbatim | Analyst impersonation | API key / JWT for non-demo |
| LOW | `ai_routes.py:21-22` | 500 detail returns `str(e)` | Information disclosure | Generic message; log server-side |
| NONE | `sanitizer.py:40-44` | Control-strip + truncate + `<UNTRUSTED>` wrap | No injection path | — |
| NONE | `system_prompt.txt` | Tags declared as data | Blocks prompt injection | — |
| NONE | Frontend | No dangerouslySetInnerHTML/eval | XSS surface eliminated | — |

## Hardening priorities (NONE implemented)
1. API-key/JWT auth + `analyst_id` sourcing from token, not body.
2. Replace 500 `str(e)` with generic detail + server logging (`ai_routes.py:21-22`).
3. Rate limiting; narrow CORS `allow_methods` (`main.py:17`).
4. Schema-validate approval bodies (Pydantic), bound `reason` length.

## Bottom line
- **0 CRITICAL / 0 HIGH / 1 LOW** (master doc Phase 26).
- Acceptable for local, fixture-driven demo; NOT a production model (no auth, no rate limit, no persistence).
- Largest forward risk: the missing Person-2 sandbox — its isolation guarantees (`SANDBOX_SECURITY.md`) must land with any probe code.