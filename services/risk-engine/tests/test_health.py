from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_critical_confirmed_finding_is_p1():
    payload = {
        "finding_id": "F001",
        "title": "SQL Injection",
        "severity": "critical",
        "cvss": 10.0,
        "asset": {
            "id": "production-api",
            "criticality": 1.0,
            "internet_exposed": True,
            "environment": "production",
        },
        "validation": {
            "status": "CONFIRMED",
            "confidence": 0.95,
        },
    }

    response = client.post("/assess", json=payload)

    assert response.status_code == 200

    result = response.json()

    assert result["priority"] == "P1"
    assert result["risk_score"] >= 0.80

def test_batch_assessment_returns_multiple_results():
    payload = [
        {
            "finding_id": "F001",
            "title": "Critical SQL Injection",
            "severity": "critical",
            "cvss": 10.0,
            "asset": {
                "id": "prod-api",
                "criticality": 1.0,
                "internet_exposed": True,
                "environment": "production",
            },
            "validation": {
                "status": "CONFIRMED",
                "confidence": 0.95,
            },
        },
        {
            "finding_id": "F002",
            "title": "Low Information Disclosure",
            "severity": "low",
            "cvss": 2.0,
            "asset": {
                "id": "test-server",
                "criticality": 0.2,
                "internet_exposed": False,
                "environment": "testing",
            },
            "validation": {
                "status": "INCONCLUSIVE",
                "confidence": 0.5,
            },
        },
    ]

    response = client.post("/assess/batch", json=payload)

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_sorted_batch_places_highest_priority_first():
    payload = [
        {
            "finding_id": "F002",
            "title": "Low Finding",
            "severity": "low",
            "cvss": 2.0,
            "asset": {
                "id": "test-server",
                "criticality": 0.2,
                "internet_exposed": False,
                "environment": "testing",
            },
            "validation": {
                "status": "INCONCLUSIVE",
                "confidence": 0.5,
            },
        },
        {
            "finding_id": "F001",
            "title": "Critical Finding",
            "severity": "critical",
            "cvss": 10.0,
            "asset": {
                "id": "prod-api",
                "criticality": 1.0,
                "internet_exposed": True,
                "environment": "production",
            },
            "validation": {
                "status": "CONFIRMED",
                "confidence": 0.95,
            },
        },
    ]

    response = client.post("/assess/batch/sorted", json=payload)

    assert response.status_code == 200

    results = response.json()

    assert results[0]["finding_id"] == "F001"
    assert results[0]["priority"] == "P1"