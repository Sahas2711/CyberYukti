# CyberYukti — Normalization

**Status: NOT IMPLEMENTED.** No normalization logic exists. PS16 requirement "Finding normalization" → NOT SATISFIED; merge blocker #2 (master doc Phases 21, 25).

## What normalization means here (PS16)
- Take heterogeneous scanner outputs (nuclei JSON, SARIF, semgrep, npm-audit/snyk advisories, burp XML/JSON) and map them onto **one canonical `Finding` schema** (`models.py:13-24`).
- Purpose: allow downstream dedup, validation, and scoring to operate on a single shape instead of per-vendor formats (master doc Phase 5: "Normalization logic — converts heterogeneous scanner formats to canonical Finding schema").

## Canonical-schema requirement
- The target schema already exists as the `Finding` model: `finding_id`, `cluster_id`, `scanner`, `scanner_rule_id?`, `cve?`, `cwe?`, `title`, `description?`, `asset` (Asset), `raw_evidence?`, `observed_at` (`models.py:13-24`).
- Required mapping responsibilities that do NOT exist:
  1. Per-format **field extraction** (e.g., SARIF `results[].ruleId` → `scanner_rule_id`).
  2. Value **normalization**: CWE/CVE reference parsing, asset hostname/environment resolution.
  3. `cluster_id` assignment (default empty / unassigned until dedup).
  4. `observed_at` timestamp standardization.
- No code performs any of these. `Finding` stays at schema-definition status (master doc Phase 5).

## Expected per-format → `Finding` mapping (what Person 1 must author)
| Source format | Source field(s) | Target `Finding` field |
|---|---|---|
| SARIF `results[]` | `.ruleId` | `scanner_rule_id` (`models.py:17`) |
| SARIF `results[]` | `.message.text` | `title` (`models.py:20`) |
| SARIF `results[].locations` | `.physicalLocation.artifactLocation.uri` | `asset.hostname` (`models.py:5-10`) |
| nuclei JSON | `template-id`, `host` | `scanner_rule_id`, `asset.hostname` |
| nuclei/DAST JSON | `info.severity`, `matcher-status` | `raw_evidence` (`models.py:23`) |
| npm-audit / snyk | `advisories[].cve`/`cwe`, `id` | `cve`, `cwe`, `scanner_rule_id` |
| any | producer name | `scanner` (`models.py:16`) |

None of these adapters exist; there is no code reading any of these formats (master doc Phase 5).

## Why `finding_count` is a constant, not a normalization result
- `finding_count=3` (CASE-001, `fixtures.py:67`), `=2` (`fixtures.py:120,271,324`), `=3` (`fixtures.py:173`), `=1` (`fixtures.py:218`) are **hand-written literals** passed into each `TriageCase` constructor.
- They are not derived from any `Finding` list length, not a count of normalized records, and not a clustering outcome. No list of findings exists to count — `Finding` is never instantiated (master doc Phases 3, 5, 20).
- The dashboard aggregates them: `total_findings = sum(c["finding_count"] for c in cases)` (`dashboard_routes.py:11`) — so the "13 findings reduced to 6 cases" display is summing constants (master doc Phase 20: **MISLEADING** — implies dedup happened). Same number is echoed in the frontend stats (`mockProvider.ts:403`) and the seeded `"clustered"` audit event (`mockProvider.ts:260`).

## Where normalized data would land (target, not current)
```
scanner artifact → parser → Finding objects (normalized) → Cluster (dedup) → TriageCase
```
- Today the graph starts at `TriageCase`: `fixtures.py:61-361` → `CASES:363-370` → in-memory stores (`case_routes.py:12`, `ai_routes.py:8`). There is no upstream node to normalize (master doc Phase 16, 22).

## Current-status table
| Normalization artifact | Exists? | Evidence |
|---|---|---|
| Parser for scanner formats | NO | no ingestion routes (master doc Phase 5) |
| Canonical `Finding` instantiation | NO | never constructed (`fixtures.py:4` import only) |
| Field/value mapping | NO | — |
| `finding_count` correctness | NO | fixtures.py hardcoded per-case |
| Contract with Person 4 `TriageCase` | schema aligned | `models.py:13-24` ↔ `models.py:96-109` 12 fields |

## Verification status
- No normalization code → no tests possible. NOT EXECUTED (branches_docs.md §13 records zero ingestion/normalization tests).
- Gate "Normalization exists" = FAIL → **MERGE BLOCKER #2** (master doc Phase 25).