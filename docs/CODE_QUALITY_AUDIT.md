# CyberYukti — Code Quality Audit

Status: GOOD within Person 4 scope — typed, consistent, injection-hardened; with 8 documented defects, none fatal to the demo.

Positive findings (VERIFIED)
- Typed contracts: 9 backend Pydantic models ↔ 10 TypeScript interfaces match field-for-field (`types.ts` vs `models.py`; branches_docs.md:260-270).
- Consistent FastAPI patterns: router-per-domain, Pydantic validation, uniform `detail`-style errors across all 5 routers.
- AI fallback chain is explicit and bounded: provider → retry with stricter prompt → MockProvider → hardcoded minimal fallback (`engine.py:45-104`).
- Sanitizer recursion-safe pattern: `TAG_RE` strips `<UNTRUSTED>` re-tags; control-char strip + 2000-char truncation + field wrap (`sanitizer.py:40-44`).
- Grounding validator: CVE references and numeric values in output must exist in input; `grounded_on` must be non-empty (`validator.py:63-108`).
- Frontend `useMemo` for filtered/sorted case list (`CaseTable.tsx:73-87`).
- No `dangerouslySetInnerHTML`, no `eval`, no `new Function` anywhere in the frontend; injection-safe rendering proven by 8 tests.
- 16 backend + 8 frontend tests all pass (mock/UI only).

Negative findings (documented defects)

| # | Defect | Evidence | Consequence |
|---|---|---|---|
| 1 | Duplicate `AIAnalysis` model — identical copies in two modules | `cases/models.py:61-72` AND `ai/schemas.py:4-15`; engine imports schemas, routes import models | Works only because routes return raw dicts via `model_dump()`; schema-drift risk |
| 2 | Two independent in-memory case stores | `case_routes.py:12` vs `ai_routes.py:8` each build `{c["case_id"]: c for c in CASES}` | Silent data inconsistency: approve in one store is invisible to the other and vice versa |
| 3 | `prev_hash` is NOT a hash | `approval_routes.py:22` sets it to the previous `event_id` | Misleading field name implies cryptographic chaining that does not exist |
| 4 | Approval response typed as `TriageCase` in FE, returns `ApprovalState` | `realProvider.ts:42-46` vs `approval_routes.py:65` | Non-blocking: FE discards body and re-fetches via `getCase()`; hides the contract violation |
| 5 | CASE-005 confidence divergence — hand-duplicated data | backend `fixtures.py:309` `evidence_confidence: 0.82` vs frontend `mockProvider.ts:106` `0.90` | Proves fixtures were duplicated by hand, not generated from one source of truth |
| 6 | Fixture data duplicated wholesale | backend `fixtures.py:61-361` vs frontend `mockProvider.ts` FIXTURES | Two sources of truth always drift (see #5) |
| 7 | Stale docs | `frontend-ui-documentation.md` lists deleted components; `person4-failure-checklist.md` references nonexistent localStorage toggle | Misleads maintainers |
| 8 | Fragile audit import chain | `audit_routes.py:3` imports `_audit_store` from `case_routes.py` | Load-order dependency; nukes import layering |

Test confidence (positive, VERIFIED)
- Backend: 16/16 pass — 10 parametrized injection + 3 direct injection + 3 hallucination guard tests (`test_injection.py`, `test_hallucination.py`). All exercise MockProvider; none exercise a real LLM.
- Frontend: 8/8 pass — `EvidencePanel` renders 8 injection payloads safely; no `<script>` elements, all payloads appear in `textContent` (`injection-ui.test.tsx`).
- Route-level: 9 endpoints verified by live HTTP probe (not automated tests) — 200/400/404/409 timelines recorded in Phase 10.

Test confidence (negative, VERIFIED)
- No automated route/integration/E2E tests (Phase 13, MASTER_SYSTEM_DOCUMENTATION.md:326-331).
- No sanitizer or validator unit tests; tested only indirectly via MockProvider + injection/hallucination tests.
- Approval workflow untested in automation; only live-probe evidence recorded (Phase 10).

Recommended cleanup priority (none is a merge blocker for the demo; all are for PS16)
1. Merge the duplicate `AIAnalysis` — pick `ai/schemas.py` as canonical, delete the copy in `models.py`.
2. Unify the case store — `ai_routes.py` and `case_routes.py` must share one dict reference.
3. Rename `prev_hash` → `previous_event_id` to stop the cryptographic-implying semantics.
4. Delete `Finding` and `Cluster` models from `models.py` until Person 1 owns them.
5. Erase or version-pin fixtures — or generate them from a single JSON source so frontend and backend cannot drift (see #5, #6 above).

Verdict
- Nothing in Person 4 scope needs rewriting (Phase 26.10) — the missing engine must be ADDED, not fixed. These defects are the correct surface for a cleanup pass, e.g., delete one `AIAnalysis`, unify the case store, rename `prev_hash`, and remove dead models (`Finding`, `Cluster`).