"""Parse and validate LLM responses for structured outputs."""

import json
import re
from typing import Any
from loguru import logger


def extract_json(text: str) -> dict:
    """Extract JSON from LLM response, handling markdown fences."""
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:])
        text = text.rsplit("```", 1)[0].strip()

    # Try direct parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Try to find JSON object in the text
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    logger.warning("Could not extract JSON from LLM response")
    return {"raw_text": text, "parse_error": True}


def extract_numbered_list(text: str) -> list[str]:
    """Extract a numbered list from LLM response."""
    lines = text.strip().split("\n")
    items = []
    for line in lines:
        line = line.strip()
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", line)
        if cleaned:
            items.append(cleaned)
    return items


def extract_score(text: str, default: float = 5.0) -> float:
    """Extract a numeric score (0-10) from text."""
    matches = re.findall(r"\b([0-9](?:\.[0-9])?|10(?:\.0)?)\b", text)
    if matches:
        try:
            return float(matches[0])
        except ValueError:
            pass
    return default


def parse_argument_response(raw: dict) -> dict:
    """Normalize argument generation response."""
    return {
        "opening_statement": raw.get("opening_statement", raw.get("OPENING_STATEMENT", "")),
        "charge_arguments": raw.get("charge_arguments", raw.get("CHARGE_ARGUMENTS", [])),
        "evidence_sequence": raw.get("evidence_sequence", raw.get("EVIDENCE_SEQUENCE", [])),
        "rebuttals": raw.get("rebuttals", raw.get("REBUTTALS", [])),
        "closing_statement": raw.get("closing_statement", raw.get("CLOSING_STATEMENT", "")),
        "cited_precedents": raw.get("cited_precedents", raw.get("CITED_PRECEDENTS", [])),
        "argument_strength_score": float(raw.get("argument_strength_score", 6.5)),
        "sentencing_recommendation": raw.get("sentencing_recommendation", raw.get("SENTENCING_RECOMMENDATION", "")),
    }


def parse_verdict_explanation(raw: str) -> dict:
    """Parse verdict prediction explanation text."""
    sections = {
        "primary_factors": [],
        "prosecution_strengths": [],
        "defense_strengths": [],
        "uncertainty_factors": [],
        "change_factors": [],
    }

    current = None
    key_map = {
        "PRIMARY FACTORS": "primary_factors",
        "PROSECUTION": "prosecution_strengths",
        "DEFENSE": "defense_strengths",
        "UNCERTAINTY": "uncertainty_factors",
        "CHANGE": "change_factors",
    }

    for line in raw.split("\n"):
        line = line.strip()
        for key, field in key_map.items():
            if key in line.upper():
                current = field
                break
        else:
            if current and line and not line.startswith("#"):
                cleaned = re.sub(r"^[-•*]\s*", "", line)
                if cleaned:
                    sections[current].append(cleaned)

    return sections
