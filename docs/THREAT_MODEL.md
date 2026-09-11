# CyberYukti — Threat Model

**Status:** Adversarial analysis of the as-built fixture workbench. Today 0 CRITICAL / 0 HIGH / 1 LOW; the material gaps are no auth, unvalidated analyst fields, 500 exception leakage, and the absent ingestion/sandbox surfaces.

## Threat actors
1. **Untrusted scanner payloads** — PS16 ingestion path does not exist; nearest analog is fixture `observed_value` text embedding "IGNORE ALL PREVIOUS INSTRUCTIONS…" and `<script>…</script>` (`fixtures.py:229,237`).
2. **Malicious analyst / local user** — can call the API directly; `analyst_id` is self-asserted.
3. **Remote attacker vs API** — 9 unauthenticated endpoints on :8000.
4. **Supply chain** — runtime deps `openai`, `anthropic`, Next.js/React; `httpx` declared but unused (`pyproject.toml`).

## Surface × actor × mitigation × gap matrix
| Actor | Surface | Mitigation present (REAL) | Remaining gap |
|---|---|---|---|
| Scanner payload | AI prompt path (title/evidence → sanitizer → LLM) | `<UNTRUSTED>` wrap+strip (`sanitizer.py:40-44`); system prompt rule 1 (`system_prompt.txt`); number/CVE grounding (`validator.py:63-108`) | Paid LLMs never tested under adversarial input (**NOT EXECUTED**); ingestion surface itself absent |
| Scanner payload | React rendering (EvidencePanel) | Default text escaping; no `dangerouslySetInnerHTML`/`eval`; 8 injection tests (`injection-ui.test.tsx:6-61`) | Only EvidencePanel tested — 24 other components untested |
| Malicious analyst | approve/reject/override | Guard logic 400/404/409 (`approval_routes.py:39-134`) | No auth (`analyst_id` verbatim, `:46,76,106`); `reason` unbounded; no rate limit; override lacks a 409 gate |
| Malicious analyst | analyze route | Engine fallback chain never exposes keys/prompts (`engine.py:45-104`) | 500 leaks `str(e)` (`ai_routes.py:21-22`) |
| Remote attacker | API :8000 | CORS localhost-only (`main.py:13-19`); no secrets in tree | No auth, no rate limiting; local-only posture, not production |
| Supply chain | deps at build/run | Version ranges pinned (`pyproject.toml`, `package.json` — master doc Phase 11) | No SBOM/dependency scanning; stale docs reference deleted components (Phase 19) |

## Likelihood / impact ratings (qualitative, as-built)
| Actor | Likelihood today | Impact if realized | Key driver |
|---|---|---|---|
| Scanner payload | LOW (surface absent) | HIGH-med | No ingestion path exists yet |
| Malicious analyst | LOW (localhost trust) | MEDIUM | No auth; fixture store corruption only |
| Remote attacker | LOW-MED (localhost-only CORS; no public deployment) | MEDIUM | No rate limit, no auth |
| Supply chain | LOW (pinned versions) | HIGH | Untested runtime snapshots |

## STRIDE-style mapping (quick)
- **Spoofing:** `analyst_id` self-asserted → any caller impersonates (`approval_routes.py:46`).
- **Tampering:** audit `prev_hash` is an event_id reference, not a hash (`approval_routes.py:22`) — revocable in memory.
- **Repudiation:** no signatures on audit events (`AUDIT_TRAIL.md`).
- **Information disclosure:** 500 `str(e)` (LOW, `ai_routes.py:21-22`); dashboard exposes fixture only.
- **DoS:** no rate limiting (master doc Phase 10).
- **Elevation:** none — no admin concept exists.

## Exposure notes
- **No subprocess/network/file surface** exists on the backend — even an unvalidated `reason` ends as a JSON dict value that is stored and re-rendered, never executed (`approval_routes.py:56-62`).
- **Prompt-injection materials ARE present** in fixture data (`fixtures.py:229,237`) and render inert in the UI — good empirical evidence for React escaping, but they never reach a real LLM today.
- **No 401/403 anywhere** — the API has no identity concept; the only access-control-like gate is the 409 already-decided check on approve/reject (`approval_routes.py:53-54,84-85`).
- **Future, non-vacuous risks** once Persons 1–3 land: probe-sandbox escape + SSRF via probe targets (`SANDBOX_SECURITY.md`), prompt injection into a real LLM, and fabricated CVEs (`CVE-2099-9999`, `fixtures.py:272`) passing the input-presence grounding check (`validator.py:104-106`).

## Suggested mitigations (NONE implemented)
- API-key/JWT auth on decision endpoints; validate `reason`/`analyst_id` (length, charset).
- Replace 500 `str(e)` with a generic detail (`ai_routes.py:21-22`) + server-side logging.
- Rate limiting; narrow CORS `allow_methods` (`main.py:17`).
- Grounding validator should reject year > current CY — blocks fabricated `CVE-2099-*`.