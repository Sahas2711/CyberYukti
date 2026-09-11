# CyberYukti — UI Audit (`UI_AUDIT.md`)

**Date:** 2026-09-11 · **Scope:** entire `frontend/` tree (45 files: 3 pages, 17 components, 5 lib/api files, configs, tests) + frontend↔backend contract check against `backend/app`
**Method:** full file-by-file read; static verification (`tsc --noEmit` clean, `next lint` clean, `vitest` 8/8 pass); cross-check of every API path/payload against FastAPI routes; one empirical component test to confirm the critical finding.

## Automated results (at audit time)

| Check | Result |
| --- | --- |
| `tsc --noEmit` | ✅ 0 errors |
| `next lint` | ✅ 0 warnings/errors |
| `vitest run` (injection-ui) | ✅ 8/8 pass |
| Backend pytest (23 tests) | ✅ pass |

## Verdict

Solid dark "SOC console" design system (custom Tailwind palette, consistent `hk-label`
micro-typography, disciplined spacing), strong injection-safe evidence rendering, and a
clean provider abstraction. But there is **1 critical functional bug that blocks the core
Approve workflow**, several contract/UX gaps, and ~40 issues in total. Details below.

---

## P0 — Critical (blocks a core workflow)

### A1. Approve case is impossible — confirm-state resets itself
- **File:** `frontend/components/case/ApprovalControls.tsx:73-78`
- **Bug:** `handleApproveClick()` runs `setConfirming(true)` then immediately calls
  `resetModal()`, whose first statement is `setConfirming(false)`. Both run in the same
  handler, so the last write wins: the button never shows "Click again to confirm" and
  `getProvider().approveCase()` can never be called from the UI.
- **Verified:** empirical render test — after clicking "Approve case", the
  "Click again to confirm" state never appears (test failed as expected).
- **Fix:** remove the `resetModal()` call from the first-click branch (or replace with
  `setError(null)` only).
- **Impact:** the #1 analyst action (approve) is dead in every deployment mode. Backend
  and mock provider both support it.

---

## P1 — High (wrong behavior users will hit)

### B1. Filters silently reset when "Reset" is clicked from the dashboard-embedded table
- **File:** `frontend/components/dashboard/CaseTable.tsx:131-137` (`resetFilters`) and
  `168-176` (select onChange)
- **Bug:** every filter change and `resetFilters()` calls
  `router.replace("/cases?…")`. Embedded on the dashboard (`app/page.tsx`), this
  **navigates the user away from `/` to `/cases`** just for filtering. `resetFilters`
  also always navigates, even when already on `/cases` (history churn, lost scroll).
- **Fix:** navigate only when rendered on `/cases` (e.g. prop `syncUrl`) or use local
  state without `router.replace` for the dashboard embed.

### B2. "Priority Queue" sidebar link does not actually filter to priority
- **File:** `frontend/components/shared/Sidebar.tsx:24` +
  `app/cases/page.tsx:33`
- **Bug:** link is `/cases?priority=P1`, but `CasesPageInner` reads the param into
  `initialPriority` and passes it only as an *initial* value. The navigation itself is
  a no-op: navigating to `/cases?priority=P1` from `/cases` re-renders the same
  component; `useState(initialPriority)` **does not re-run**, so the select still shows
  ALL and the sidebar's active state lies.
- **Fix:** key `CaseTable` by the query string or derive filter state from
  `useSearchParams` reactively.

### B3. Same staleness bug for "Evidence Queue" link
- **File:** `frontend/components/shared/Sidebar.tsx:31` — same mechanism as B2 with
  `?evidence=CONFIRMED`.

### B4. "Analyst-1" is hardcoded; no session/user concept
- **Files:** `frontend/lib/api/realProvider.ts:44,60,74` (`analyst_id: "analyst-1"`),
  `TopHeader.tsx:96` (`analyst-1`), mock provider
- **Bug:** every approve/reject/override is recorded in the audit trail as `analyst-1`
  regardless of who operates the tool. For an auditable-triage product this undermines
  the audit value.
- **Fix:** a user/identity switcher or env-based identity
  (`NEXT_PUBLIC_ANALYST_ID`), passed through the provider.

### B5. `ApiError` status 0 is unreachable; network failures still handled, but `TypeError` double-check is dead code
- **File:** `frontend/lib/api/realProvider.ts:10-14`
- **Bug:** `describeError` checks `err.status === 0 || err instanceof TypeError` inside
  the `ApiError` branch, but `fetch` throws `TypeError` before an `ApiError` exists —
  the `ApiError` branch can never see `TypeError`. Harmless but dead logic; the network
  path relies solely on the second block.
