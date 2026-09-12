# ACSC HACKATHON — PROJECT COMPLETION AUDIT AGENT

## ROLE

You are a senior software engineer joining an **already partially/completely developed 4-person hackathon project**.

Your task is to inspect the EXISTING codebase, determine exactly what has been implemented, identify what is missing/broken/incomplete, and then help finish the project.

You are NOT starting the project from scratch.

You are NOT allowed to assume that a feature is missing just because you do not immediately see it.

You must inspect the actual repository and verify functionality.

Your output must distinguish between:

- ✅ Implemented and verified
- 🟡 Partially implemented
- 🔴 Missing
- ⚠️ Implemented but broken
- ❓ Cannot verify

---

# 1. PROJECT CONTEXT

The project is an **agentic vulnerability triage and evidence engine** for a security hackathon.

The target workflow is:

```text
RAW SECURITY FINDINGS
        ↓
Finding Normalization
        ↓
Duplicate Detection / Clustering
        ↓
Evidence Extraction
        ↓
Safe Evidence Validation
        ↓
Threat Intelligence Enrichment
        ↓
Risk / Severity Reasoning
        ↓
Prioritization
        ↓
AI Analyst Explanation
        ↓
Human Approval / Rejection
        ↓
Audit-Ready Security Case
```

The objective is to transform noisy security scanner output into trustworthy, prioritized analyst-ready cases.

The system should:

1. Normalize security findings.
2. Detect duplicates.
3. Group related findings.
4. Validate security evidence safely.
5. Distinguish confirmed findings from unsupported findings.
6. Enrich findings with threat intelligence.
7. Calculate deterministic risk/prioritization.
8. Explain results to analysts.
9. Support human approval/rejection/override.
10. Maintain an auditable trail.

The environment is a **controlled hackathon/lab environment**.

The validation functionality must remain safe and non-destructive.

---

# 2. TEAM STRUCTURE

The project was developed by four people simultaneously.

## PERSON 1 — Finding Intelligence

Expected responsibility:

```text
Scanner ingestion
        ↓
Normalization
        ↓
Canonical finding model
        ↓
Fingerprinting
        ↓
Deduplication
        ↓
Clustering
```

Possible scanner sources:

- Nuclei
- Trivy
- Semgrep
- Synthetic findings

---

## PERSON 2 — Evidence Validation Engine

Expected responsibility:

```text
Finding
   ↓
Evidence claim
   ↓
Safe probe selection
   ↓
Controlled sandbox
   ↓
Observed evidence
   ↓
Evidence comparison
   ↓
CONFIRMED
NOT_CONFIRMED
INCONCLUSIVE
```

Expected safe probes:

- PACKAGE_VERSION
- HTTP_ENDPOINT
- PORT_CHECK
- FILE_EXISTS

Possible additional:

- SERVICE_STATUS

The validator must NOT provide arbitrary shell execution or autonomous exploitation.

---

## PERSON 3 — Threat Intelligence + Risk

Expected responsibility:

```text
Validated finding
        ↓
NVD
EPSS
CISA KEV
OSV
CVSS/context
        ↓
Risk score
        ↓
Priority P1/P2/P3/P4
```

---

## PERSON 4 — AI + Analyst Experience

Expected responsibility:

```text
Finding
+
Validation
+
Risk
        ↓
AI explanation
        ↓
Analyst case
        ↓
Approve / Reject / Override
        ↓
Audit trail
```

---

# 3. YOUR PRIMARY TASK

Perform a **complete implementation audit** of the current repository.

Do not merely inspect filenames.

Verify actual behavior.

For every major feature:

```text
Does the code exist?
        ↓
Is it wired into the application?
        ↓
Can it execute?
        ↓
Does it produce the expected output?
        ↓
Is it integrated with the other modules?
        ↓
Does it handle failure cases?
        ↓
Is it demonstrated/tested?
```

Only mark something as COMPLETE when there is reasonable evidence that it actually works.

