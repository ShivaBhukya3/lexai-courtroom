"""Prompt templates for LexAI LLM interactions."""

from string import Template
from pathlib import Path
import yaml

_PROMPTS_PATH = Path(__file__).parent.parent / "config" / "prompts.yaml"

def _load_prompts() -> dict:
    try:
        with open(_PROMPTS_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        return {}

PROMPTS = _load_prompts()


def get_prosecution_prompt(
    case_summary: str,
    evidence_summary: str,
    legal_context: str,
    precedents: str,
    style: str = "balanced",
) -> str:
    template = PROMPTS.get("argument_generation", {}).get("prosecution", "")
    return Template(template).safe_substitute(
        case_summary=case_summary,
        evidence_summary=evidence_summary,
        legal_context=legal_context,
        precedents=precedents,
        style=style,
    )


def get_defense_prompt(
    case_summary: str,
    evidence_summary: str,
    legal_context: str,
    precedents: str,
    style: str = "balanced",
) -> str:
    template = PROMPTS.get("argument_generation", {}).get("defense", "")
    return Template(template).safe_substitute(
        case_summary=case_summary,
        evidence_summary=evidence_summary,
        legal_context=legal_context,
        precedents=precedents,
        style=style,
    )


def get_image_analysis_prompt(case_context: str) -> str:
    template = PROMPTS.get("evidence_analysis", {}).get("image_analysis", "")
    return Template(template).safe_substitute(case_context=case_context)


def get_testimony_analysis_prompt(transcript: str, case_context: str) -> str:
    template = PROMPTS.get("testimony_analysis", {}).get("content_analysis", "")
    return Template(template).safe_substitute(
        transcript=transcript, case_context=case_context
    )


def get_legal_answer_prompt(question: str, context: str, case_context: str) -> str:
    template = PROMPTS.get("legal_research", {}).get("answer", "")
    return Template(template).safe_substitute(
        question=question, context=context, case_context=case_context
    )


SYSTEM_LEGAL_ANALYST = (
    "You are an expert Indian legal analyst with 25+ years of experience across "
    "criminal, civil, and constitutional law. You have appeared before the Supreme "
    "Court of India and multiple High Courts. Provide precise, legally accurate "
    "analysis citing specific IPC/CrPC sections and case precedents."
)

SYSTEM_DOCUMENT_ANALYST = (
    "You are an expert Indian legal document analyst. Extract all legally relevant "
    "information from documents with precision — parties, charges, dates, amounts, "
    "applicable sections, and key facts. Return structured JSON."
)

SYSTEM_FORENSIC_ANALYST = (
    "You are a forensic evidence analyst and legal expert specializing in evidence "
    "evaluation for Indian courts. Analyze evidence objectively, noting both facts "
    "and inferences. Assess evidentiary value and chain of custody."
)
