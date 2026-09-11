# CyberYukti — Correlation

**Status: NOT IMPLEMENTED.** No SAST↔DAST (or any cross-scanner) correlation logic exists. Findings are never compared, joined, or reasoned over. Related PS16 requirements (cross-scanner dedup/reconciliation) → NOT SATISFIED (master doc Phase 21).

## What correlation means here (PS16)
- Cross-reference findings from **different scanner families** that describe the same underlying issue:

  | Family | Example sources | What it sees | Fixture analogue |
  |---|---|---|---|
  | SAST (static) | semgrep | source code pattern ("insecure query string in login handler") | `semgrep` in `sources` (`fixtures.py:66`) |
  | DAST / network | nuclei, burp, acunetix | runtime behavior ("SQL error returned by /api/v2/login") | `nuclei`, `burp` (`fixtures.py:66`) |
  | SCA (dependency) | npm-audit, snyk | library version ("jQuery < 3.5.1 present") | `npm-audit`, `snyk` (`fixtures.py:119`) |

- Goal: enrich one case with evidence from every relevant sensor and confirm the vuln is real in *this* deployment (master doc Phase 5: "Correlation logic — cross-references SAST ↔ DAST findings from different scanners").
- Required, absent outputs: (1) a mapping that the same `title`/`CWE`/`asset`/endpoint seen by SAST and DAST is one issue; (2) joined evidence records (per-sensor `EvidenceObservation` so that `ValidationResult.observations` mix probe and scanner evidence — `models.py:35-50`); (3) conflict resolution (SAST says X, DAST contradicts → see `CASE-002`/`CASE-005` patterns).

## Why `sources=["nuclei","semgrep","burp"]` is data, not correlation
- CASE-001 (`fixtures.py:66`), CASE-003 (`fixtures.py:172`), CASE-005 (`fixtures.py:270`) carry a `sources` list that includes all three scanner types — which *reads* like "SAST + DAST agreed."
- It is a **string list baked into a `TriageCase` constructor** — attribute data about the fixture, not a correlation computation:
  1. No logic joins a semgrep finding to a burp finding; the list is authored by hand (`fixtures.py:61-361`).
  2. No per-source `Finding` records exist to correlate — `Finding` is never instantiated (`models.py:13-24`, UNUSED; master doc Phase 5).
  3. `finding_count` (e.g. 3 for CASE-001, `fixtures.py:67`) is a hardcoded literal that happens to equal the number of `sources`, and is reused verbatim by the DuplicateClusterPanel and the audit seed (`DuplicateClusterPanel.tsx:26`, `mockProvider.ts:260`) — so the UI *implies* a correlation/dedup result that was never produced (master doc Phase 20).
- No correlation, merge, or join function exists anywhere in the backend (grep for correlation/cluster-merge logic: 0 hits; master doc Phase 5).

## Correlation vs the AI layer (what *does* run, and on what)
- The AI engine's `grounded_on` + validator (`validator.py:63-108`, `140-171`) references **fields of a single case dict** — e.g. `grounded_on=["evidence.status", ...]` (`mockProvider.ts:154`) — it never reasons across multiple findings/scanners.
- `MockProvider.analyze` concatenates whatever `case["sources"]` holds into prose (`mock_provider.py:20-57`: `Cluster contains {finding_count} finding(s)`) — pass-through of fixture constants, not sensor fusion.
- Result: cross-scanner context is only synthetically staged in fixture text (e.g. `CASE-002` "npm-audit and snyk flagged... but direct package inspection confirms patched" at `mockProvider.ts:158-159`), which a real correlation pipeline would be responsible for producing.

## Conflict-resolution matrix a real correlator must implement (absent)
| SAST | DAST | Verdict expected |
|---|---|---|
| flags vuln | confirms behavior | CONFIRMED (join evidence → one case) |
| flags vuln | contradicts (e.g. patched version) | NOT_CONFIRMED (case still scored low) |
| flags vuln | inconclusive | INCONCLUSIVE (needs probe) |

These are today expressed only as fixture `evidence.status` constants (`fixtures.py:71,124,222`) and template narrative (`mockProvider.ts:158-163`); no logic decides them.

## Target placement (master doc Phase 22, 24)
- Correlation slots between normalization and evidence validation:
  `scanner artifacts → normalization → correlation/dedup (Cluster) → evidence sandbox → scoring → AI explanation`.
- Owned by Person 1 (with Person 2's validation output feeding it). No branch or code exists. Merge gate lands under "Dedup exists" = FAIL → **MERGE BLOCKER #3** (master doc Phase 25).

## Verification status
- No correlation code → no tests. NOT EXECUTED (branches_docs.md §13).

## Bottom line
- What exists is the *display* of a correlated outcome (sources + finding_count on fixtures and in the mock audit log); the *mechanism* that justifies that display is entirely absent. The honest label for `sources` is **fixture metadata**, not correlation evidence.