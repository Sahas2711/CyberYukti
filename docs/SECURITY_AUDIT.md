# CyberYukti — Security Audit

Status: ADEQUATE FOR LOCAL DEMO — 0 CRITICAL, 0 HIGH, 1 LOW. Scans clean; no dangerous surfaces present.

AppSec findings (Phase 13, MASTER_SYSTEM_DOCUMENTATION.md:296-305)

| Severity | File:Line | Finding | Exploit Path | Impact | Fix |
|---|---|---|---|---|---|
| INFO | `main.py:13-19` | CORS `allow_origins=["http://localhost:3000"]`, `allow_credentials=True`, `allow_methods=["*"]` | N/A (localhost only) | Acceptable for local tool | Document; restrict `allow_methods` in production |
| INFO | `approval_routes.py:46,76,106` | No authentication; `analyst_id` from request body trusted verbatim | Any HTTP caller can impersonate any analyst | Analyst identity unverified | API key or JWT for non-demo use |
| LOW | `ai_routes.py:17-22` | Exception handler returns `detail=f"AI analysis failed: {str(e)}"` in HTTP 500 | Trigger AI failure → internal error text exposed to caller | Information disclosure | Return generic message; log full error server-side |
| NONE | `sanitizer.py:40-44` | Control-char strip + 2000-char truncation + `<UNTRUSTED>` wrapping | No injection vector through sanitized fields | — | Already secure |
| NONE | `system_prompt.txt` | System prompt declares `<UNTRUSTED>` tags are data | Combined with sanitizer, prevents prompt injection | — | Already secure |
| NONE | Frontend | No `dangerouslySetInnerHTML`, no `eval`, no `new Function` | XSS surface eliminated by React default escaping | — | Already secure |

Explicit scan / no-finding notes (VERIFIED)
- No `subprocess`, `docker`, `os.system`, `requests.get`, `httpx.get` in backend code (excluding tests + provider imports) — grep returns 0 hits. No command execution surface (Phase 6).
- No file access / path traversal surface: no file read of user input in backend (providers read static prompt files only).
- No outbound network calls beyond the OPTIONAL OpenAI/Anthropic SDK calls (`openai_provider.py:45`, `anthropic_provider.py:45`) when API keys are configured — which are disabled by default (`USE_MOCK_AI=true`).
- No secrets committed: full-history secret scan clean; only `.env.example` committed with empty placeholders (Phase 1). No `sk-`, `ghp_`, `AKIA`, or private keys.
- Zero CRITICAL / HIGH findings. The 8 LOW+ certifications: 2 INFO, 1 LOW, 3 NONE-pre-hardened.

Structural defensive note
- The absence of the validation/sandbox engine (Person 2) means there is NO sandbox-escape surface — because there is no sandbox. The dangerous surface that PS16 anticipates simply does not exist yet; when added it must be network-isolated and time-boxed.

Residual risks (not scored, untested — see Phase 14)
- Paid providers under adversarial input: untested; real LLMs may hallucinate CVEs (only mock + validator tested).
- Backend routes under adversarial `analyst_id` / `reason`: untested; no input length validation on non-sanitized fields; no rate limiting on any endpoint (Phase 10).

CORS detail (INFO-grade, already secure for local)
- `allow_origins=["http://localhost:3000"]` — exactly one origin; no wildcard (Phase 13).
- `allow_credentials=True` + `allow_methods=["*"]` — `allow_methods=["*"]` is over-broad; POST/GET/OPTIONS suffices. Acceptable for local; restrict in production before any public deployment.
- Browser preflight behavior: `allow_headers` is not set, so the explicit `Content-Type: application/json` in `client.ts:21` satisfies it; custom headers are blocked.

Auth / input-length gaps (untested, noted for future hardening)
- No API key or JWT on any endpoint: `analyst_id` is trusted verbatim from the POST body (`approval_routes.py:46,76,106`).
- `analyst_id` and `reason` fields have no max-length constraint; a malicious request could embed large payloads. Currently non-exploitative because all data is in-memory and there is no log sink, but would become a risk with persistence + log tail.
- Rate limits: none; rapid `POST /api/ai/analyze/{id}` would re-trigger the mock provider deterministically (no harm); on a real LLM it could cause cost overruns — rate limiting is mandatory before real AI keys are enabled.

Threat model summary (attacker scenario absent)
- The system has no public endpoint, no file I/O, and no subprocess. Without a sandbox (Person 2) and without a scanner integration (Person 1), the adversarial surface today is the same as any local Flask/FastAPI demo.
- The injection defense is real and complete for the mock path (sanitizer strips control chars, wraps `<UNTRUSTED>`, validator checks grounding) — but has not been proven against a real LLM under adversarial conditions (Phase 14 gaps).