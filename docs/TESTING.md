# CyberYukti — Testing

**Status:** LOW-MODERATE CONFIDENCE. 24 tests pass (16 backend mock-AI + 8 frontend UI-rendering), build + lint clean — but nothing tests routes, persistence, deployment, or the paid providers, and every backend test runs against the deterministic mock.

## What runs and what it proves (VERIFIED — master doc Phases 15, 25)
- **Backend pytest — 16 passed.**
  - `test_injection.py` (13 tests): 10 parametrized payloads (`ignore_previous_instructions`, `dan_jailbreak`, `shell_command`, `priority_override`, `json_instruction`, `unicode_homoglyphs`, `base64_payload`, `markdown_fences`, `nested_untrusted`, `long_payload` — `test_injection.py:8-59`) driven against `MockProvider` for schema-valid output (`:89-119`); plus `test_mock_provider_output_matches_schema` (`:121-127`), `test_mock_provider_produces_valid_json` (`:130-135`), `test_mock_provider_does_not_follow_instructions` (`:138-149`).
  - `test_hallucination.py` (3 tests): `test_no_kev_claimed_when_none_in_input` (`:78-93`), `test_correct_cvss_referenced` (`:96-114`), `test_no_cve_invented` (`:117-135`) — validator + mock.
  - Proves: the deterministic mock provider ignores instructions and passes grounding checks. Does NOT prove real-LLM safety (master doc Phase 15 caveat: real LLMs hallucinate CVEs; these tests would likely FAIL against a real provider).
- **Frontend vitest — 8 passed.** `injection-ui.test.tsx`: 6 payloads + `<img src=x onerror=alert(1)>` render as plain text with no `<script>`/`<img>` elements; benign control has no false positives (`injection-ui.test.tsx:6-61`). Proves React escaping is XSS-safe for EvidencePanel.
- **Build + lint — clean.** `npm run build` completes; backend starts and serves routes (master doc Phase 25 gates PASS).

## What it proves about real AI — very little
- All 16 backend tests import `MockProvider` directly (`test_injection.py:5`, `test_hallucination.py:5`). OpenAI/Anthropic never invoked (no keys on this machine) — mark **NOT EXECUTED** (master doc Phase 26 §2).

## Coverage gap analysis
- **No route tests** — all 9 endpoints verified by manual live probes only, never automated (master doc Phase 15; branches_docs.md §13).
- **No approval/audit tests** — 400/404/409 guards and restart-loss are probe-verified, not automated.
- **No persistence tests**; **no sanitizer unit tests** (sanitizer tested only indirectly via mock + injection); **no validator unit tests** (only via the hallucination suite).
- **No E2E**, **no deployment tests** (no Docker — master doc Phase 12), **no load/performance tests**.
- **No adversarial route tests** — malicious `analyst_id`/`reason` bodies untested (master doc Phase 14).

## Coverage table (honest — no percentages)
| Category | Runs | Tests | Status |
|---|---|---|---|
| Unit — AI mock + validator | pytest | 16 passed | LOW (mock-only) |
| Unit — frontend rendering | vitest | 8 passed | LOW (EvidencePanel only) |
| Integration (routes x stores) | — | 0 | NONE |
| E2E (ingest → approve) | — | 0 | NONE |
| Security (injection/XSS) | 10 + 8 | 18 passed | MODERATE but mock-only |
| Deployment (Docker/startup) | — | 0 | NONE (no Dockerfile) |
| Paid providers (OpenAI/Anthropic) | — | 0 | NOT EXECUTED |

## Regression triggers (what each green test protects)
- Mock provider: any change that breaks schema, JSON validity, or field completeness fails `test_injection.py:121-149`.
- Grounding: any change that lets mock output invent CVEs/CVSS/KEV fails `test_hallucination.py:78-135` (mock output is hand-built, so these assert mock+validator agreement, not real-AI grounding).
- UI: any change that renders payloads as HTML (`dangerouslySetInnerHTML`, unescaped interpolation) fails `injection-ui.test.tsx:35-61`.

## Verdict
- Confidence is LOW-MODERATE: deterministic mock behavior and UI escaping are genuinely proven; the pipeline, routes, persistence, and real-LLM behavior are untested. Matches master doc Phase 26 final verdict.
- Route/integration/E2E/deployment stay NONE until `INTEGRATION_GAPS.md` GAP 10 is closed.