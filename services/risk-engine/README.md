# ACSC Risk Intelligence Engine

The Risk Intelligence Engine is the risk-scoring and prioritization service of the ACSC Autonomous Vulnerability Triage & Evidence Engine.

It receives normalized security findings and validation results, calculates a deterministic risk score, computes a separate evidence confidence score, assigns a priority level and a decision category, classifies every finding into a risk-confidence matrix with a recommended next step, and returns human-readable reasons for the decision.

## Responsibilities

The service performs the following tasks:

* Calculate risk scores for security findings
* Consider severity and CVSS scores
* Consider asset criticality
* Consider internet exposure
* Consider validation status and confidence
* Assign priority levels from P1 to P4
* Calculate a separate evidence confidence score
* Assign a decision category based on risk and evidence confidence
* Classify every finding into the risk-confidence matrix (risk band × evidence confidence) with a recommended next step
* Sort findings by priority and risk score
* Return explanations for prioritization decisions
* Explain why a specific finding was prioritized (key drivers, priority basis, and the reason behind the priority)
* Build an analyst action queue grouped by recommended action category
* Prepare findings for human review with auditable evidence provenance
* Record human review decisions (approve, reject, defer, request more evidence)
* Support single and batch assessment

The service does not independently exploit targets or claim that a finding is confirmed without validation evidence.

## Project Structure

```text
risk-engine/
├── app/
│   ├── __init__.py
│   ├── explanation.py
│   ├── main.py
│   ├── models.py
│   ├── prioritization.py
│   └── scoring.py
├── tests/
│   ├── test_batch.py
│   ├── test_evidence_confidence.py
│   ├── test_examples.py
│   ├── test_explain.py
│   ├── test_explain_why_first.py
│   ├── test_health.py
│   ├── test_queue.py
│   ├── test_review.py
│   ├── test_risk_confidence_matrix.py
│   └── test_sorting.py
├── examples/
│   └── sample-findings.json
├── requirements.txt
└── README.md
```

## Technology Stack

* Python
* FastAPI
* Pydantic
* Uvicorn
* Pytest

## Setup

From the repository root:

```powershell
cd services\risk-engine
```

Create a virtual environment if it does not already exist:

```powershell
python -m venv .venv
```

Activate the virtual environment:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Run the Service

From the `services\risk-engine` directory:

```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8003
```

The service will be available at:

```text
http://127.0.0.1:8003
```

Interactive API documentation is available at:

```text
http://127.0.0.1:8003/docs
```

OpenAPI JSON is available at:

```text
http://127.0.0.1:8003/openapi.json
```

## Run Tests

From the `services\risk-engine` directory:

```powershell
$env:PYTHONPATH = (Get-Location).Path
pytest -v
```

## API Endpoints

### Health Check

```http
GET /health
```

Example response:

```json
{
  "status": "ok",
  "service": "risk-engine",
  "version": "0.1.0"
}
```

### Single Finding Assessment

```http
POST /assess
```

This endpoint accepts one finding and returns its risk score, priority, reasons, and scoring factors.

### Batch Assessment

```http
POST /assess/batch
```

This endpoint accepts a JSON object containing a `findings` array and returns a response envelope with:

* `count` — the total number of findings processed
* `results` — an array of `PriorityResult` objects in submission order

#### Request format for `/assess/batch`

```json
{
  "findings": [
    {
      "finding_id": "F001",
      "title": "SQL Injection",
      "severity": "critical",
      "cvss": 10.0,
      "asset": {
        "id": "shop-api-01",
        "criticality": 1.0,
        "internet_exposed": true,
        "environment": "production"
      },
      "validation": {
        "status": "CONFIRMED",
        "confidence": 0.95
      }
    },
    {
      "finding_id": "F002",
      "title": "Info Disclosure",
      "severity": "low",
      "cvss": 2.0,
      "asset": {
        "id": "dev-server",
        "criticality": 0.2,
        "internet_exposed": false,
        "environment": "development"
      },
      "validation": {
        "status": "NOT_CONFIRMED",
        "confidence": 0.0
      }
    }
  ]
}
```

#### Response format for `/assess/batch`

```json
{
  "count": 2,
  "results": [
    {
      "finding_id": "F001",
      "risk_score": 0.9925,
      "priority": "P1",
      "reasons": ["Critical severity", "Very high CVSS score", "Internet-exposed asset", "Production environment", "Evidence confirmed with 95% confidence"],
      "factors": { "severity": 1.0, "asset_criticality": 1.0, "exposure": 1.0, "validation": 0.95 },
      "evidence_confidence": 0.95,
      "evidence_status": "CONFIRMED",
      "decision_category": "IMMEDIATE_ACTION",
      "risk_confidence_category": "HIGH_RISK_HIGH_CONFIDENCE",
      "matrix_label": "Immediate action",
      "recommended_next_step": "Review and remediate"
    },
    {
      "finding_id": "F002",
      "risk_score": 0.205,
      "priority": "P4",
      "reasons": ["Evidence was not confirmed", "No CVE identifier available"],
      "factors": { "severity": 0.2, "asset_criticality": 0.2, "exposure": 0.3, "validation": 0.1 },
      "evidence_confidence": 0.0,
      "evidence_status": "NOT_CONFIRMED",
      "decision_category": "DEFER",
      "risk_confidence_category": "LOW_RISK_LOW_CONFIDENCE",
      "matrix_label": "Defer and collect evidence",
      "recommended_next_step": "Defer for later review"
    }
  ]
}
```

### Sorted Batch Assessment

```http
POST /assess/batch/sorted
```

This endpoint accepts the same `BatchFindingInput` body as `/assess/batch` and returns a `BatchResult` envelope where `results` are sorted by:

1. Priority level: P1 → P2 → P3 → P4
2. `risk_score` descending within the same priority band

#### Request format for `/assess/batch/sorted`

