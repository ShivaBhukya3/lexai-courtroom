"""Tests for VerdictPredictor ML model."""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture(scope="module")
def predictor():
    from src.verdict_predictor import VerdictPredictor
    p = VerdictPredictor()
    if not p._models_trained:
        p.train_model()
    return p


def test_generate_training_data(predictor):
    df = predictor.generate_training_data()
    assert len(df) == 1000
    assert "conviction" in df.columns
    assert df["conviction"].isin([0, 1]).all()
    conviction_rate = df["conviction"].mean()
    assert 0.40 <= conviction_rate <= 0.80, f"Conviction rate out of expected range: {conviction_rate}"


def test_train_model(predictor):
    metrics = predictor.train_model()
    assert "random_forest_accuracy" in metrics
    assert metrics["random_forest_accuracy"] > 0.55
    assert metrics["training_samples"] == 800


def test_predict_verdict_conviction(predictor):
    features = {
        "evidence_count": 12,
        "evidence_strength_avg": 8.5,
        "witness_count": 5,
        "witness_credibility_avg": 8.0,
        "precedent_match_score": 0.85,
        "charge_severity": 4,
        "defense_argument_score": 5.0,
        "prosecution_argument_score": 9.0,
        "ipc_section_severity": 4,
        "case_duration_days": 400,
        "judge_type": "sessions",
        "bail_status": 0,
        "confession_present": 1,
        "documentary_evidence": 1,
        "forensic_evidence": 1,
    }
    result = predictor.predict_verdict(features)

    assert "verdict" in result
    assert result["verdict"] in ("Conviction", "Acquittal")
    assert 0 <= result["conviction_probability"] <= 1
    assert 0 <= result["acquittal_probability"] <= 1
    assert abs(result["conviction_probability"] + result["acquittal_probability"] - 1.0) < 0.01
    assert isinstance(result["key_factors"], list)

    # Strong case should lean conviction
    assert result["conviction_probability"] > 0.5


def test_predict_verdict_acquittal(predictor):
    features = {
        "evidence_count": 2,
        "evidence_strength_avg": 3.0,
        "witness_count": 1,
        "witness_credibility_avg": 4.0,
        "precedent_match_score": 0.2,
        "charge_severity": 2,
        "defense_argument_score": 9.0,
        "prosecution_argument_score": 4.0,
        "ipc_section_severity": 2,
        "case_duration_days": 200,
        "judge_type": "magistrate",
        "bail_status": 1,
        "confession_present": 0,
        "documentary_evidence": 0,
        "forensic_evidence": 0,
    }
    result = predictor.predict_verdict(features)

    # Weak prosecution case should lean acquittal
    assert result["acquittal_probability"] > 0.4


def test_sensitivity_analysis(predictor):
    features = {
        "evidence_count": 5, "evidence_strength_avg": 5.0, "witness_count": 2,
        "witness_credibility_avg": 6.0, "precedent_match_score": 0.5, "charge_severity": 3,
        "defense_argument_score": 6.0, "prosecution_argument_score": 6.0, "ipc_section_severity": 3,
        "case_duration_days": 365, "judge_type": "sessions", "bail_status": 0,
        "confession_present": 0, "documentary_evidence": 1, "forensic_evidence": 0,
    }
    result = predictor.sensitivity_analysis(features)

    assert "base_probability" in result
    assert "scenarios" in result
    assert len(result["scenarios"]) > 0
    assert "Add forensic evidence" in result["scenarios"]
