# CyberYukti — Ingestion

**Status: NOT IMPLEMENTED.** No endpoint, parser, or instantiations exist. Person 1's entire deliverable is absent. See `docs/MASTER_SYSTEM_DOCUMENTATION.md` Phase 5; `branches_docs.md` §7, §12.

## What would need to exist
1. **`POST /api/findings`** — accept raw scanner output. Not present: grep for any `@router.post("/findings")` or ingestion route returns 0 hits (master doc Phase 5).
2. **Format parsers** — JSON, SARIF, JSONL. None exist. No code converts scanner artifacts in any format (master doc Phase 5: "No route accepts scanner findings in any format").
3. **Canonical `Finding` population** — instantiate the model with the parsed payload. Model exists, unused.
4. Nominal flow the endpoint must feed: `finding → normalize → dedup Cluster → TriageCase` (master doc Phase 16 pipeline; Person 1 branch sequence in Phase 24).

## Endpoint expectations (PS16) — with the per-format parsing gap
| Input format | Example producer | Required mapping (absent) |
|---|---|---|
| JSON | nuclei template output, snyk | top-level finding objects → `Finding` fields (`models.py:13-24`) |
| SARIF | semgrep, sarif-emitting scanners | `runs[].results[].ruleId` → `scanner_rule_id`; `locations` → asset; `message` → `title` |
| JSONL | streaming DAST/cloud scanners | per-line event → one `Finding` |

No parser code exists for any row; nothing reads a file, reads stdin, or accepts a multipart body.

## Models defined but UNUSED (ingestion's schema is ready, the code is not)
- **`Finding`** (`models.py:13-24`) — 11 fields: `finding_id`, `cluster_id`, `scanner`, `scanner_rule_id?`, `cve?`, `cwe?`, `title`, `description?`, `asset` (Asset), `raw_evidence?`, `observed_at`. Imported at `fixtures.py:4` but **never instantiated anywhere** (master doc Phases 5, 19).
- **`Cluster`** (`models.py:27-32`) — `cluster_id`, `finding_ids`, `primary_finding_id`, `dedup_confidence`, `dedup_method`. Imported at `fixtures.py:5`; never instantiated.
- `Asset` (`models.py:5-10`) is usable as-is for probe targets; the fixture assets (`fixtures.py:13-59`) are demo data, not discovered assets.

## Scanner-integration vs scanner-fixture distinction
- **`sources=["nuclei","semgrep","burp"]`** on CASE-001 (`fixtures.py:66`), CASE-003 (`fixtures.py:172`), CASE-005 (`fixtures.py:270`) are **name strings**. They record "which scanners supposedly reported this case" — attribute data, not integration.
- No scanner binary, no scanner API client, no subprocess, no outbound request to any scanner exists (master doc Phase 6: grep for `subprocess`/`docker`/`requests.get`/`httpx.get` = 0 hits).
- An added wrinkle: some fixture values look like scanner output but are authored text — e.g. nested fake HTML in `observed_value` (`fixtures.py:229,237`) and fake CVEs (`fixtures.py:68`) — demonstrating these were written by a demo author, not collected.
- A real integration means: a scanner artifact arriving **in** → normalized → stored. Today the system begins at the "6 already-triaged cases" step; the arrival step does not exist (master doc Phase 16).

## Effect of the gap
- Evidence panels, DuplicateClusterPanel, and AI analysis all consume `TriageCase` dicts that begin in `fixtures.py` (`CASES:363-370`). Nothing can produce a `TriageCase` from live data.
- PS16 requirement "Finding normalization" → NOT SATISFIED; gateway blocker for the whole pipeline (master doc Phases 21, 25).
- Demo scenario #4 ("malicious scanner output → sanitized") is only PARTIAL: the sanitizer/grounding layer works against a mock provider, but the scanner-to-ingestion leg that scenario supplies never existed (master doc Phase 17).

## Verification status
- No ingestion logic to test → 0 tests reference `POST /api/findings`. Test suite covers only mock-provider AI + React rendering (branches_docs.md §13). Ingestion execution: **NOT EXECUTED** (impossible — no code).

## Merge gate
- Gate "Ingestion exists" = FAIL → **MERGE BLOCKER #1 of 8** (master doc Phase 25).
- Ownership: Person 1; recommended next step after making `person4` the default branch (master doc Phase 24).