- **Fix:** drop the redundant `TypeError` check in the `ApiError` branch.

### B6. Provider type imported from the mock module
- **File:** `frontend/lib/providers.ts:1`,
  `realProvider.ts:10` (`import type { Provider } from "./mockProvider"`)
- **Bug:** the *real* provider's interface is defined in the mock file
  (`mockProvider.ts` exports `interface Provider`). Any mock-only change breaks the
  real provider's type contract; circular-ish coupling.
- **Fix:** move `interface Provider` into `lib/api/types.ts` (or a dedicated
  `provider.ts`).

### B7. Dashboard stats KPI "Pending Review" can disagree with queue counts
- **Files:** `app/page.tsx:88` (`pending = cases.filter(...)`), 
  `backend/app/api/dashboard_routes.py` (stats without `pending`)
- **Bug:** pending is computed client-side from `listCases()`; if the backend list is
  truncated/paginated in the future, KPIs and queue disagree. Minor today (6 cases),
  but a silent inconsistency for a "single source of truth" claim.
- **Fix:** backend `/api/dashboard/stats` should own `pending`.

### B8. Docker/EXE demo parity: `stats.ingestion` is unused by the UI
- **Files:** `backend/app/api/dashboard_routes.py` (adds `stats.ingestion`),
  `app/page.tsx:65-70` (uses `/api/v1/report` only)
- **Bug:** backend embeds ingestion summary into stats, and the frontend separately
  fetches `/api/v1/report`; two sources for the same truth. If `/api/v1/report` 404s
  (fresh backend without ingestion run), the dashboard shows the "No ingestion run
  yet" empty state even though `stats.ingestion` exists.
- **Fix:** prefer `stats.ingestion` when present; drop the second request.

---

## P2 — Medium (quality, robustness, polish)

### C1. `PipelineStrip` component is dead code
- **File:** `frontend/components/dashboard/PipelineStrip.tsx` (115 lines)
- **Bug:** imported nowhere; excluded from Tailwind's content scan? No — content covers
  `components/**` so classes are kept, but the component is never rendered. Its labels
  ("Validated/Prioritized/Decisions") duplicate `CasePipeline` on the case page.
- **Fix:** delete it or wire it into the dashboard.

### C2. Table row uses div-like keyboard semantics without `role`
- **File:** `frontend/components/dashboard/CaseTable.tsx:279-295`
- **Bug:** rows are `tabIndex={0}` + click/Enter/Space handlers with `aria-label`
  (good), but no `role="link"`/`role="button"`; screen readers announce them as plain
  rows with an odd label. The `▲/▼` sort indicators are inside the button text, so
  announced as literal characters.
- **Fix:** add `role="button"` (or move navigation into a real `<a>` overlay), and
  use `aria-sort` on `<th>` + hidden text like "sorted ascending".

### C3. Sortable `<th>` lacks `aria-sort`
- **File:** `frontend/components/dashboard/CaseTable.tsx:207-247`
- **Bug:** sighted users get ▲/▼; AT users get nothing.

### C4. Filter `<select>` in a `<label>` without visible text association on dashboard embed
- **File:** `frontend/components/dashboard/CaseTable.tsx:161-166`
- **Bug:** `<span class="hk-label">Priority</span>` is inside the `<label>`, which does
  associate, but the select *also* has `aria-label` which **overrides** the label text
  — acceptable but redundant; the label element is then pointless.

### C5. Mock provider deep-clones everything via JSON
- **File:** `frontend/lib/api/mockProvider.ts` (`JSON.parse(JSON.stringify(...))` in
  `listCases`/`getCase`/mutation returns)
- **Bug:** works, but every poll deep-clones all fixtures; `analyzeCase` mutates the
  shared `_cases` store (a second browser tab on the same origin would share the
  module-level state). Acceptable for a demo; fragile as a pattern.

### C6. `EvidencePanel` re-derives `inconclusiveReasons()` on every render
- **File:** `frontend/components/case/EvidencePanel.tsx:76-101`
- **Bug:** called inline in JSX; not memoized. Small arrays — cosmetic.

### C7. `Key={reason}` on `<li>` — duplicate reasons collapse
- **File:** `frontend/components/case/EvidencePanel.tsx:268`
- **Bug:** `inconclusiveReasons()` can emit identical strings for two observations;
  React will warn and drop one. Use the observation id as part of the key.

### C8. List keys are raw user data
- **Files:** `AIAnalysisPanel.tsx:28` (`key={item}`), `:109` (`key={g}`),
  `RemediationPanel.tsx:31` (`key={step}`)
- **Bug:** duplicate AI strings → React key collisions (console warnings, dropped
  list items). Use `${index}-${slug}` composite keys.

