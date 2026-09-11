# CyberYukti — Exhaustive Limitations
Status: VERIFIED — sourced from master doc Phases 3–15, 20, 22, 26.

---

## Persistence
- All data lives in Python dicts. Restart wipes approvals, audit events, and analyses. `case_routes.py:12`, `ai_routes.py:8`, `approval_routes.py:15`.

## Two Divergent Case Stores
- `case_routes._cases_store` and `ai_routes._cases_store` are separate dicts built from the same fixture list. Mutations in one are invisible to the other. Silent data consistency bug.

## `prev_hash` Semantics
- `approval_routes.py:22` — field stores previous `event_id`, not a cryptographic hash. Name is misleading. Not an integrity chain.

## No Authentication
- `approval_routes.py:46,76,106` — `analyst_id` accepted verbatim from request body. Any HTTP caller can impersonate any analyst.

## No Rate Limiting
- Zero rate limiting on any endpoint. No throttling, no request quotas.

## Mock-Only AI Verification
- 16 backend tests test `MockProvider` only (`test_injection.py`, `test_hallucination.py`). Paid providers (OpenAI, Anthropic) never tested under adversarial input. Tests validate guardrails against a deterministic string builder, not real LLM behavior.

## Paid Providers Untested
- `openai_provider.py`, `anthropic_provider.py` — exist but fall back to mock silently when no API key is configured. Zero evidence of real LLM invocation on this machine.

## Fake CVEs
- Fixtures reference `CVE-2099-*` (non-existent year). These are placeholder identifiers, not real CVEs.

## Fixture Evidence Statuses
- `evidence.status` (CONFIRMED/NOT_CONFIRMED/INCONCLUSIVE) set at case creation time (`fixtures.py:69-93`). No probe produces these values.

## Stale Documentation
- `frontend-ui-documentation.md` references deleted components (`StatCard`, `PriorityChart`, `AssetPanel`, `DuplicateSourcesPanel`).
- `person4-failure-checklist.md` references a localStorage toggle that does not exist.

## Windows Path/Import Quirks
- Backend must run from repo root (`python -m uvicorn backend.app.main:app`). Running from `backend/` fails with `ModuleNotFoundError`. Undocumented requirement.

## No Docker
- No Dockerfile, docker-compose.yml, Makefile, or shell script (Phase 12). One-command deployment impossible.

## CASE-005 Confidence Mismatch
- Backend fixture `fixtures.py:309`: `confidence=0.82`. Frontend mock `mockProvider.ts:106`: `confidence=0.90`. Data was hand-duplicated, not machine-generated.

## `Finding` and `Cluster` Models Unused
- `models.py:13-32` — both defined, never instantiated. Dead code occupying schema space.

## Unused `httpx` Dependency
- `pyproject.toml` — `httpx>=0.25.0` listed but never imported in any backend route.

## Duplicate `AIAnalysis` Definition
- Identical in `models.py:61-72` and `ai/schemas.py:4-15`. Works because `model_dump()` produces identical dicts.

## Exception Message Leakage
- `ai_routes.py:17-22` — HTTP 500 returns `str(e)`. Could expose internal error details.

## Frontend Approval Response Type Mismatch
- Frontend types approve/reject/override as `TriageCase`; backend returns `ApprovalState`. Non-blocking (response body discarded, re-fetches via `getCase()`).

## Audit 404 vs [] Divergence
- Backend returns 404 when no audit events exist (`audit_routes.py:11`). Frontend mock returns `[]`. Frontend real mode falls back to mock on 404.
