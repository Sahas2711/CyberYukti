# CyberYukti — Evidence Engine

**Status:** NOT IMPLEMENTED. No probe execution exists anywhere in the backend. `ValidationResult`/`EvidenceObservation` models are used only as type annotations for fixture constants.

## What exists (models only)
- `EvidenceObservation` (`backend/app/cases/models.py:35-41`): observation_id, type, target, observed_value, expected_value, method.
- `ValidationResult` (`backend/app/cases/models.py:44-50`): cluster_id, status, confidence, observations, validated_at, validator_version.
- Both are instantiated exclusively inside hardcoded `TriageCase` constructors:
  - CASE_001 evidence block — obs-001/obs-002, `status="CONFIRMED"`, `confidence=0.95` (`fixtures.py:69-93`).
  - CASE_002 (`fixtures.py:122-146`), CASE_003 (`fixtures.py:175-191`), CASE_004 (`fixtures.py:220-244`), CASE_005 (`fixtures.py:273-297`), CASE_006 (`fixtures.py:326-342`).
- No code reads or computes these fields. `status`/`confidence` are set at case-creation time, not produced by any validation logic (master doc Phase 6).

## Data flow today (pure pass-through)
```
fixtures.py CASES → case_routes._cases_store (case_routes.py:12) → GET /api/cases/{id} JSON
→ EvidencePanel renders ValidationResult fields as text → ValidationBadge colors the literal status
```
- `EvidencePanel` is a pass-through renderer (master doc Phase 23). No downstream engine consumes observations.

## What does NOT exist
- Zero probe execution: grep for `subprocess`, `docker`, `requests.get`, `httpx.get`, `os.system`, `socket`, `urllib` in `backend/app` → **0 hits** (re-verified).
- No sandbox, no Docker container, no subprocess wrapper, no target contact of any kind (master doc Phases 6, 12).
- No `POST /api/validate/{cluster_id}` route — the evidence-validation endpoint PS16 requires does not exist (master doc Phase 10 "Missing endpoints"; `INTEGRATION_GAPS.md` GAP 4).

## What a real evidence engine would need (design note — nothing implemented)
1. **Target registry** — resolved, allowlisted host/asset records to probe. Fixtures only carry hostnames (e.g. `fixtures.py:15`); no reachable-target structure exists.
2. **Probe allowlist** — explicit allow/deny so scanner payloads can never select an arbitrary target. Absent.
3. **Probe library** keyed to `EvidenceObservation.type` (`models.py:37`):
   - `http` probes (status/body) — `method="http_get"` is a fixture string (`fixtures.py:80`), never a call.
   - `package` probes (dependency/version) — `method="dpkg"` (`fixtures.py:133`) is a string; no dpkg execution.
   - `port` probes (reachability) — not present, even as fixture data.
   - `file` probes (existence/hash/stat) — `method="stat"` (`fixtures.py:141`) is a string; no stat call.
4. **Evaluator** — maps observed-vs-expected to CONFIRMED / NOT_CONFIRMED / INCONCLUSIVE; today `status` is a literal (`fixtures.py:71,124,177,222,275,328`).
5. **Confidence calculation** — derived from probe agreement/count/freshness; today `confidence` is a literal (`fixtures.py:72,125,178,223,276,329`).
6. **Validator provenance** — `validator_version="2.1.0"` (`fixtures.py:92`) is a literal; no validator binary exists.

## Security-relevant observation
- Fixture `observed_value` strings already embed prompt-injection and `<script>` text (`fixtures.py:229,237`). A real probe road — if a target reflects such strings — is the future untrusted-input surface (`THREAT_MODEL.md`); probe output must become `EvidenceObservation` data only (`SANDBOX_SECURITY.md` guarantee 7).

## PS16 traceability
- "Evidence validation": NOT IMPLEMENTED — `ValidationResult` used as fixture type only (`models.py:44-50`; master doc Phase 21).
- "Safe sandbox": NOT IMPLEMENTED — no probe/sandbox code at all.
- Person 2 owns this slice (master doc Phase 22); acceptance = a probe against a real target produces a computed, restart-safe `ValidationResult.status`.