```json
{
  "findings": [
    {
      "finding_id": "F002",
      "title": "Info Disclosure",
      "severity": "low",
      "cvss": 2.0,
      "asset": {
        "id": "dev-server",
        "criticality": 0.2,
        "internet_exposed": false,
        "environment": "development"
      },
      "validation": { "status": "NOT_CONFIRMED", "confidence": 0.0 }
    },
    {
      "finding_id": "F001",
      "title": "SQL Injection",
      "severity": "critical",
      "cvss": 10.0,
      "asset": {
        "id": "shop-api-01",
        "criticality": 1.0,
        "internet_exposed": true,
        "environment": "production"
      },
      "validation": { "status": "CONFIRMED", "confidence": 0.95 }
    }
  ]
}
```

#### Response format for `/assess/batch/sorted`

```json
{
  "count": 2,
  "results": [
    {
      "finding_id": "F001",
      "risk_score": 0.9925,
      "priority": "P1",
      "reasons": ["Critical severity", "Very high CVSS score", "Internet-exposed asset", "Production environment", "Evidence confirmed with 95% confidence"],
      "factors": { "severity": 1.0, "asset_criticality": 1.0, "exposure": 1.0, "validation": 0.95 },
      "evidence_confidence": 0.95,
      "evidence_status": "CONFIRMED",
      "decision_category": "IMMEDIATE_ACTION",
      "risk_confidence_category": "HIGH_RISK_HIGH_CONFIDENCE",
      "matrix_label": "Immediate action",
      "recommended_next_step": "Review and remediate"
    },
    {
      "finding_id": "F002",
      "risk_score": 0.205,
      "priority": "P4",
      "reasons": ["Evidence was not confirmed", "No CVE identifier available"],
      "factors": { "severity": 0.2, "asset_criticality": 0.2, "exposure": 0.3, "validation": 0.1 },
      "evidence_confidence": 0.0,
      "evidence_status": "NOT_CONFIRMED",
      "decision_category": "DEFER",
      "risk_confidence_category": "LOW_RISK_LOW_CONFIDENCE",
      "matrix_label": "Defer and collect evidence",
      "recommended_next_step": "Defer for later review"
    }
  ]
}
```

#### PowerShell example for `/assess/batch/sorted`

```powershell
$sortedBody = @{
    findings = @(
        @{
            finding_id = "F002"
            title      = "Info Disclosure"
            severity   = "low"
            cvss       = 2.0
            asset      = @{
                id               = "dev-server"
                criticality      = 0.2
                internet_exposed = $false
                environment      = "development"
            }
            validation = @{ status = "NOT_CONFIRMED"; confidence = 0.0 }
        },
        @{
            finding_id = "F001"
            title      = "SQL Injection"
            severity   = "critical"
            cvss       = 10.0
            asset      = @{
                id               = "shop-api-01"
                criticality      = 1.0
                internet_exposed = $true
                environment      = "production"
            }
            validation = @{ status = "CONFIRMED"; confidence = 0.95 }
        }
    )
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8003/assess/batch/sorted" `
    -Method POST `
    -ContentType "application/json" `
    -Body $sortedBody
```

Expected result (P1 appears first regardless of submission order):

```text
count   : 2
results : {@{finding_id=F001; risk_score=0.9925; priority=P1; evidence_status=CONFIRMED; decision_category=IMMEDIATE_ACTION; risk_confidence_category=HIGH_RISK_HIGH_CONFIDENCE; matrix_label=Immediate action; recommended_next_step=Review and remediate; ...},
           @{finding_id=F002; risk_score=0.205;  priority=P4; evidence_status=NOT_CONFIRMED; decision_category=DEFER; risk_confidence_category=LOW_RISK_LOW_CONFIDENCE; matrix_label=Defer and collect evidence; recommended_next_step=Defer for later review; ...}}