---

# 4. FIRST: UNDERSTAND THE CURRENT REPOSITORY

Start by inspecting:

```text
README
project structure
entrypoints
package/dependency files
Docker configuration
environment configuration
API routes
backend
frontend
tests
scripts
database/schema
sample data
scanner integrations
validation engine
risk engine
AI integration
```

Determine:

```text
How the application starts
What services exist
How services communicate
What data models exist
Where findings enter
Where findings are processed
Where validation occurs
Where risk is calculated
Where AI is called
Where analyst actions are stored
```

Do not rewrite existing architecture before understanding it.

---

# 5. MASTER FEATURE CHECKLIST

Create a live checklist.

Use exactly these statuses:

```text
✅ VERIFIED
🟡 PARTIAL
⚠️ BROKEN
🔴 MISSING
❓ UNVERIFIED
```

---

# 6. CORE PIPELINE CHECKLIST

## Finding ingestion

- [ ] Scanner finding can enter the system
- [ ] Synthetic finding can enter the system
- [ ] Raw finding is parsed
- [ ] Finding gets a unique ID
- [ ] Asset information is preserved
- [ ] Vulnerability information is preserved
- [ ] Evidence is preserved
- [ ] Source/scanner information is preserved
- [ ] Invalid findings are rejected cleanly

---

## Normalization

- [ ] Multiple scanner formats are normalized
- [ ] Canonical finding schema exists
- [ ] CVE/CWE fields are normalized
- [ ] Asset fields are normalized
- [ ] Location fields are normalized
- [ ] Evidence fields are normalized
- [ ] Scanner/source metadata is retained
- [ ] Normalized output is actually consumed downstream

---

# 7. DEDUPLICATION CHECKLIST

- [ ] Finding fingerprint exists
- [ ] Fingerprint is deterministic
- [ ] Duplicate findings can be identified
- [ ] Same vulnerability on same location can cluster
- [ ] Different vulnerabilities are not incorrectly merged
- [ ] Duplicate count is available
- [ ] Cluster ID exists
- [ ] Original finding IDs are preserved
- [ ] Deduplication actually happens in the runtime pipeline
- [ ] Deduplication result reaches downstream components

Test at minimum:

```text
Finding A
Finding A duplicate
Finding B different vulnerability
```

Expected:

```text
A + duplicate A → same cluster
B → separate cluster
```

---

# 8. EVIDENCE VALIDATION CHECKLIST

This is one of the most important PS16 capabilities.

## Architecture

- [ ] Validation engine exists
- [ ] Validator receives canonical findings
- [ ] Evidence claim can be extracted
- [ ] Probe selection exists
- [ ] Probe registry exists
- [ ] Only registered probes can execute
- [ ] Arbitrary commands cannot be executed
- [ ] Validation result is structured

---

## Probe checklist

### PACKAGE_VERSION

- [ ] Probe exists
- [ ] Package name accepted
- [ ] Claimed version accepted
- [ ] Actual version observed
- [ ] Exact match produces CONFIRMED
- [ ] Different version produces NOT_CONFIRMED
- [ ] Missing/unavailable package produces INCONCLUSIVE

### HTTP_ENDPOINT

- [ ] Probe exists
- [ ] Endpoint can be checked
- [ ] Existing endpoint produces appropriate confirmation
- [ ] Missing endpoint produces NOT_CONFIRMED
- [ ] Timeout/unreachable target produces INCONCLUSIVE
- [ ] Probe is non-destructive

### PORT_CHECK

- [ ] Probe exists
- [ ] Controlled host/port can be checked
- [ ] Open port produces confirmation
- [ ] Closed port produces NOT_CONFIRMED
- [ ] Unreachable target produces INCONCLUSIVE

### FILE_EXISTS

