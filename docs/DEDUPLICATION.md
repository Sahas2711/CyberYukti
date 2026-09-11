# CyberYukti — Deduplication

**Status: NOT IMPLEMENTED.** No clustering algorithm. The `Cluster` model is UNUSED. The "3 FINDINGS → 1 CLUSTER → 1 TRIAGE CASE" UI is a fixture-literal display. Merge blocker #3 (master doc Phases 5, 21, 25).

## Current truth
- `Cluster` (`models.py:27-32`: `cluster_id`, `finding_ids`, `primary_finding_id`, `dedup_confidence`, `dedup_method`) is imported at `fixtures.py:5` and **never instantiated** (master doc Phase 3).
- `finding_count` is a hand-written constant per case (`fixtures.py:67,120,173,218,271,324`) — not a clustering result (master doc Phase 5:112-122).
- No `GET /api/clusters`; dedup "output" appears only as `cluster_id` strings baked into fixtures (`fixtures.py:63` etc.) and frontend `_cases` (`mockProvider.ts:12`).

## The UI is a fixture display, not pipeline evidence
- `DuplicateClusterPanel` (`frontend/components/case/DuplicateClusterPanel.tsx:23-48`) renders a fixed chain: `{findingCount}` Findings → **1** Cluster → **1** Triage Case, where `findingCount ?? 0` is passed the fixture number (`finding_count`, e.g. `fixtures.py:67`).
- Subtitle "Findings normalized and deduplicated" (`DuplicateClusterPanel.tsx:19`) — **FALSE**: no normalization or dedup code exists (master doc Phase 20: **MISLEADING/FALSE**).
- "Origins" chips render the `sources` array verbatim from fixture data (`DuplicateClusterPanel.tsx:52-64`; source strings at `fixtures.py:66,172,270`).
- Frontend audit seed logs a synthetic `"clustered"` event with `finding_count`/`sources` in metadata (`mockProvider.ts:253-261`) — generated at startup, no real clustering occurred.

## The 8 dedup scenarios PS16 expects (required logic — all absent)
Person 1's dedup must decide, per pair of findings, whether they collapse into one `Cluster`. Expected scenarios:
1. **Exact duplicate** — same scanner rule, same asset, identical raw evidence → dedup.
2. **Same vuln, different line** — same rule/CVE, different source line in same file → dedup.
3. **Cross-scanner duplication** — nuclei + semgrep + burp all report the same vulnerability → one cluster (this is what CASE-001 *pretends*: `sources=["nuclei","semgrep","burp"]`, `finding_count=3`, `fixtures.py:66-67`).
4. **Same CWE, different vulnerability** — shared weakness class but distinct vulns → do NOT dedup.
5. **Different asset** — identical signature on two hosts → separate findings/clusters.
6. **Different endpoint** — same rule, different URL/port → separate or grouped per policy (PS16 requires a decision rule).
7. **Parameter variants** — same endpoint, differing injection param → dedup as one logical finding.
8. **Layer / SCA / SAST / DAST** — same library issue reported by npm-audit (SCA), semgrep (SAST), and DAST must be reconciled (see also `CORRELATION.md`).

None of these decision rules exist; there is no code that ever compares two findings (master doc Phase 5).

## What a correct runtime must produce per Cluster (all absent)
- `finding_ids` — the actual distinct findings merged (never populated anywhere; `Cluster` unused).
- `primary_finding_id` — canonical representative (absent).
- `dedup_confidence` — numeric match confidence (absent).
- `dedup_method` — which scenario/algorithm decided (e.g. "cve+asset+endpoint"; absent).
- The pipeline feeding it: `POST /api/findings → normalize → dedup → Cluster → TriageCase` (master doc Phase 24 step 2).

## What exists today that *looks* like dedup, and what it actually is
| Element | Appearance | Reality | Evidence |
|---|---|---|---|
| `Cluster` model | dedup output schema | dead code | `models.py:27-32` |
| `cluster_id` on cases | a cluster was formed | fixture literal | `fixtures.py:63` |
| `finding_count` | dedup counted findings | hand-written constant | `fixtures.py:67` |
| DuplicateClusterPanel chain | normalized+deduped | renders constant | `DuplicateClusterPanel.tsx:26,44` |
| `"clustered"` audit event | lifecycle shows clustering | synthetic seed | `mockProvider.ts:253-261` |
| Demo scenario #3 ("three scanners → one incident") | dedup working | MOCK — fixture constants | master doc Phase 17 |

## Verification status
- No dedup code → no tests. NOT EXECUTED (branches_docs.md §13: zero dedup/cluster tests). Backend test suite covers mock AI only; frontend covers EvidencePanel rendering only.

## Merge gate
- Gate "Dedup exists" (`Finding → Cluster`) = FAIL → **MERGE BLOCKER #3** (master doc Phase 25). Required deliverable: ingestion response path that groups `Finding` objects into `Cluster` objects per the 8 scenarios above (master doc Phase 24 step 2).