```


### Risk-Confidence Matrix Classification

```http
POST /matrix/classify
```

This endpoint accepts a single `FindingInput` and returns the risk-confidence
matrix classification for the finding. The response contains exactly six
fields:

* `finding_id`
* `risk_score`
* `evidence_confidence`
* `risk_confidence_category`
* `matrix_label`
* `recommended_next_step`

The same three matrix fields (`risk_confidence_category`, `matrix_label`,
`recommended_next_step`) are also included in the responses of `/assess`,
`/assess/batch`, `/assess/batch/sorted`, and `/explain`.

#### Request format for `/matrix/classify`

```json
{
  "finding_id": "F001",
  "title": "SQL Injection",
  "severity": "critical",
  "cvss": 10.0,
  "asset": {
    "id": "shop-api-01",
    "criticality": 1.0,
    "internet_exposed": true,
    "environment": "production"
  },
  "validation": {
    "status": "CONFIRMED",
    "confidence": 0.95
  }
}
```

#### Response format for `/matrix/classify`

```json
{
  "finding_id": "F001",
  "risk_score": 0.9925,
  "evidence_confidence": 0.95,
  "risk_confidence_category": "HIGH_RISK_HIGH_CONFIDENCE",
  "matrix_label": "Immediate action",
  "recommended_next_step": "Review and remediate"
}
```

#### PowerShell example for `/matrix/classify`

```powershell
$matrixBody = @{
    finding_id = "F002"
    title      = "Info Disclosure"
    severity   = "low"
    cvss       = 2.0
    asset      = @{
        id               = "dev-server"
        criticality      = 0.2
        internet_exposed = $false
        environment      = "development"
    }
    validation = @{ status = "NOT_CONFIRMED"; confidence = 0.0 }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8003/matrix/classify" `
    -Method POST `
    -ContentType "application/json" `
    -Body $matrixBody
```

Expected result:

```text
finding_id                  : F002
risk_score                  : 0.205
evidence_confidence         : 0.0
risk_confidence_category    : LOW_RISK_LOW_CONFIDENCE
matrix_label                : Defer and collect evidence
recommended_next_step       : Defer for later review
```


### Finding Explanation

```http
POST /explain
```

This endpoint accepts a single `FindingInput` and returns a structured explanation of why the finding received its priority and risk score.

The response includes a `summary` field — a readable sentence that accurately reflects:

* The severity or CVSS score used
* Whether the asset is internet-exposed and in production
* The exact validation status (`CONFIRMED`, `INCONCLUSIVE`, `NOT_CONFIRMED`, or `UNAVAILABLE`)

The `summary` never claims evidence was confirmed unless the validation status is `CONFIRMED`.

#### Request format for `/explain`

```json
{
  "finding_id": "F001",
  "title": "SQL Injection",
  "severity": "critical",
  "cvss": 9.8,
  "cve": "CVE-2021-44228",
  "asset": {
    "id": "shop-api-01",
    "criticality": 1.0,
    "internet_exposed": true,
    "environment": "production"
  },
  "validation": {
    "status": "CONFIRMED",
    "confidence": 0.95
  }
}
```

#### Response format for `/explain`

```json
{
  "finding_id": "F001",
  "title": "SQL Injection",
  "risk_score": 0.9845,
  "priority": "P1",
  "reasons": [
    "Critical severity",
    "Very high CVSS score",
    "Internet-exposed asset",
    "Production environment",
    "Evidence confirmed with 95% confidence"
  ],
  "factors": {
    "severity": 0.98,
    "asset_criticality": 1.0,
    "exposure": 1.0,
    "validation": 0.95
  },
  "evidence_confidence": 0.95,
  "evidence_status": "CONFIRMED",
  "decision_category": "IMMEDIATE_ACTION",
  "risk_confidence_category": "HIGH_RISK_HIGH_CONFIDENCE",
  "matrix_label": "Immediate action",
  "recommended_next_step": "Review and remediate",
  "summary": "Finding F001 received priority P1 with a risk score of 0.9845 because it has a CVSS score of 9.8, affects an internet-exposed production asset, its evidence was confirmed with 95% confidence, and its decision category is IMMEDIATE_ACTION."
}
```

#### Validation status in the summary

| Validation Status | Summary contains           |
| ----------------- | -------------------------- |
| `CONFIRMED`       | "confirmed with X% confidence" |
| `INCONCLUSIVE`    | "inconclusive"             |
| `NOT_CONFIRMED`   | "not confirmed"            |
| `UNAVAILABLE`     | "unavailable"              |

The `summary` always ends with the assigned decision category, for example
`"its decision category is VALIDATE_EVIDENCE."`

#### PowerShell example for `/explain`

```powershell
$explainBody = @{
    finding_id = "F001"
    title      = "SQL Injection"
    severity   = "critical"
    cvss       = 9.8
    cve        = "CVE-2021-44228"
    asset      = @{
        id               = "shop-api-01"
        criticality      = 1.0
        internet_exposed = $true
        environment      = "production"
    }
    validation = @{
        status     = "CONFIRMED"
        confidence = 0.95
    }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8003/explain" `
    -Method POST `
    -ContentType "application/json" `
    -Body $explainBody
```

Expected result:

```text
finding_id         : F001
title              : SQL Injection
risk_score         : 0.9845
priority           : P1
evidence_confidence: 0.95
evidence_status    : CONFIRMED
decision_category  : IMMEDIATE_ACTION
risk_confidence_category: HIGH_RISK_HIGH_CONFIDENCE
matrix_label        : Immediate action
recommended_next_step: Review and remediate
summary            : Finding F001 received priority P1 with a risk score of 0.9845
                     because it has a CVSS score of 9.8, affects an internet-exposed
                     production asset, its evidence was confirmed with 95% confidence,
                     and its decision category is IMMEDIATE_ACTION.
```


### Explain Why This Finding is Prioritized First

```http
POST /explain/why-first
```

This endpoint accepts a single `FindingInput` and returns a structured
explanation object that tells an analyst exactly why the finding was assigned
its priority. It is intended as a drill-down view for the top item(s) in the
dashboard so an analyst can understand a prioritization decision before acting.

#### Response format for `/explain/why-first`

The response contains:

* `finding_id` — the original ID of the finding.
* `title` — the finding title.
* `risk_score` — float between 0.0 and 1.0.
* `priority` — `P1`, `P2`, `P3`, or `P4`.
* `evidence_confidence` — float between 0.0 and 1.0.
* `risk_confidence_category` — the risk-confidence matrix category.
* `explanation` — the structured explanation object with:

| Field                | Description                                                      |
| -------------------- | ---------------------------------------------------------------- |
| `summary`            | Readable sentence explaining the priority and risk score.        |
| `why_this_priority`  | Which priority-threshold band the risk score falls into.         |
| `priority_basis`     | Comparison-friendly phrase naming the factor that contributed the most to the score. |
| `key_drivers`        | Drivers derived from the actual input (severity, CVSS, exposure, environment, criticality, evidence status, missing CVE). |
| `risk_factors`       | The risk-side input values used by the formula.                  |
| `evidence_factors`   | The validation status, confirmation wording, and evidence confidence. |
| `confidence_warning` | Warning surfaced only when evidence is inconclusive, not confirmed, or unavailable; `null` when evidence is confirmed. |
| `recommended_next_step` | Safe, non-exploitative recommended action.                     |

Example response for a critical, internet-exposed, production finding with confirmed evidence:

```json
{
  "finding_id": "F001",
  "title": "SQL Injection",
  "risk_score": 0.9925,
  "priority": "P1",
  "evidence_confidence": 0.95,
  "risk_confidence_category": "HIGH_RISK_HIGH_CONFIDENCE",
  "explanation": {
    "summary": "Finding F001 received priority P1 with a risk score of 0.9925 because it has a CVSS score of 10.0, affects an internet-exposed production asset, its evidence was confirmed with 95% confidence, and its decision category is IMMEDIATE_ACTION.",
    "why_this_priority": "P1 was assigned because the risk score (0.9925) is at or above the P1 threshold (0.8).",
    "priority_basis": "P1 priority driven mainly by severity",
    "key_drivers": [
      "Critical severity",
      "Very high CVSS score (10.0)",
      "Internet-exposed asset",
      "Production environment",
      "High asset criticality (1.0)",
      "Evidence confirmed with 95% confidence",
      "No CVE identifier available"
    ],
    "risk_factors": [
      "Severity: critical (CVSS 10.0)",
      "Asset criticality: 1.0",
      "Exposure: internet-exposed",
      "Environment: production"
    ],
    "evidence_factors": [
      "Evidence status: CONFIRMED",
      "Evidence confirmed with 95% confidence",
      "Evidence confidence: 0.95"
    ],
    "confidence_warning": null,
    "recommended_next_step": "Review and remediate"
  }
}
```

Example response for a finding with inconclusive evidence:

```json
{
  "finding_id": "F003",
  "title": "Cross-Site Scripting",
  "risk_score": 0.705,
  "priority": "P2",
  "evidence_confidence": 0.8,
  "risk_confidence_category": "HIGH_RISK_LOW_CONFIDENCE",
  "explanation": {
    "summary": "Finding F003 received priority P2 with a risk score of 0.705 because it has a CVSS score of 8.0, affects an internet-exposed production asset, its evidence validation was inconclusive (80% confidence), and its decision category is VALIDATE_EVIDENCE.",
    "why_this_priority": "P2 was assigned because the risk score (0.705) is at or above the P2 threshold (0.6) and below the P1 threshold (0.8).",
    "priority_basis": "P2 priority driven mainly by severity",
    "key_drivers": [
      "High severity",
      "Internet-exposed asset",
      "Production environment",
      "Evidence validation was inconclusive (80% confidence)",
      "No CVE identifier available"
    ],
    "risk_factors": [
      "Severity: high (CVSS 8.0)",
      "Asset criticality: 0.5",
      "Exposure: internet-exposed",
      "Environment: production"
    ],
    "evidence_factors": [
      "Evidence status: INCONCLUSIVE",
      "Evidence validation was inconclusive (80% confidence)",
      "Evidence confidence: 0.8"
    ],
    "confidence_warning": "Inconclusive evidence: treat this finding as uncertain until further validation.",
    "recommended_next_step": "Collect additional evidence"
  }
}
```

#### PowerShell example for `/explain/why-first`

```powershell
$whyBody = @{
    finding_id = "F001"
    title      = "SQL Injection"
    severity   = "critical"
    cvss       = 10.0
    asset      = @{
        id               = "shop-api-01"
        criticality      = 1.0
        internet_exposed = $true
        environment      = "production"
    }
    validation = @{ status = "CONFIRMED"; confidence = 0.95 }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8003/explain/why-first" `
    -Method POST `
    -ContentType "application/json" `
    -Body $whyBody
```

The explanation text is deterministic, concise, and accurate: it is generated
only from the actual input values, and it never states or implies that evidence
was confirmed unless the validation status is exactly `CONFIRMED`.

## Analyst Action Queue

The action queue lets Person 4 display findings by the recommended analyst
action instead of (or alongside) numerical priority.

### Queue Categories

Every finding is assigned one of four action queue categories. These are the
same `decision_category` values produced by the engine — the queue does not
introduce a second risk scoring formula:

| Category            | Meaning                                        |
| ------------------- | ---------------------------------------------- |
| `IMMEDIATE_ACTION`  | High risk + high evidence confidence — act now |
| `VALIDATE_EVIDENCE` | High risk + low or uncertain evidence — confirm before acting |
| `REMEDIATE`         | Lower risk + high evidence confidence — schedule remediation |
| `DEFER`             | Lower risk + low or uncertain evidence — revisit later |

The queue recommends safe analyst actions only. It never automatically
exploits, scans, or modifies any target.

### Sorting Rules

Findings are sorted by operational importance:

1. `IMMEDIATE_ACTION`
2. `VALIDATE_EVIDENCE`
3. `REMEDIATE`
4. `DEFER`

Within each category, findings are sorted by descending `risk_score`.

### Endpoint

```http
POST /queue
```

This endpoint accepts a batch of findings (the same `BatchFindingInput` body
used by `/assess/batch`). For every finding it:

* scores the finding using the existing risk formula,
* assigns the evidence confidence,
* assigns the risk-confidence matrix category,
* assigns the action queue category (`decision_category`),
* sorts the results by operational importance.

#### Request format for `/queue`

```json
{
  "findings": [
    {
      "finding_id": "F001",
      "title": "SQL Injection",
      "severity": "critical",
      "cvss": 10.0,
      "asset": {
        "id": "shop-api-01",
        "criticality": 1.0,
        "internet_exposed": true,
        "environment": "production"
      },
      "validation": { "status": "CONFIRMED", "confidence": 0.95 }
    },
    {
      "finding_id": "F002",
      "title": "Info Disclosure",
      "severity": "low",
      "cvss": 2.0,
      "asset": {
        "id": "dev-server",
        "criticality": 0.2,
        "internet_exposed": false,
        "environment": "development"
      },
      "validation": { "status": "NOT_CONFIRMED", "confidence": 0.0 }
    }
  ]
}
```

#### Response format for `/queue`

The response contains `count` (number of items returned), `summary`, and
`items`.

`summary` contains `total` plus `categories` — the number of findings in each
queue category. All four category keys are always present.

`items` is an array of queue items, each containing:

* `finding_id`
* `title`
* `risk_score`
* `priority`
* `evidence_confidence`
* `evidence_status`
* `risk_confidence_category`
* `decision_category` (the action queue category)
* `reasons`
* `recommended_next_step`

```json
{
  "count": 2,
  "summary": {
    "total": 2,
    "categories": {
      "IMMEDIATE_ACTION": 1,
      "VALIDATE_EVIDENCE": 0,
      "REMEDIATE": 0,
      "DEFER": 1
    }
  },
  "items": [
    {
      "finding_id": "F001",
      "title": "SQL Injection",
      "risk_score": 0.9925,
      "priority": "P1",
      "evidence_confidence": 0.95,
      "evidence_status": "CONFIRMED",
      "risk_confidence_category": "HIGH_RISK_HIGH_CONFIDENCE",
      "decision_category": "IMMEDIATE_ACTION",
      "reasons": ["Critical severity", "Very high CVSS score", "Internet-exposed asset", "Production environment", "Evidence confirmed with 95% confidence"],
      "recommended_next_step": "Review and remediate"
    },
    {
      "finding_id": "F002",
      "title": "Info Disclosure",
      "risk_score": 0.205,
      "priority": "P4",
      "evidence_confidence": 0.0,
      "evidence_status": "NOT_CONFIRMED",
      "risk_confidence_category": "LOW_RISK_LOW_CONFIDENCE",
      "decision_category": "DEFER",
      "reasons": ["Evidence was not confirmed", "No CVE identifier available"],
      "recommended_next_step": "Defer for later review"
    }
  ]
}
```

#### Filtering

Optional query parameters:

| Parameter  | Allowed values                                                            |
| ---------- | ------------------------------------------------------------------------- |
| `category` | `IMMEDIATE_ACTION`, `VALIDATE_EVIDENCE`, `REMEDIATE`, `DEFER`             |
| `priority` | `P1`, `P2`, `P3`, `P4`                                                    |

Examples:

```http
POST /queue?category=VALIDATE_EVIDENCE
POST /queue?priority=P1
POST /queue?category=DEFER&priority=P4
```

Invalid filter values return HTTP `422` with a clear validation error message
listing the allowed values.

#### PowerShell example for `/queue`

```powershell
$queueBody = Get-Content -Path "examples\sample-findings.json" -Raw

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8003/queue" `
    -Method POST `
    -ContentType "application/json" `
    -Body $queueBody
```

Filtered example (validation-evidence worklist only):

```powershell
Invoke-RestMethod `
    -Uri "http://127.0.0.1:8003/queue?category=VALIDATE_EVIDENCE" `
    -Method POST `
    -ContentType "application/json" `
    -Body $queueBody
```

## Human-in-the-Loop Review

The engine may recommend an action, but only a human reviewer can approve,
reject, defer, or request more evidence. The two review endpoints provide a
safe workflow for putting every prioritised finding into a reviewer's hands
and recording the outcome.

The service is stateless: preparation records and review decisions are
returned immediately but are not permanently persisted unless a storage layer
is added. Integrations must capture the returned audit metadata and store it
in the upstream system of record.

### Evidence Provenance

`POST /review/prepare` and `POST /assess` accept an optional
`evidence_provenance` object. The fields are:

| Field                | Type     | Max length | Allowed values                                          |
| -------------------- | -------- | ---------- | ------------------------------------------------------- |
| `source`             | string   | 100        | Any non-sensitive description                           |
| `source_type`        | string   |            | `SCANNER`, `MANUAL`, `OSINT`, `EXTERNAL`, `UNKNOWN`    |
| `observed_at`        | datetime |            | ISO 8601 timestamp (e.g. `2026-09-10T08:15:30Z`)       |
| `validation_method`  | string   | 150        | Any non-sensitive description                           |
| `evidence_reference` | string   | 250        | A report ID, ticket number, or similar pointer          |

The API never accepts secrets, credentials, tokens, or exploit payloads.
Fields that contain obvious secret-like content (private keys, bearer tokens,
`password=`, `token=`, etc.) are rejected with HTTP 422.

### Supported Review Statuses

| Status               | Meaning                                                      |
| -------------------- | ------------------------------------------------------------ |
| `PENDING_REVIEW`     | Awaiting human review (the only status set by `/review/prepare`) |
| `APPROVED`           | Reviewer confirmed the finding and agreed to the next step   |
| `REJECTED`           | Reviewer determined the finding is not valid in this context |
| `NEEDS_MORE_EVIDENCE`| More evidence or validation is required before deciding      |
| `DEFERRED`           | The finding is valid but should be addressed later           |
| `RESOLVED`           | The issue has been addressed or remediated                    |

The system never automatically moves a finding out of `PENDING_REVIEW`.

### Prepare Finding for Review

```http
POST /review/prepare
```

Accepts a standard `FindingInput` body. Returns:

* `finding_id`
* `risk_score`
* `priority`
* `evidence_confidence`
* `evidence_provenance`
* `audit_metadata` — timestamps, action (`PREPARED_FOR_REVIEW`), and null reviewer fields
* `review_status` — always `PENDING_REVIEW`
* `recommended_next_step`

```powershell
$findingPayload = Get-Content -Path "examples\sample-findings.json" -Raw | \
    ConvertFrom-Json | ForEach-Object { $_.findings[0] } | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8003/review/prepare" `
    -Method POST `
    -ContentType "application/json" `
    -Body $findingPayload
```

### Record a Review Decision

```http
POST /review/decision
```

Accepts a JSON body:

```json
{
  "finding_id": "SYN-001",
  "review_status": "APPROVED",
  "reviewer": "analyst-niles",
  "review_note": "Confirmed after packet capture. Schedule patching."
}
```

* `review_status` must be one of the supported values; anything else is
  rejected with HTTP 422.
* `reviewer` is a non-sensitive display name or internal alias (max 50 chars).
* `review_note` is optional (max 500 chars).
* Both `reviewer` and `review_note` are rejected if they contain secret-like
  content.

```powershell
$review = @{
    finding_id = "SYN-001"
    review_status = "APPROVED"
    reviewer = "analyst-niles"
    review_note = "Confirmed after packet capture. Schedule patching."
} | ConvertTo-Json

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8003/review/decision" `
    -Method POST `
    -ContentType "application/json" `
    -Body $review
```

### Audit Metadata

Both review endpoints return an `audit_metadata` object:

```json
{
    "created_at": "2026-09-11T13:42:00Z",
    "status_changed_at": "2026-09-11T13:42:00Z",
    "action": "PREPARED_FOR_REVIEW",
    "reviewer": null,
    "review_note": null
}
```

On preparation, `action` is `PREPARED_FOR_REVIEW` and reviewer fields are
null. On a review decision, `action` is `REVIEW_DECISION` and `reviewer` and
`review_note` carry the submitted values.

### Integration Guidance for Person 4

The dashboard should:

1. Call `POST /review/prepare` for every prioritised finding.
2. Present the prepared findings in a review queue, showing `risk_score`,
   `priority`, `evidence_confidence`, and the `evidence_provenance` summary.
3. On reviewer action, call `POST /review/decision` and display the returned
   `audit_metadata`.
4. Persist the returned `audit_metadata` in the upstream system of record —
   the service does not retain it.

## Risk Scoring Formula

The current deterministic risk formula is:

```text
risk_score =
    0.40 * severity
  + 0.25 * asset_criticality
  + 0.20 * exposure
  + 0.15 * validation
```

The final score is limited to the range:

```text
0.0 to 1.0
```

### Scoring Factors

#### Severity

If a CVSS score is available:

```text
severity_factor = CVSS / 10
```

Otherwise, the severity label is converted using the following values:

| Severity      | Factor |
| ------------- | -----: |
| Critical      |   1.00 |
| High          |   0.80 |
| Medium        |   0.50 |
| Low           |   0.20 |
| Informational |   0.05 |
| Unknown       |   0.30 |

#### Asset Criticality

Asset criticality is a value between `0.0` and `1.0`.

Examples:

```text
0.0 = Non-critical asset
0.5 = Moderately important asset
1.0 = Business-critical asset
```

#### Exposure

```text
1.0 = Internet-exposed asset
0.3 = Not internet-exposed
```

#### Validation

The validation factor depends on the validation status:

| Validation Status | Calculation                 |
| ----------------- | --------------------------- |
| CONFIRMED         | Validation confidence       |
| INCONCLUSIVE      | Validation confidence × 0.5 |
| NOT_CONFIRMED     | 0.1                         |
| UNAVAILABLE       | 0.2                         |

The validation confidence must be between `0.0` and `1.0`.

## Priority Thresholds

| Priority |             Risk Score |
| -------- | ---------------------: |
| P1       |              `>= 0.80` |
| P2       | `>= 0.60` and `< 0.80` |
| P3       | `>= 0.35` and `< 0.60` |
| P4       |               `< 0.35` |

Priority levels are assigned deterministically using the final risk score.

## Evidence Confidence Score

The Evidence Confidence Score is calculated **separately** from the risk score. It
reflects how much the evidence behind a finding can be trusted, based on the
validation result only.

| Validation Status | Evidence Confidence                             |
| ----------------- | ---------------------------------------------- |
| `CONFIRMED`       | The supplied validation confidence             |
| `INCONCLUSIVE`    | The supplied confidence (status stays `INCONCLUSIVE`) |
| `NOT_CONFIRMED`   | `0.0` — unconfirmed evidence is not treated as confirmed |
| `UNAVAILABLE`     | `0.0` — no validation data means no confidence |

The value is clamped to the range `0.0` to `1.0`.

Every result also exposes `evidence_status`, which always matches the original
validation status, and `decision_category`, which is derived by combining the
risk score with the evidence confidence.

## Decision Categories

| Category            | Condition                                      |
| ------------------- | ---------------------------------------------- |
| `IMMEDIATE_ACTION`  | High risk (`>= 0.60`) + high evidence confidence (`>= 0.70` confirmed) |
| `VALIDATE_EVIDENCE` | High risk (`>= 0.60`) + low or uncertain evidence confidence |
| `REMEDIATE`         | Lower risk (`< 0.60`) + high evidence confidence (`>= 0.70` confirmed) |
| `DEFER`             | Lower risk (`< 0.60`) + low or uncertain evidence confidence |

Rules:

* "High risk" means the risk score is at or above the P2 threshold (`0.60`).
* Evidence is only considered "high confidence" when `evidence_status` is
  `CONFIRMED` and the confidence is at least `0.70`.
* `INCONCLUSIVE`, `NOT_CONFIRMED`, and `UNAVAILABLE` evidence is always treated
  as uncertain, regardless of any numeric confidence supplied, so it can never
  produce `IMMEDIATE_ACTION` or `REMEDIATE`.

## Risk-Confidence Classification Matrix

The matrix combines the risk band with the evidence confidence to assign every
finding a deterministic `risk_confidence_category`, a human-readable
`matrix_label`, and a safe `recommended_next_step`.

### Thresholds

| Dimension | High when |
| --------- | --------- |
| Risk      | `risk_score >= 0.60` (the P2 / high-risk threshold) |
| Confidence | `evidence_status == "CONFIRMED"` and `evidence_confidence >= 0.70` |

The thresholds are inclusive: a risk score exactly `0.60` is high risk, and an
evidence confidence exactly `0.70` is high confidence.

### Matrix

| Risk band      | Confidence | `risk_confidence_category`     | `matrix_label`               | `recommended_next_step`                    |
| -------------- | ---------- | ------------------------------ | ---------------------------- | ------------------------------------------ |
| `>= 0.60` high | high       | `HIGH_RISK_HIGH_CONFIDENCE`    | Immediate action             | Review and remediate                       |
| `>= 0.60` high | low/uncertain | `HIGH_RISK_LOW_CONFIDENCE`     | Validate evidence            | Collect additional evidence                |
| `< 0.60` low   | high       | `LOW_RISK_HIGH_CONFIDENCE`     | Routine remediation          | Validate asset and finding context         |
| `< 0.60` low   | low/uncertain | `LOW_RISK_LOW_CONFIDENCE`      | Defer and collect evidence   | Defer for later review                     |

### Rules

* The classification is deterministic — a pure function of `risk_score`, `evidence_confidence`, and `evidence_status`.
* Only `CONFIRMED` evidence can ever be high confidence. `INCONCLUSIVE`, `NOT_CONFIRMED`, and `UNAVAILABLE` evidence stays in the low-confidence column of the matrix even when the numeric confidence is at or above `0.70`.
* The matrix reuses the same thresholds and confidence rule as the decision categories, so it stays compatible: `HIGH_RISK_HIGH_CONFIDENCE` corresponds to `IMMEDIATE_ACTION`, `HIGH_RISK_LOW_CONFIDENCE` to `VALIDATE_EVIDENCE`, `LOW_RISK_HIGH_CONFIDENCE` to `REMEDIATE`, and `LOW_RISK_LOW_CONFIDENCE` to `DEFER`.
* The recommended next steps are safe and non-exploitative; they never instruct the engine to scan, probe, or attack a target.

## Request Format

Example request for `/assess`:

```json
{
  "finding_id": "F001",
  "cluster_id": "CL001",
  "title": "SQL Injection",
  "severity": "critical",
  "cve": "CVE-2021-44228",
  "cvss": 10.0,
  "asset": {
    "id": "shop-api-01",
    "criticality": 1.0,
    "internet_exposed": true,
    "environment": "production"
  },
  "validation": {
    "status": "CONFIRMED",
    "confidence": 0.95
  }
}
```

## Response Format

Example response:

```json
{
  "finding_id": "F001",
  "risk_score": 0.9925,
  "priority": "P1",
  "reasons": [
    "Critical severity",
    "Very high CVSS score",
    "Internet-exposed asset",
    "Production environment",
    "Evidence confirmed with 95% confidence"
  ],
  "factors": {
    "severity": 1.0,
    "asset_criticality": 1.0,
    "exposure": 1.0,
    "validation": 0.95
  },
  "evidence_confidence": 0.95,
  "evidence_status": "CONFIRMED",
  "decision_category": "IMMEDIATE_ACTION",
  "risk_confidence_category": "HIGH_RISK_HIGH_CONFIDENCE",
  "matrix_label": "Immediate action",
  "recommended_next_step": "Review and remediate"
}
```

## Windows PowerShell Test

Use the following commands to test the running service:

```powershell
$body = @{
    finding_id = "F001"
    cluster_id = "CL001"
    title = "SQL Injection"
    severity = "critical"
    cve = "CVE-2021-44228"
    cvss = 10.0
    asset = @{
        id = "shop-api-01"
        criticality = 1.0
        internet_exposed = $true
        environment = "production"
    }
    validation = @{
        status = "CONFIRMED"
        confidence = 0.95
    }
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8003/assess" `
    -Method POST `
    -ContentType "application/json" `
    -Body $body
```

Expected result:

```text
finding_id         : F001
risk_score         : 0.9925
priority           : P1
evidence_confidence: 0.95
evidence_status    : CONFIRMED
decision_category  : IMMEDIATE_ACTION
risk_confidence_category: HIGH_RISK_HIGH_CONFIDENCE
matrix_label        : Immediate action
recommended_next_step: Review and remediate
```

### Batch Assessment PowerShell Test

```powershell
$batchBody = @{
    findings = @(
        @{
            finding_id = "F001"
            title      = "SQL Injection"
            severity   = "critical"
            cvss       = 10.0
            asset      = @{
                id               = "shop-api-01"
                criticality      = 1.0
                internet_exposed = $true
                environment      = "production"
            }
            validation = @{
                status     = "CONFIRMED"
                confidence = 0.95
            }
        },
        @{
            finding_id = "F002"
            title      = "Info Disclosure"
            severity   = "low"
            cvss       = 2.0
            asset      = @{
                id               = "dev-server"
                criticality      = 0.2
                internet_exposed = $false
                environment      = "development"
            }
            validation = @{
                status     = "NOT_CONFIRMED"
                confidence = 0.0
            }
        }
    )
} | ConvertTo-Json -Depth 5

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8003/assess/batch" `
    -Method POST `
    -ContentType "application/json" `
    -Body $batchBody
```

Expected result:

```text
count   : 2
results : {@{finding_id=F001; risk_score=0.9925; priority=P1; evidence_status=CONFIRMED; decision_category=IMMEDIATE_ACTION; risk_confidence_category=HIGH_RISK_HIGH_CONFIDENCE; matrix_label=Immediate action; recommended_next_step=Review and remediate; ...},
           @{finding_id=F002; risk_score=0.205;  priority=P4; evidence_status=NOT_CONFIRMED; decision_category=DEFER; risk_confidence_category=LOW_RISK_LOW_CONFIDENCE; matrix_label=Defer and collect evidence; recommended_next_step=Defer for later review; ...}}
```

### Loading the Synthetic Dataset

You can load the provided synthetic dataset from `examples\sample-findings.json` and send it to the batch assessment endpoint using PowerShell:

```powershell
$jsonBody = Get-Content -Path "examples\sample-findings.json" -Raw

Invoke-RestMethod `
    -Uri "http://127.0.0.1:8003/assess/batch/sorted" `
    -Method POST `
    -ContentType "application/json" `
    -Body $jsonBody
```

## Integration Flow

The intended integration flow is:

```text
Person 1:
Finding Normalization
        |
        v
Person 2:
Evidence Validation
        |
        v
Person 3:
Risk Intelligence Engine
        |
        v
Person 4:
Dashboard and Human Approval Workflow
```

The Risk Intelligence Engine consumes:

* Finding ID
* Finding title
* Severity
* CVSS score
* CVE identifier
* Asset context
* Asset criticality
* Internet exposure
* Environment
* Validation status
* Validation confidence

The engine produces:

* Finding ID
* Risk score
* Priority
* Explanation reasons
* Individual scoring factors
* Evidence confidence score
* Decision category
* Risk-confidence matrix category, matrix label, and recommended next step

## Safety Rules

The service follows these rules:

* A finding is not considered confirmed unless its validation status is `CONFIRMED`.
* Unconfirmed evidence must not be described as confirmed.
* `INCONCLUSIVE` validation must reduce confidence rather than increase it.
* Missing validation data must not be treated as confirmed evidence.
* `NOT_CONFIRMED` and `UNAVAILABLE` evidence always produce an evidence confidence of `0.0`; the supplied confidence value is never used as if it were proof.
* `INCONCLUSIVE` evidence is always treated as uncertain for decision purposes, regardless of the numeric confidence supplied.
* `INCONCLUSIVE`, `NOT_CONFIRMED`, and `UNAVAILABLE` evidence can never be classified as high confidence in the risk-confidence matrix, even when the numeric confidence is at or above `0.70`.
* Recommended next steps in the matrix are safe and non-exploitative; they never instruct the engine to scan, probe, or attack a target.
* The engine must not claim that exploitation occurred without validation evidence.
* The service does not exploit targets.
* Scores must be deterministic and reproducible.
* The evidence confidence score is computed independently from the risk score.
* All input values must be validated using Pydantic models.
* The service only evaluates synthetic or controlled-lab findings.

## Dashboard Integration (Person 4)

The Risk Intelligence Engine provides the prioritized results that should be displayed in the analyst dashboard.

### How to Call the Service

The dashboard should use the `/assess/batch/sorted` endpoint to submit multiple findings at once and receive them back in prioritized order (P1 to P4).

To drive an action-oriented worklist, the dashboard should call `POST /queue`
with the same batch body. The response groups every finding into an action
queue category (`IMMEDIATE_ACTION`, `VALIDATE_EVIDENCE`, `REMEDIATE`, `DEFER`)
sorted by operational importance, and the `summary.categories` object lets the
dashboard render tab counts (e.g. "Validate evidence (3)"). The optional
`category` and `priority` query parameters allow building filtered worklists
such as "all findings requiring evidence validation".

For the human-in-the-loop review flow, the dashboard should call
`POST /review/prepare` for each finding it presents to an analyst and display
the returned risk score, priority, evidence confidence, provenance summary,
and the `PENDING_REVIEW` status. When the analyst approves, rejects, defers,
or requests more evidence, the dashboard should call `POST /review/decision`
with the analyst's identifier and note, then persist the returned
`audit_metadata` in the system of record — the service is stateless and does
not retain review decisions.

### Expected JSON Fields

The dashboard should parse the response envelope which contains:
* `count`: Integer representing the total number of processed findings.
* `results`: An array of objects, each containing:
  * `finding_id`: The original ID of the finding.
  * `risk_score`: Float between 0.0 and 1.0.
  * `priority`: String (P1, P2, P3, or P4).
  * `reasons`: Array of strings detailing the risk factors.
  * `factors`: Object with the numerical breakdown of the score.
  * `evidence_confidence`: Float between 0.0 and 1.0, calculated independently of the risk score.
  * `evidence_status`: String (`CONFIRMED`, `INCONCLUSIVE`, `NOT_CONFIRMED`, or `UNAVAILABLE`), always matching the original validation status.
  * `decision_category`: String (`IMMEDIATE_ACTION`, `VALIDATE_EVIDENCE`, `REMEDIATE`, or `DEFER`) indicating the recommended next step.
  * `risk_confidence_category`: String (`HIGH_RISK_HIGH_CONFIDENCE`, `HIGH_RISK_LOW_CONFIDENCE`, `LOW_RISK_HIGH_CONFIDENCE`, or `LOW_RISK_LOW_CONFIDENCE`) placing the finding in the risk-confidence matrix.
  * `matrix_label`: Human-readable label for the matrix quadrant (e.g. `Immediate action`).
  * `recommended_next_step`: Safe, non-exploitative recommended action (e.g. `Review and remediate`).

For detailed human-readable summaries, the dashboard can call the `/explain` endpoint passing a single finding to get a `summary` sentence.

To let an analyst drill down into why the top finding is prioritized, call `/explain/why-first` with that finding. It returns the same `summary` plus a structured `explanation` object with `why_this_priority`, `priority_basis`, `key_drivers`, `risk_factors`, `evidence_factors`, `confidence_warning`, and `recommended_next_step`. The dashboard can display `key_drivers` as badge chips, `confidence_warning` as an inline warning banner, and `recommended_next_step` as the action button label.

### Example Response Handling

```javascript
// Example in JavaScript (Frontend Dashboard)
async function fetchPrioritizedFindings(findingsPayload) {
    const response = await fetch('http://127.0.0.1:8003/assess/batch/sorted', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ findings: findingsPayload })
    });
    
    const data = await response.json();
    console.log(`Loaded ${data.count} prioritized findings.`);
    
    // The results are already sorted P1 to P4
    data.results.forEach(result => {
        console.log(`[${result.priority}] ${result.finding_id} - Score: ${result.risk_score} - Decision: ${result.decision_category} - Matrix: ${result.risk_confidence_category} - Next step: ${result.recommended_next_step}`);
    });
}
```

## Future Enhancements

Possible future improvements include:

* CVE enrichment using NVD
* EPSS probability integration
* CISA KEV status
* OSV package vulnerability enrichment
* Exploit availability indicators
* Asset business impact
* Vulnerability age
* Active exploitation signals
* Confidence calibration
* Analyst feedback
* Risk score history
* Export to dashboard and case-management systems

## Development Workflow

After making changes:

```powershell
$env:PYTHONPATH = (Get-Location).Path
pytest -v
```

Then return to the repository root:

```powershell
cd ..\..
```

Review changes:

```powershell
git status
git diff
```

Commit changes:

```powershell
git add services/risk-engine
git commit -m "Update risk intelligence engine documentation"
```

Push changes:

```powershell
git push
```

## Current Version

```text
0.1.0
```

## Owner

```text
Person 3 - Risk Intelligence & Prioritization Engineer
```