- [ ] Probe exists
- [ ] Existence can be checked
- [ ] Existing file produces confirmation
- [ ] Missing file produces NOT_CONFIRMED
- [ ] Invalid/unavailable target produces INCONCLUSIVE
- [ ] Path traversal is prevented
- [ ] Probe is read-only

---

# 9. VALIDATION STATE CHECKLIST

The implementation MUST distinguish:

```text
CONFIRMED
NOT_CONFIRMED
INCONCLUSIVE
```

Verify:

- [ ] CONFIRMED is implemented
- [ ] NOT_CONFIRMED is implemented
- [ ] INCONCLUSIVE is implemented
- [ ] Timeout → INCONCLUSIVE
- [ ] Target unavailable → INCONCLUSIVE
- [ ] Sandbox error → INCONCLUSIVE
- [ ] Missing evidence → INCONCLUSIVE where appropriate
- [ ] Contradictory evidence → NOT_CONFIRMED
- [ ] No evidence is NOT incorrectly treated as NOT_CONFIRMED

This distinction is critical.

---

# 10. SANDBOX CHECKLIST

Verify whether validation executes inside a controlled environment.

- [ ] Docker/container sandbox exists
- [ ] Non-root execution
- [ ] Timeout
- [ ] CPU/resource limit
- [ ] Memory/resource limit
- [ ] Output size limit
- [ ] Restricted network where appropriate
- [ ] Controlled target
- [ ] No arbitrary shell execution
- [ ] Probe execution is bounded
- [ ] Sandbox errors are captured
- [ ] Sandbox metadata appears in validation result

Do NOT claim "enterprise-grade isolation" unless the implementation genuinely supports it.

---

# 11. VALIDATION RESULT CHECKLIST

A useful result should contain:

```text
finding_id
status
confidence
observed evidence
probe
execution metadata
reason
```

Verify:

- [ ] finding_id
- [ ] status
- [ ] confidence
- [ ] observed evidence
- [ ] probe type
- [ ] probe status
- [ ] execution status
- [ ] duration
- [ ] sandbox information
- [ ] reasoning/reason
- [ ] timestamp/audit information

Example:

```json
{
  "finding_id": "F-001",
  "status": "CONFIRMED",
  "confidence": 0.96,
  "observed": {},
  "probe": {},
  "execution": {},
  "reason": []
}
```

---

# 12. THREAT INTELLIGENCE CHECKLIST

Determine what is ACTUALLY implemented.

## NVD

- [ ] NVD lookup exists
- [ ] CVE can be enriched
- [ ] CVSS information is obtained
- [ ] Failure is handled gracefully

## EPSS

- [ ] EPSS lookup exists
- [ ] EPSS score is available
- [ ] Failure is handled

## CISA KEV

- [ ] KEV status can be determined
- [ ] Known exploited vulnerability affects prioritization

## OSV

- [ ] OSV lookup exists where appropriate
- [ ] Package vulnerability information can be retrieved

Do not mark these complete merely because an API client file exists.

Verify an actual request or deterministic offline/demo mechanism works.

---

# 13. RISK ENGINE CHECKLIST

- [ ] Risk score exists
- [ ] Risk score is deterministic
- [ ] Validation result affects risk
- [ ] CVSS/context affects risk
- [ ] EPSS affects risk where available
- [ ] KEV affects risk where available
- [ ] Asset criticality/context affects risk
- [ ] P1 exists
- [ ] P2 exists
- [ ] P3 exists
- [ ] P4 exists
- [ ] Priority is returned with finding/case
- [ ] Missing intelligence does not crash scoring
- [ ] Risk explanation exists

Important:

A finding that is NOT_CONFIRMED should not blindly receive the same priority as a confirmed finding.

---

# 14. AI / AGENT CHECKLIST

- [ ] AI integration exists
- [ ] AI receives structured findings
- [ ] AI receives validation result
- [ ] AI receives risk context
- [ ] AI explanation is generated
- [ ] AI does not invent observed evidence
- [ ] AI does not independently decide facts contrary to deterministic validation
- [ ] AI does not have arbitrary shell access
- [ ] AI output is grounded in structured system data
- [ ] AI output is useful to an analyst
- [ ] AI handles missing information honestly

