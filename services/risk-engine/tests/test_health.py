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