### C9. `Tooltip` is a `title` attribute wrapper
- **File:** `frontend/components/shared/Tooltip.tsx`
- **Bug:** no keyboard/focus/ARIA; `title` doesn't show on touch or keyboard focus.
  Used on confidence badges and CVSS/EPSS/KEV labels.
- **Fix:** ARIA `role="tooltip"` + `aria-describedby` + focus trigger, or accept the
  limitation.

### C10. `KevBadge`/`priorityVariantMap`/`evidenceVariant`/`approvalVariant` maps duplicated across 5+ files
- **Files:** `CaseHeader.tsx`, `CasePipeline.tsx`, `CaseTable.tsx`,
  `ValidationBadge.tsx`, `ApprovalControls.tsx`
- **Bug:** same enum→variant maps re-declared; a new status (e.g. "QUARANTINED")
  would need edits in 6 places, with silent fallbacks (e.g. `?? "p4"`).
- **Fix:** centralize in `lib/api/types.ts` or `lib/variants.ts`.

### C11. `PriorityQueue` renders a fake minimum bar for zero counts
- **File:** `frontend/components/dashboard/PriorityQueue.tsx:60`
- **Bug:** `Math.max(2, widthPercent)` renders a 2% bar for P4=0, implying non-zero.
- **Fix:** render 0-width or an explicit "0" state.

### C12. Case detail right column sticky offset assumes header height
- **File:** `frontend/app/cases/[id]/CaseDetail.tsx:156` (`lg:top-20`)
- **Bug:** `top-20` (80px) vs actual header 56px (h-14) — 24px of dead space and the
  panel can overlap the header shadow area on short viewports.
- **Fix:** `lg:top-[72px]` or measure via CSS var.

### C13. `Sidebar` footer mock/live text duplicates `TopHeader` badge
- **Files:** `Sidebar.tsx:108-115`, `TopHeader.tsx:70-80`
- **Bug:** same info twice on desktop; each has independent copy that can drift.
- **Fix:** extract a `ModeBadge` shared component.

### C14. `DuplicateClusterPanel` arrows render vertically on mobile but numbers stay inline
- **File:** `frontend/components/case/DuplicateClusterPanel.tsx:26-45`
- **Bug:** `↓` arrows are meaningless mid-list on stacked mobile layout (column flow);
  they read "3 ↓ 1 ↓ 1" vertically which is fine, but horizontal centering with
  `sm:justify-center` makes the desktop row look sparse vs the panel width.
- Minor visual polish.

### C15. `EvidencePanel` renders the full observations table *and* a duplicate NOT_CONFIRMED block
- **File:** `frontend/components/case/EvidencePanel.tsx:222-262`
- **Bug:** for NOT_CONFIRMED cases the same observations appear twice (table above,
  "Scanner claim vs Observed" comparison below). Deliberate design choice, but it
  doubles reading load; the comparison block alone is more useful.
- Consider hiding the table when the contradiction block is shown.

### C16. Confidence percentage duplicated in 4 components
- **Files:** `CaseTable.tsx:296-299`, `CaseHeader.tsx:41-44`,
  `EvidencePanel.tsx:104-107`, `ValidationBadge.tsx:16-18`
- **Bug:** identical `Math.round((typeof x === "number" ? x : 0) * 100)` logic
  copy-pasted.
- **Fix:** `formatConfidence()` helper in `lib`.

### C17. `case` as a prop name everywhere
- **Files:** `CaseHeader.tsx`, `CasePipeline.tsx` (`{ case: TriageCase }`)
- **Bug:** `case` is a reserved word; forces rename destructure
  (`{ case: caseData }`) in every consumer. Works, but stylistically hazardous.
- **Fix:** prop `triageCase`.

### C18. Empty-state inconsistency
- **Files:** `ClustersPanel.tsx:9-16`, `IngestionPanel.tsx:13-21` (dashed border),
  `CaseTable.tsx:152-159` (dashed), `AuditTimeline.tsx` (dashed) vs
  `PriorityQueue` (no empty state — always renders 4 rows even with no cases)
- **Bug:** mixed empty-state styles; `PriorityQueue` shows all-zero bars with no
  guidance when the store is empty.

### C19. `CaseTable` result-count row is visually cramped against the toolbar
- **File:** `frontend/components/dashboard/CaseTable.tsx:216-226`
- Minor spacing polish (`py-1.5` vs toolbar `py-2.5`).

### C20. `inconclusiveReasons` string-matching is fragile
- **File:** `frontend/components/case/EvidencePanel.tsx:88` (regex on observed value)
- **Bug:** `/timed?\s*out|timeout|unable to confirm/i` guessing reasons from data
  strings — misclassification risk as validator wording evolves.