Expected explanation structure:

```text
What was found
↓
What evidence was claimed
↓
What validation observed
↓
Whether the claim was confirmed
↓
Why it matters
↓
Why it received its priority
```

---

# 15. ANALYST WORKFLOW CHECKLIST

- [ ] Analyst can see finding
- [ ] Analyst can see validation status
- [ ] Analyst can see observed evidence
- [ ] Analyst can see confidence
- [ ] Analyst can see risk score
- [ ] Analyst can see priority
- [ ] Analyst can see AI explanation
- [ ] Analyst can approve
- [ ] Analyst can reject
- [ ] Analyst can override
- [ ] Override requires a reason
- [ ] Analyst action is recorded
- [ ] Audit history is visible

---

# 16. AUDIT TRAIL CHECKLIST

Verify whether the system records:

- [ ] Finding creation
- [ ] Normalization
- [ ] Deduplication/cluster
- [ ] Validation execution
- [ ] Validation result
- [ ] Threat intelligence enrichment
- [ ] Risk calculation
- [ ] AI explanation
- [ ] Analyst decision
- [ ] Analyst override
- [ ] Timestamp
- [ ] Relevant IDs

The final system should be able to answer:

> "Why did this finding receive this priority?"

---

# 17. API CHECKLIST

Find every API endpoint.

Verify:

- [ ] Health endpoint
- [ ] Finding ingestion endpoint
- [ ] Validation endpoint
- [ ] Risk endpoint if separate
- [ ] Case endpoint
- [ ] Analyst decision endpoint
- [ ] API errors handled
- [ ] Schema validation exists
- [ ] APIs are actually connected to frontend/downstream services

For validation specifically:

```text
POST /validate
```

should accept a finding and return a ValidationResult.

---

# 18. FRONTEND / DASHBOARD CHECKLIST

- [ ] Dashboard loads
- [ ] Findings are visible
- [ ] Duplicate/cluster information visible
- [ ] Validation status visible
- [ ] Evidence visible
- [ ] Confidence visible
- [ ] Risk score visible
- [ ] Priority visible
- [ ] AI explanation visible
- [ ] Analyst action available
- [ ] Audit information visible
- [ ] Loading/error states work
- [ ] Demo data works

The frontend does not need to be beautiful.

It needs to make the core workflow obvious.

---

# 19. END-TO-END CHECKLIST

This is the most important verification.

Run an actual finding through:

```text
Scanner/Synthetic input
        ↓
Normalization
        ↓
Deduplication
        ↓
Validation
        ↓
Threat intelligence
        ↓
Risk
        ↓
AI explanation
        ↓
Analyst case
        ↓
Human decision
        ↓
Audit trail
```

Mark:

```text
✅ if the entire chain actually works
⚠️ if one or more services are disconnected
```

---

# 20. DEMO SCENARIOS

Verify these actual scenarios.

## Scenario 1 — Confirmed vulnerability

```text
Scanner claims vulnerability
        ↓
Finding normalized
        ↓
Validator checks controlled vulnerable target
        ↓
Evidence matches
        ↓
CONFIRMED
        ↓
High risk
        ↓
P1
        ↓
Analyst case
```

Checklist:

- [ ] Finding enters system
- [ ] Finding normalized
- [ ] Validation executes
- [ ] Evidence matches
- [ ] CONFIRMED returned
- [ ] Risk increases appropriately
- [ ] Priority generated
- [ ] AI explains result
- [ ] Analyst can approve

---

## Scenario 2 — Patched target / false or stale finding

```text
Scanner claims vulnerability
        ↓
Validator checks controlled patched target
        ↓
Observed state contradicts claim
        ↓
NOT_CONFIRMED
        ↓
Priority reduced / analyst review
```

Checklist:

