# CyberYukti — Person 4 Demo Script (5 Minutes)

## Pre-Demo Setup
- Ensure `NEXT_PUBLIC_USE_MOCK=true` (default)
- Frontend running: `npm run dev` in `frontend/`
- Backend running: `uvicorn backend.app.main:app --reload` in `repo-root/`

---

## 0:00–0:30 — Dashboard Overview

**Screen:** Open `/` (Dashboard)

**Say:** "CyberYukti is an AI-powered vulnerability triage system. The dashboard shows our current posture: findings, clusters, evidence status, and priority breakdown."

**Show:**
- Stat cards: Total Findings, Unique Clusters, Confirmed, Not Confirmed, Inconclusive
- Priority distribution chart (P1–P4)
- Case table with 6 cases

**Click:** None yet — just narrate.

---

## 0:30–1:30 — Scenario 1: Confirmed P1 (SQL Injection)

**Screen:** Click CASE-001 in the case table

**Say:** "This is a confirmed critical SQL injection in our shop API. Let me walk through the chain."

**Show:**
1. **Case Header** — CASE-001, P1 badge (red), CONFIRMED badge (green)
2. **Asset Panel** — shop-api-01.prod.example.com, production, internet-exposed, critical
3. **Evidence Panel** — Two observations confirming the injection; confidence 95%
4. **Threat Intel** — CVSS 8.8, EPSS 0.72%, KEV = Yes
5. **Priority Breakdown** — Score 92.5, all six factors visible
6. **AI Analysis** — "Run Analysis" button → click it → read summary, why_it_matters, remediation steps
7. **Click Approve** → double-click confirm → audit event appears

**Say:** "Every step is deterministic. AI explains. Humans decide."

---

## 1:30–2:30 — Scenario 2: NOT_CONFIRMED (False Positive)

**Screen:** Click CASE-002

**Say:** "This case shows our validation system catching a false positive."

**Show:**
1. **Evidence Panel** — NOT_CONFIRMED badge (red), contradiction highlighted: scanner says jQuery <3.5.1, but we observed 3.7.1 (patched)
2. **AI Analysis** — explains the contradiction, recommends no action
3. **Click Reject** → enter reason "False positive — patched version installed" → audit event

**Say:** "The analyst can see exactly why the scanner was wrong. No guessing."

---

## 2:30–3:15 — Scenario 3: Duplicate Cluster

**Screen:** Click CASE-003

**Say:** "Three scanners found the same XSS. Person 1's dedup merged them into one cluster."

**Show:**
1. **Duplicate Sources Panel** — nuclei, semgrep, acunetix (3 sources), finding_count=3
2. **Evidence Panel** — CONFIRMED, 91% confidence

**Say:** "The analyst sees all sources without triaging three separate findings."

---

## 3:15–4:00 — Scenario 4: Prompt Injection

**Screen:** Click CASE-004 (navigate back to cases, find the injection case)

**Say:** "Findings are untrusted input. A scanner output could contain adversarial text."

**Show:**
1. **Evidence Panel** — payload renders as plain text, NOT as executable code
2. **AI Analysis** — summary is grounded in case data, ignores any injected instructions

**Say:** "The AI treats finding text as data, not instructions. This is our trust boundary."

---

## 4:00–4:45 — Scenario 5: Override

**Screen:** Click CASE-005

**Say:** "Sometimes an analyst needs to override the priority based on business context."

**Show:**
1. **Priority** — currently P2, score 68.9
2. **Click Override** → select P1 → enter reason "Business-critical admin panel, KEV-listed"
3. **Priority badge updates** to P1
4. **Audit timeline** shows override event with old_priority, new_priority, reason

**Say:** "Every decision is auditable. The override is logged with the analyst's identity and reasoning."

---

## 4:45–5:00 — Wrap

**Screen:** Show audit timeline for CASE-005

**Say:** "CyberYukti: deterministic systems decide, AI explains, humans approve. Every action is auditable. Thank you."

---

## Fallback: If Something Fails

| Issue | Workaround |
|---|---|
| Dashboard blank | Refresh page; check mock mode is ON |
| AI Analysis button fails | Show pre-generated analysis in mock data |
| Approval button fails | Explain the workflow verbally |
| Case page 404 | Navigate back to cases, pick a different case |
| Any crash | Switch to pre-recorded screenshots in `docs/` |
