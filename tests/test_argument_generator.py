"""Tests for LegalArgumentGenerator."""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def generator():
    from src.argument_generator import LegalArgumentGenerator
    return LegalArgumentGenerator()


@pytest.fixture
def sample_case():
    return {
        "metadata": {
            "case_id": "TEST-001",
            "case_type": "Criminal",
            "charges": ["IPC 420 — Cheating", "IPC 468 — Forgery"],
            "court": "Sessions Court Mumbai",
            "status": "Trial",
        }
    }


@pytest.fixture
def sample_evidence():
    return [
        {"file_name": "bank_statement.pdf", "doc_type": "pdf", "evidence_strength": 8.0, "summary": "Bank transfers to accused"},
        {"file_name": "victim_statement.pdf", "doc_type": "pdf", "evidence_strength": 7.5, "summary": "Victim's account of fraud"},
    ]


def test_generate_prosecution_argument(generator, sample_case, sample_evidence):
    args = generator.generate_prosecution_argument(
        case_data=sample_case,
        evidence_analyses=sample_evidence,
        legal_context={},
        precedents=[],
        style="balanced",
    )

    assert "side" in args
    assert args["side"] == "prosecution"
    assert "opening_statement" in args
    assert "closing_statement" in args
    assert "argument_strength_score" in args
    assert isinstance(args["argument_strength_score"], float)


def test_generate_defense_argument(generator, sample_case, sample_evidence):
    args = generator.generate_defense_argument(
        case_data=sample_case,
        evidence_analyses=sample_evidence,
        legal_context={},
        precedents=[],
        style="balanced",
    )

    assert args["side"] == "defense"
    assert "opening_statement" in args
    assert "closing_statement" in args
    assert "acquittal_grounds" in args


def test_compare_argument_strength(generator):
    prosecution = {"opening_statement": "Strong prosecution case.", "argument_strength_score": 7.5}
    defense = {"opening_statement": "Strong defense case.", "argument_strength_score": 6.0}

    result = generator.compare_argument_strength(prosecution, defense)
    assert "winner_prediction" in result
    assert result["winner_prediction"] in ("Prosecution", "Defense")
    assert "overall_prosecution_score" in result
    assert "overall_defense_score" in result


def test_build_case_summary(generator, sample_case):
    summary = generator._build_case_summary(sample_case)
    assert "TEST-001" in summary
    assert "Criminal" in summary


def test_build_evidence_summary(generator, sample_evidence):
    summary = generator._build_evidence_summary(sample_evidence)
    assert "bank_statement.pdf" in summary
    assert len(summary) > 0