---

## P3 — Low (nitpicks)

- **D1.** `AuditTimeline.tsx:96` — `dateTime={event.timestamp}` renders invalid
  `datetime` attr when timestamp is unparseable but present (guarded in display, not
  in the attribute).
- **D2.** `CaseTable.tsx:171` — search input `type="search"` gets browser-provided
  clear button styling that clashes with the dark theme (minor).
- **D3.** `CaseDetail.tsx:120` — error-while-data fallback renders the generic
  "Data source unavailable" card even when the error happened during *analyze*
  (`handleAnalyze` sets the same `error` state); the analyze failure message appears
  only if data still exists, else the misleading full-page error shows.
- **D4.** `ValidationBadge.tsx:21` — `confidencePct >= 0 ? … : ""` is always true
  (confidence is clamped to 0); dead branch.
- **D5.** `mockProvider.ts` — `approveCase` in mock sets `reason: reason || undefined`
  but approve UI sends `""`; approve decisions thus never record a reason (by design,
  but inconsistent with reject/override).
- **D6.** `globals.css` — `* { transition-duration: 0.01ms !important }` under
  reduced-motion also kills the `transition-all` width bars (intended) but the
  universal selector is heavy-handed; scope to `*::before/::after` too for parity.
- **D7.** `KpiStrip` — values not `Intl.NumberFormat`-formatted; fine at demo scale.
- **D8.** `realProvider.getAudit` is exposed but never called by any component (the
  case payload embeds audit events). Dead public API.
- **D9.** `Sidebar` — active "Cases" detection breaks for URL-encoded query orders
  (`?evidence=…&priority=…` would activate both links).
- **D10.** `TopHeader` breadcrumbs for `/cases/CASE-001` show the raw case id instead
  of the case title (minor context loss).

---

## Contract parity (frontend ↔ backend)

Verified route-by-route against `backend/app`:

| Frontend call (realProvider) | Backend route | Status |
| --- | --- | --- |
| `GET /api/cases` | `case_routes.list_cases` | ✅ match |
| `GET /api/cases/{id}` | `case_routes.get_case_route` | ✅ match |
| `POST /api/ai/analyze/{id}` | `ai_routes.analyze` | ✅ match |
| `POST /api/cases/{id}/approve` | `approval_routes.approve_case` | ✅ payload `{analyst_id, reason?}` |
| `POST /api/cases/{id}/reject` | `approval_routes.reject_case` | ✅ payload `{analyst_id, reason}` |
| `POST /api/cases/{id}/override` | `approval_routes.override_case` | ✅ payload `{analyst_id, override_priority, reason}` |
| `GET /api/dashboard/stats` | `dashboard_routes.get_dashboard_stats` | ✅ match |
| `GET /api/v1/report` | `main.get_full_report` | ✅ 404 → `{summary:null, clusters:[]}` handled |
| `GET /api/cases/{id}/audit` | `audit_routes` | ⚠️ exposed, unused (D8) |

Contract mismatch found during packaging work (fixed there): the backend approvals
require `analyst_id` on **every** action — the approve UI's confirm flow (A1) sends
none today because the action can never fire.

## Positive findings (worth keeping)

1. **Injection-safe evidence rendering** — `isSuspicious()` detection + "Untrusted
   observation" framing + React text-only rendering; covered by tests (8/8) and
   empirically robust for payloads like `<script>`, `onerror=`, `IGNORE ALL PREVIOUS…`.
2. **Consistent design tokens** — one Tailwind palette (`canvas/graphite/line/tx/
   accent/priority/evidence`), one `hk-label` micro-label pattern, uniform panel
   chrome (`rounded-sm border border-line bg-graphite`).
3. **Honest AI labeling** — every AI block carries "AI-generated — verify before
   acting"; grounded_on fields surfaced; limitations shown.
4. **Append-only audit UI** — hash-linked events indicator, actor badges, state
   transitions, override transitions from metadata.
5. **Deterministic ordering** — explicit `levelOrder/evidenceOrder/approvalOrder` maps
   rather than alphabetical accidents.
6. **Reduced-motion support** and visible focus outlines globally.

## Recommended fix order

1. **A1** (approve) — one-line fix, unblocks the product's core loop.
2. **B2/B3** (sidebar filters) — make the Intelligence/Priority nav honest.
3. **B1** (dashboard filter navigation) — stop stealing the user's context.
4. **C8/C7** (React keys) — correctness warnings.
5. **C2/C3** (roles/aria-sort) — accessibility.
6. **C10/C16** (centralize maps & formatters) — maintainability.
