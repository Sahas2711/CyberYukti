# CyberYukti — Configuration

Status: VERIFIED — 6 env vars, all optional at runtime; defaults make the app run mock-only out of the box.

Repository `.env.example` (committed, empty placeholders; `.env` is gitignored and NOT committed — `.gitignore:17-19`):

```bash
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
USE_MOCK_AI=true
NEXT_PUBLIC_USE_MOCK=true
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Variable table

| Var | Read by | Default | Effect |
|---|---|---|---|
| `OPENAI_API_KEY` | `openai_provider.py:24` | "" (unset) | If empty → OpenAIProvider falls back to MockProvider (`:30-32`). Key is never logged/committed. |
| `ANTHROPIC_API_KEY` | `anthropic_provider.py:24` | "" (unset) | If empty → fallback to MockProvider (`:30-32`). |
| `USE_MOCK_AI` | `engine.py:18` | `true` | Truthy (`true`/`1`/`yes`) forces MockProvider and disables real AI entirely. **Default = mock.** Only read if mock is disabled to reach `AI_PROVIDER` selection. |
| `AI_PROVIDER` | `engine.py:23` | `openai` | Chooses Provider when mock is off: `anthropic` → AnthropicProvider, else OpenAIProvider. Unknown values silently route to OpenAI. |
| `OPENAI_MODEL` | `openai_provider.py:25` | `gpt-4o` | Model string for OpenAI chat.completions when mock disabled + key present. |
| `ANTHROPIC_MODEL` | `anthropic_provider.py:25` | `claude-sonnet-4-20250514` | Model string for Anthropic messages.create when mock disabled + key present. |
| `NEXT_PUBLIC_USE_MOCK` | `providers.ts:10` | `true` | **Logic is `!== "false"`.** Any value except the literal string `false` selects the mock provider (`createMockProvider()`). Only `"false"` enables `createRealProvider()`. |
| `NEXT_PUBLIC_API_URL` | `client.ts:1` | `http://localhost:8000` | Base URL prepended to every API fetch. Must match backend CORS allow-list — only `http://localhost:3000` origin is trusted for the browser (`main.py:13-19`). |

Notes
- Docs vars: `USE_MOCK_AI=true` in `.env.example` is redundant with the code default (`engine.py:18`) — mock is forced with or without `.env`.
- `python-dotenv` is a declared dependency (`pyproject.toml:11`) but never imported; `.env` is not loaded by `main.py`. Values must come from the shell environment or the runner.
- Backend env vars are read at provider-construction time, not per-request; changing them requires a restart.
- Secret hygiene: value `OPENAI_API_KEY=sk-...` committed would trip the audit secret scan; scan of full history is clean (Phase 1).

Component → variable read map (VERIFIED against source)
- Backend AI engine: reads `USE_MOCK_AI`, `AI_PROVIDER` (`engine.py:18,23`).
- Backend OpenAI provider: reads `OPENAI_API_KEY`, `OPENAI_MODEL` (`openai_provider.py:24-25`).
- Backend Anthropic provider: reads `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` (`anthropic_provider.py:24-25`).
- Frontend provider switch: reads `NEXT_PUBLIC_USE_MOCK` (`providers.ts:10`).
- Frontend API client: reads `NEXT_PUBLIC_API_URL` (`client.ts:1`).
- Case/approval/audit/dashboard routes: read NO env vars — they operate purely on fixtures + in-memory stores.
- `python-dotenv` / `httpx`: declared in `pyproject.toml:10-11`, imported by no component.

Standard run matrix

| `USE_MOCK_AI` | `OPENAI/ANTHROPIC_API_KEY` | `NEXT_PUBLIC_USE_MOCK` | Runtime that results |
|---|---|---|---|
| unset or `true` | anything | anything except `"false"` | Backend + frontend mock (default) |
| `false` | unset | — | Backend still mock — both providers fall back on missing keys (`openai_provider.py:30-32`, `anthropic_provider.py:30-32`) |
| `false` | set (one or both) | — | Backend real LLM via `AI_PROVIDER`, subject to sanitizer + validator + fallback chain (sanitizer/validator are executed regardless) |
| — | — | `"false"` | Frontend realProvider: hits backend on 8000; falls back to mock per-request on any error (`realProvider.ts`) |

- `AI_PROVIDER` semantics: value `anthropic` → Anthropic; ANY other string → OpenAI (incl. typos). No unknown-provider error is raised (`engine.py:23-28`).
- Frontend flag nuance: only the EXACT string `"false"` disables the mock; `"False"`, `"0"`, or empty all keep mock active (`providers.ts:10`).