"""Integration tests for FastAPI endpoints."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from api.main import app
    with TestClient(app) as c:
        yield c


def test_health_check(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root_endpoint(client):
    response = client.get("/", follow_redirects=False)
    # Root redirects to /dashboard/ or returns JSON/HTML — all acceptable
    assert response.status_code in (200, 307, 308)
    if response.status_code == 200:
        ct = response.headers.get("content-type", "")
        if "html" in ct:
            assert "LexAI" in response.text
        else:
            assert "LexAI" in response.json().get("message", "")
    else:
        assert "/dashboard" in response.headers.get("location", "")


def test_create_case(client):
    payload = {
        "case_name": "Test Property Dispute",
        "case_type": "Civil",
        "sub_type": "Property Dispute",
        "court": "Civil Court Test",
        "charges": ["Recovery of possession"],
        "plaintiff_name": "Test Plaintiff",
        "defendant_name": "Test Defendant",
    }
    response = client.post("/api/v1/cases/create", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "case_id" in data
    assert data["case_type"] == "Civil"
    return data["case_id"]


def test_list_cases(client):
    response = client.get("/api/v1/cases/list")
    assert response.status_code == 200
    data = response.json()
    assert "cases" in data
    assert isinstance(data["cases"], list)


def test_get_case_not_found(client):
    response = client.get("/api/v1/cases/NONEXISTENT-CASE")
    assert response.status_code == 404


def test_verdict_predict(client):
    # First create a case
    create_response = client.post("/api/v1/cases/create", json={
        "case_name": "Verdict Test Case", "case_type": "Criminal",
        "charges": ["IPC 420"], "plaintiff_name": "P", "defendant_name": "D"
    })
    case_id = create_response.json()["case_id"]

    # Predict verdict with explicit features
    predict_response = client.post("/api/v1/verdict/predict", json={
        "case_id": case_id,
        "features": {
            "evidence_count": 5, "evidence_strength_avg": 6.0, "witness_count": 2,
            "witness_credibility_avg": 7.0, "precedent_match_score": 0.6, "charge_severity": 3,
            "defense_argument_score": 6.0, "prosecution_argument_score": 7.0, "ipc_section_severity": 3,
            "case_duration_days": 365, "judge_type": "sessions", "bail_status": 0,
            "confession_present": 0, "documentary_evidence": 1, "forensic_evidence": 0
        }
    })
    assert predict_response.status_code == 200
    data = predict_response.json()
    assert "verdict" in data
    assert data["verdict"] in ("Conviction", "Acquittal")
    assert 0 <= data["conviction_probability"] <= 1


def test_research_sections(client):
    response = client.post("/api/v1/research/sections", json={"query": "cheating fraud deception"})
    assert response.status_code == 200
    data = response.json()
    assert "results" in data


def test_research_precedents(client):
    response = client.post("/api/v1/research/precedents", json={"query": "murder rarest of rare"})
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
