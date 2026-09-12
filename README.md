# CyberYukti 🛡️
### Autonomous Vulnerability Triage & Evidence Engine (PS16)

Ingests noisy multi-scanner findings (Trivy / Semgrep / Nuclei), deduplicates them with a
3-tier enterprise dedup engine, validates evidence, scores priority, explains findings with
an AI analyst-assist layer, and records every decision in an append-only audit trail —
served as **one web app** (Next.js UI + FastAPI API).

---

## 🚀 Run CyberYukti — pick ONE

### OPTION 1 — Web / Development

Requires: **Python 3.11+** and **Node 20+**.

```bash
# 1) Backend (API on http://localhost:8000, docs at /docs)
pip install -r requirements.txt "httpx>=0.25.0" "python-dotenv>=1.0.0"
python run_server.py

# 2) Frontend (dev server on http://localhost:3000)
cd frontend
npm ci
npm run dev
```

Open **http://localhost:3000**. The frontend talks to the backend at
`NEXT_PUBLIC_API_URL` (default `http://localhost:8000`).

Run the test suites:

```bash
python -m pytest backend/tests backend/app/ai/tests -v   # backend
cd frontend && npm test                                  # frontend
```

### OPTION 2 — Windows EXE (no Python/Node needed)

1. Download **`CyberYukti-Windows-x64.zip`** from the latest successful
   **Build & Release** workflow run (Actions → Build & Release → artifacts), or from a
   GitHub Release if one exists.
2. Unzip and double-click **`CyberYukti-Windows-x64.exe`**.
3. Open **http://localhost:8000** — the full UI and API run from that single file.
4. Stop with `Ctrl+C` in the console window.

> SmartScreen may warn about an unsigned binary — choose *More info → Run anyway*.
> The EXE starts in **demo mode** (bundled demo data + offline mock AI). No internet,
> keys, or installs required.

### OPTION 3 — Docker

```bash
docker pull ghcr.io/<owner>/cyberyukti:latest
docker run --rm -p 8000:8000 ghcr.io/<owner>/cyberyukti:latest
```

Open **http://localhost:8000** (UI + API on the same port). One image contains the
complete application; the container is healthchecked and runs as a non-root user.

---

## 🧪 Demo mode

All packaged formats (EXE, Docker) default to a **safe demo configuration**:

| Behavior            | Default                                   |
| ------------------- | ----------------------------------------- |
| Frontend data       | Bundled demo cases (`NEXT_PUBLIC_USE_MOCK=true` baked into the packaged UI) |
| AI analysis         | Offline mock provider (`USE_MOCK_AI=true`) |
| Network             | No external calls, no API keys needed     |

Real LLM analysis (optional): set `USE_MOCK_AI=false` plus `AI_PROVIDER=openai|anthropic`
and the matching key (see `.env.example`). Keys are **never** committed.

## ⚙️ Environment variables

| Variable                | Default                 | Purpose                              |
| ----------------------- | ----------------------- | ------------------------------------ |
| `PORT`                  | `8000`                  | HTTP port (EXE & Docker)             |
| `USE_MOCK_AI`           | `true`                  | Offline mock AI provider             |
| `AI_PROVIDER`           | `openai`                | `openai` or `anthropic`              |
| `OPENAI_API_KEY`        | —                       | Only when `USE_MOCK_AI=false`        |
| `OPENAI_MODEL`          | `gpt-4o`                | OpenAI model                         |
| `ANTHROPIC_API_KEY`     | —                       | Only when `USE_MOCK_AI=false`        |
| `ANTHROPIC_MODEL`       | `claude-sonnet-4-…`     | Anthropic model                      |
| `NEXT_PUBLIC_USE_MOCK`  | `true` (packaged UI)    | Frontend demo data source            |
| `NEXT_PUBLIC_API_URL`   | `http://localhost:8000` | Backend URL for web/dev frontend     |

Build metadata (commit SHA, timestamp, environment) is exposed by the packaged app at
`/api/build-info` and printed at EXE startup.

## 🔁 Build & release process

`.github/workflows/build-release.yml` runs on every push/PR to `main`:

```
validate (ubuntu)      exe (windows-latest)         docker (ubuntu)
├─ backend tests       ├─ static UI build           ├─ docker build (multi-stage)
├─ frontend lint+test  ├─ PyInstaller one-file EXE  ├─ tags: latest + commit SHA
├─ static web build    ├─ EXE launch smoke test     ├─ GHCR push (main only)
└─ web build artifact  └─ CyberYukti-Windows-x64.zip└─ container smoke test
```

- **PRs**: validation + Docker build only (nothing published).
- **Pushes to `main`**: everything builds; EXE, web build, and build metadata are
  uploaded as artifacts; image is pushed to `ghcr.io/<owner>/cyberyukti`
  (`latest` + SHA).
- **Tags `v*`**: additionally creates a GitHub Release containing the Windows EXE.
- Every job fails the workflow if lint, tests, builds, or smoke tests fail.

## 🧱 Application architecture (unchanged)

- **Backend** — FastAPI (`backend/app`): ingestion + 3-tier dedup, shared case store,
  evidence validation, deterministic risk scoring (`services/risk_engine`), AI
  analyst-assist (`backend/app/ai`), approvals, audit trail, dashboard stats.
- **Frontend** — Next.js 14 App Router (`frontend/`): triage dashboard, case workspace,
  approval controls, audit timeline. Talks to the API over HTTP; can also run fully
  offline on bundled demo data.
- **Packaging** — one process serves both: the UI is statically exported
  (`BUILD_STATIC_EXPORT=true`) and embedded (`backend/static-ui/`), then served by the
  same FastAPI app (`run_cyberyukti.py` → `dist/CyberYukti-Windows-x64.exe` or the
  Docker image).