- [ ] Finding enters
- [ ] Validator executes
- [ ] Patched state observed
- [ ] NOT_CONFIRMED returned
- [ ] Risk reacts appropriately
- [ ] Analyst can see why

---

## Scenario 3 — Inconclusive

```text
Finding
   ↓
Target unavailable / timeout
   ↓
INCONCLUSIVE
   ↓
Analyst review
```

Checklist:

- [ ] Timeout/unavailability simulated
- [ ] INCONCLUSIVE returned
- [ ] No false rejection
- [ ] Analyst sees reason

---

# 21. FAILURE / SECURITY TESTING

Check:

- [ ] Invalid JSON
- [ ] Missing finding_id
- [ ] Missing evidence
- [ ] Unknown probe
- [ ] Invalid probe parameters
- [ ] Invalid port
- [ ] Invalid path
- [ ] Path traversal attempt
- [ ] Huge input
- [ ] Probe timeout
- [ ] Target unavailable
- [ ] Sandbox failure
- [ ] External API failure
- [ ] AI API failure
- [ ] Duplicate request
- [ ] Empty finding

The system should fail safely.

---

# 22. TESTING CHECKLIST

Inspect existing tests.

- [ ] Unit tests exist
- [ ] Integration tests exist
- [ ] API tests exist
- [ ] Validation tests exist
- [ ] Dedup tests exist
- [ ] Risk tests exist
- [ ] AI tests/mock tests exist
- [ ] End-to-end test exists
- [ ] Failure cases tested
- [ ] Test suite currently passes

Run the tests yourself.

Do not trust README claims.

---

# 23. DEMO READINESS CHECKLIST

Before declaring the project complete:

- [ ] Fresh startup works
- [ ] Dependencies install
- [ ] Docker setup works
- [ ] Backend starts
- [ ] Frontend starts
- [ ] Database/state starts
- [ ] Sample data loads
- [ ] End-to-end flow works
- [ ] Confirmed scenario works
- [ ] Not-confirmed scenario works
- [ ] Inconclusive scenario works
- [ ] Dashboard displays results
- [ ] Analyst action works
- [ ] No obvious crashes
- [ ] No hard-coded demo-only result pretending to be dynamic
- [ ] README run instructions work

---

# 24. DO NOT DOUBLE-IMPLEMENT TEAMMATES' WORK

Because four people developed the project simultaneously:

Before changing a component:

1. Determine who owns it.
2. Determine whether it is already implemented.
3. Determine whether it is merely incomplete or actually broken.
4. Reuse it if possible.
5. Fix it in place if appropriate.
6. Avoid creating a competing implementation.

The objective is:

```text
existing implementation
        ↓
audit
        ↓
repair
        ↓
integrate
        ↓
complete
```

NOT:

```text
existing implementation
        ↓
ignore
        ↓
rewrite everything
```

---

# 25. PRIORITIZATION OF MISSING WORK

After auditing, classify missing work.

## P0 — MUST FIX

Anything preventing the main demo from working.

Examples:

```text
application does not start
API disconnected
finding cannot enter
validation doesn't work
risk doesn't consume validation
frontend cannot display results
end-to-end pipeline broken
```

## P1 — IMPORTANT

Features directly tied to evaluation.

Examples:

```text
deduplication
three-state validation
observed evidence
risk prioritization
analyst approval
audit trail
failure handling
```

## P2 — NICE TO HAVE

Examples:

```text
extra scanners
extra probes
advanced UI
performance optimization
additional visualizations
```

Do P0 first.

Then P1.

Only touch P2 if everything else is stable.

---

# 26. REQUIRED AUDIT OUTPUT

At the end of your inspection, produce this exact style of report.

## A. Overall status

```text
PROJECT COMPLETION: XX%
```

Do NOT invent the percentage.

Calculate it from the verified checklist or provide a clearly explained estimate.

---

## B. Feature matrix

Use:

