"""Tests for MultimodalDocumentProcessor."""

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def processor():
    from src.document_processor import MultimodalDocumentProcessor
    return MultimodalDocumentProcessor()


def test_processor_initialization(processor):
    assert processor is not None
    assert hasattr(processor, "process_document")


def test_extract_entities_regex(processor):
    text = (
        "IPC 420 case filed by Vikram Mehta against Pradeep Sharma. "
        "Amount: Rs. 25,00,000. Date: 08-01-2024. "
        "FIR No. 234/2024 at Andheri Police Station."
    )
    entities = processor.extract_entities(text)

    assert "ipc_sections" in entities
    assert "420" in entities["ipc_sections"]
    assert "dates" in entities
    assert len(entities["dates"]) > 0
    assert "case_numbers" in entities


def test_identify_legal_charges(processor):
    text = "The accused is charged under IPC Section 420, 468, and 120B."
    charges = processor.identify_legal_charges(text)

    assert isinstance(charges, list)
    assert len(charges) > 0
    sections = [c["section_number"] for c in charges]
    assert "420" in sections


def test_process_nonexistent_file(processor):
    result = processor.process_document("/nonexistent/path/file.pdf")
    assert result.get("success") is False
    assert "error" in result


def test_extract_text_file(tmp_path, processor):
    test_file = tmp_path / "test.txt"
    test_file.write_text("This is a test legal document with IPC 302 and Section 420.")

    result = processor._extract_text_file(str(test_file))
    assert "text" in result
    assert "IPC 302" in result["text"] or "302" in result["text"]
    assert result["word_count"] > 0


def test_supported_types(processor):
    assert "pdf" in processor.SUPPORTED_TYPES
    assert "jpg" in processor.SUPPORTED_TYPES
    assert "mp3" in processor.SUPPORTED_TYPES
    assert processor.SUPPORTED_TYPES["pdf"] == "pdf"
    assert processor.SUPPORTED_TYPES["jpg"] == "image"
    assert processor.SUPPORTED_TYPES["mp3"] == "audio"
