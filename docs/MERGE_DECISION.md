# Merge Decision

**Branch reviewed:** `person4/integration` (created from `main` during review; repository previously had zero commits)
**Review date:** 2026-09-11

---

### Should we merge Person 4?

# NO (DO NOT MERGE)

---

### Why? (strongest reasons)

1. **The problem statement's engine does not exist.** No finding-ingestion endpoint, no normalization, no deduplication/clustering logic, no sandboxed evidence validation, and no deterministic priority *computation* — all case data is pre-baked fixture constants (`backend/app/mock/fixtures.py`). Persons 1–3 scope is absent from the repository.
2. **The real-workflow integration gate fails by design.** A real scanner finding has no path into the system, so "Real scanner X → vulnerability Y on target Z → validated case" (Section 46 evidence) cannot be produced.
3. **Dedup and evidence validation are fixture attributes, not behaviors.** `finding_count=3` describes a hand-written case; `CONFIRMED/NOT_CONFIRMED` are static strings. The requirement "do not merely populate finding_count" is unmet.
4. **No persistence.** Approvals, overrides, and audit events vanish on server restart (verified empirically: APPROVED→PENDING, audit cleared, P1→P2 reverted). Section 24/38.9 fail.
5. **Deployment is not one-command reproducible.** No Dockerfile/compose exists; backend must run from repo root due to `backend.app.*` imports.

---

### What was proven (working today)

- Frontend SOC workbench renders purely from data; no hardcoded fake metrics; 8/8 injection tests; 6 fixture cases.
- Real backend API: list/get cases, dashboard stats, approve (200/400/409), reject, override (P2→P1, stats update), audit log with before/after/actor/reason, `/api/ai/analyze` → grounded `mock-v1` output. 16/16 backend tests.
- Prompt-injection defenses (sanitizer `<UNTRUSTED>` wrapping, grounding validator, mock-only tests) and injection-safe UI rendering.
- All dependency/API contracts match field-for-field between frontend and backend; all deps free/open-source with an automatic free AI fallback.

---

### What was NOT proven

- Real finding ingestion, normalization, deduplication, sandboxed validation, priority computation.
- Persistence across restart.
- Any live execution against a real scanner/target through the product (blocked on the missing pipeline).
- Real (paid) LLM providers under adversarial input — tests cover the mock provider only.

---

### Real-world scenario

- **Target:** intentionally vulnerable local Flask app (`docs/REAL_WORLD_DEMO.md` §3; SQLi + reflected XSS + pinned old dependency) — fully specified, reproducible, free.
- **Scanners:** nuclei (web), semgrep (SAST), pip-audit (dependency) — all free/open-source; commands specified. **Findings were NOT fed into CyberYukti because no ingestion endpoint exists.**

### Paid dependencies?

**NO.** OpenAI/Anthropic SDKs are optional; with empty/missing keys the system automatically uses the free deterministic `mock-v1`.

### Deployable?

**PARTIAL.** Manual path verified (uvicorn from repo root + `npm run dev`). Not one-command/Docker reproducible.

### Critical blockers?

**YES.** Missing P1–P3 engine, no persistence, no deployment harness.

### Final recommendation

Do not merge Person 4 as the "complete ACSC solution" today — it would ship a fixture-driven triage/demo surface with a real approval+audit API but none of the engine the problem statement is about. Keep Person 4's frontend, contracts, and AI-guardrail layer as-is; merge only after (1) a finding-ingestion + normalization + dedup pipeline, (2) real time-boxed evidence validation, (3) a deterministic priority function, and (4) durable persistence exist and the documented restart test and E2E-001 pass. That is the acceptance path, not a redesign: none of the confirmed Person 4 architecture needs rework.