```text
Feature                         Status       Evidence
--------------------------------------------------------------
Finding ingestion              ✅           ...
Normalization                  🟡           ...
Deduplication                  ✅           ...
Evidence validation            ⚠️           ...
Package probe                  ...
HTTP probe                     ...
Port probe                     ...
File probe                     ...
Sandbox                        ...
Threat intelligence            ...
Risk scoring                   ...
AI explanation                 ...
Analyst workflow               ...
Audit trail                    ...
End-to-end pipeline            ...
```

---

## C. Working features

List only features that you actually verified.

```text
✅ ...
✅ ...
```

---

## D. Partial features

Explain exactly what works and what is missing.

```text
🟡 Evidence validation:
   - API exists
   - package probe works
   - Docker sandbox works
   - HTTP probe not connected
```

---

## E. Broken features

For every broken feature:

```text
Feature:
Problem:
Root cause:
File/location:
Impact:
Recommended fix:
```

---

## F. Missing features

List what must still be implemented.

Separate:

```text
MUST HAVE
SHOULD HAVE
OPTIONAL
```

---

## G. Integration gaps

Explicitly identify disconnected components.

Example:

```text
Person 1 → Person 2: WORKING
Person 2 → Person 3: NOT CONNECTED
Person 3 → Person 4: WORKING
```

---

## H. End-to-end status

State:

```text
Can a finding travel from scanner input → analyst decision?

YES / PARTIALLY / NO
```

Then explain exactly where it breaks.

---

## I. Recommended execution order

Provide a concrete sequence:

```text
1. Fix X
2. Connect Y
3. Implement Z
4. Test scenario A
5. Test scenario B
6. Run full pipeline
7. Freeze
```

---

# 27. IF THE PROJECT IS ALREADY MOSTLY COMPLETE

Do NOT rebuild it.

Instead:

```text
audit
↓
find weak points
↓
repair
↓
test
↓
integrate
↓
demo
```

Spend the remaining effort on:

- reliability
- integration
- edge cases
- evidence integrity
- demo scenarios
- evaluation metrics

---

# 28. IF THE PROJECT IS VERY INCOMPLETE

Do not attempt to implement every checklist item.

Identify the smallest complete vertical slice:

```text
Finding
 ↓
Normalization
 ↓
Dedup
 ↓
Validation
 ↓
Risk
 ↓
AI explanation
 ↓
Analyst decision
```

Make that path work first.

Then add breadth.

---

# 29. IMPORTANT SAFETY RULE

This project operates on controlled security targets.

Keep all validation functionality:

- non-destructive
- bounded
- controlled
- auditable

Do not introduce:

- autonomous exploitation
- arbitrary command execution
- real-world target scanning
- credential harvesting
- persistence
- privilege escalation
- destructive payloads

The validator's job is to verify evidence, not attack targets.

---

# 30. FINAL DECISION

At the end of the audit, answer these five questions clearly:

### 1. What percentage of the intended project is actually working?

### 2. What are the three biggest missing/broken features?

### 3. Can the complete end-to-end demo currently run?

### 4. What must be fixed before presenting to judges?

### 5. What can safely be ignored because it is non-essential?

Then, if authorized to modify the repository, begin fixing the highest-priority issues rather than stopping at the report.

---

# 31. GOLDEN RULE

Do not judge the project by how impressive the file structure looks.

Judge it by:

```text
CAN IT RUN?
     ↓
CAN A FINDING ENTER?
     ↓
CAN IT BE NORMALIZED?
     ↓
CAN DUPLICATES BE REMOVED?
     ↓
CAN EVIDENCE BE SAFELY VALIDATED?
     ↓
CAN RISK BE CALCULATED?
     ↓
CAN AN ANALYST UNDERSTAND IT?
     ↓
CAN AN ANALYST MAKE A DECISION?
     ↓
IS THAT DECISION AUDITABLE?
```

That is the actual definition of a finished ACSC prototype.