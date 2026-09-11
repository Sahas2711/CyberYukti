# ACSC Risk Intelligence Engine

The Risk Intelligence Engine is the risk-scoring and prioritization service of the ACSC Autonomous Vulnerability Triage & Evidence Engine.

It receives normalized security findings and validation results, calculates a deterministic risk score, assigns a priority level, and returns human-readable reasons for the decision.

## Responsibilities

The service performs the following tasks:

* Calculate risk scores for security findings
* Consider severity and CVSS scores
* Consider asset criticality
* Consider internet exposure
* Consider validation status and confidence
* Assign priority levels from P1 to P4
* Sort findings by priority and risk score
* Return explanations for prioritization decisions
* Support single and batch assessment

The service does not independently exploit targets or claim that a finding is confirmed without validation evidence.

## Project Structure

```text
risk-engine/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── scoring.py
│   └── prioritization.py
├── tests/
│   └── test_health.py
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

This endpoint accepts a list of findings and returns one result for each finding.

### Sorted Batch Assessment

```http
POST /assess/batch/sorted
```

This endpoint accepts a list of findings and returns results sorted by:

1. Priority level, with P1 first
2. Risk score, with the highest score first within the same priority

### Finding Explanation

```http
POST /explain
```

This endpoint returns a human-readable summary of the finding’s risk assessment.

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
  }
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
finding_id : F001
risk_score : 0.9925
priority   : P1
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

## Safety Rules

The service follows these rules:

* A finding is not considered confirmed unless its validation status is `CONFIRMED`.
* `INCONCLUSIVE` validation must reduce confidence rather than increase it.
* Missing validation data must not be treated as confirmed evidence.
* The engine must not claim that exploitation occurred without validation evidence.
* Scores must be deterministic and reproducible.
* All input values must be validated using Pydantic models.
* The service is intended for synthetic findings and controlled lab environments.

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
