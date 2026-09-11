# CyberYukti — Threat Intelligence

**Status:** NOT IMPLEMENTED (data only). `threat_intelligence` is a fixture constant per case; zero NVD/EPSS/KEV/OSV enrichment calls exist.

## The data — HARDCODED CONSTANT (`fixtures.py`)
| Case | cvss | epss | kev | File:Line |
|---|---|---|---|---|
| CASE-001 | 8.8 | 0.72 | true | `fixtures.py:94` |
| CASE-002 | 5.4 | 0.15 | false | `fixtures.py:147` |
| CASE-003 | 6.1 | 0.42 | false | `fixtures.py:192` |
| CASE-004 | 4.2 | 0.08 | false | `fixtures.py:245` |
| CASE-005 | 7.5 | 0.35 | false | `fixtures.py:298` |
| CASE-006 | 9.8 | 0.85 | true | `fixtures.py:343` |
- Schema: backend `TriageCase.threat_intelligence: dict` (`models.py:105`); frontend typed strictly as `{ cvss?; epss?; kev? }` (master doc Phase 9).

## How the constants flow today (no source anywhere)
- AI mock reads `threat_intelligence.cvss/epss/kev` and interpolates them into `why_it_matters`/`priority_explanation` (`mock_provider.py:40-44,78-80`).
- The same cvss/epss/kev are re-listed by hand in `PriorityResult.factors` (`fixtures.py:99-106` vs `fixtures.py:94`) — consumed by `PriorityBreakdown`.
- `ThreatIntelPanel` renders the dict directly (master doc Phase 8).
- Enrichment endpoints: NVD (`nvd.nist.gov`), EPSS (`api.first.org`), CISA KEV (`cisa.gov`), OSV — grep across `backend/app` → **0 hits** (master doc Phase 7; `INTEGRATION_GAPS.md` GAP 7). Nothing refreshes or derives these values.

## Illustrative (fake) CVEs — proof the data is hand-written
- `CVE-2099-0001` (`fixtures.py:68`), `CVE-2099-1234` (`fixtures.py:121`), `CVE-2099-5678` (`fixtures.py:219`), `CVE-2099-9999` (`fixtures.py:272`), `CVE-2099-7777` (`fixtures.py:325`).
- Year `2099` is in the future — these cannot be real NVD/KEV/EPSS-correlated entries (master doc Phase 3: all six cases HARDCODED FIXTURE).
- Hand-duplication signature: CASE-005 `evidence_confidence` differs between backend `PriorityResult.factors` (0.82, `fixtures.py:309`) and the frontend mock (0.90, `mockProvider.ts:106`) — copy-pasted, not machine-generated, data (branches_docs.md §6).

## No validation of the intel values
- Nothing clamps or bounds the constants: cvss is any float (no 0-10 check), epss any float (no 0-1 check), kev any truthy value — all flow dict → UI and mock text untouched (`mock_provider.py:41-44`).
- No refresh policy, no staleness field: there is no "as_of"/timestamp on the intel dict (the `validated_at` on evidence is a separate constant, `fixtures.py:91`).

## Hazard
- The grounding validator checks only CVE presence-in-input, not validity (`validator.py:104-106`): a fabricated `CVE-2099-*` would pass grounding against a real LLM. Future enrichment must reject CVEs whose year exceeds the current CY.

## What a real implementation must add (all absent)
1. EPSS query to `api.first.org` keyed by CVE; 2. CISA KEV membership lookup; 3. NVD CVSS retrieval; 4. OSV advisory correlation; 5. cache + staleness TTL; 6. per-case "as_of" provenance; 7. validator rule: referenced CVE year ≤ current CY (see Hazard).

## PS16 traceability
- "Exploitability context (EPSS/KEV)": NOT IMPLEMENTED (master doc Phase 21). No OSV advisory correlation; `Finding.cve` (`models.py:18`) is never consulted because `Finding` is never instantiated.

## Cross-references
- System-wide: PS16 completion 1.5/11 (13.6%), DO NOT MERGE (8 blockers), single branch `person4` (master doc Phases 21, 25; branches_docs.md §1).
- Intel constants are also the raw inputs the (absent) risk formula would consume — see `RISK_ENGINE.md`; both share the same fixture dicts (`fixtures.py:94` vs `fixtures.py:99-106`).