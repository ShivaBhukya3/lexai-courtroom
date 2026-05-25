"""Core LexAI feature — AI-powered legal argument generation."""

import json
from loguru import logger

from llm.groq_client import GroqClient
from llm.prompt_templates import (
    SYSTEM_LEGAL_ANALYST,
    get_prosecution_prompt,
    get_defense_prompt,
)


ARGUMENT_STYLES = {
    "aggressive": (
        "AGGRESSIVE style: Use strong, assertive language. "
        "Leave no room for doubt. Attack weaknesses in the opposing case directly. "
        "Demand maximum sentence / complete acquittal."
    ),
    "conservative": (
        "CONSERVATIVE style: Measured, precise legal language. "
        "Focus on established precedents and statutes. "
        "Present facts methodically without emotional appeal."
    ),
    "balanced": (
        "BALANCED style: Combine legal precision with compelling narrative. "
        "Acknowledge opposing arguments where necessary. "
        "Focus on key strengths while subtly undermining weaknesses."
    ),
}


class LegalArgumentGenerator:
    """Generate comprehensive prosecution and defense arguments using AI."""

    def __init__(self):
        self._groq = GroqClient()

    def generate_prosecution_argument(
        self,
        case_data: dict,
        evidence_analyses: list,
        legal_context: dict,
        precedents: list,
        style: str = "balanced",
    ) -> dict:
        """Generate full prosecution case structure."""
        logger.info(f"Generating prosecution argument — style: {style}")

        case_summary = self._build_case_summary(case_data)
        evidence_summary = self._build_evidence_summary(evidence_analyses)
        legal_ctx = self._build_legal_context_str(legal_context)
        precedents_str = self._build_precedents_str(precedents)
        style_instruction = ARGUMENT_STYLES.get(style, ARGUMENT_STYLES["balanced"])

        prompt = get_prosecution_prompt(
            case_summary=case_summary,
            evidence_summary=evidence_summary,
            legal_context=legal_ctx,
            precedents=precedents_str,
            style=style_instruction,
        )

        raw = self._groq.complete_json(prompt, system=SYSTEM_LEGAL_ANALYST, max_tokens=4096)
        return self._normalize_prosecution(raw, style)

    def generate_defense_argument(
        self,
        case_data: dict,
        evidence_analyses: list,
        legal_context: dict,
        precedents: list,
        style: str = "balanced",
    ) -> dict:
        """Generate full defense case structure."""
        logger.info(f"Generating defense argument — style: {style}")

        case_summary = self._build_case_summary(case_data)
        evidence_summary = self._build_evidence_summary(evidence_analyses)
        legal_ctx = self._build_legal_context_str(legal_context)
        precedents_str = self._build_precedents_str(precedents)
        style_instruction = ARGUMENT_STYLES.get(style, ARGUMENT_STYLES["balanced"])

        prompt = get_defense_prompt(
            case_summary=case_summary,
            evidence_summary=evidence_summary,
            legal_context=legal_ctx,
            precedents=precedents_str,
            style=style_instruction,
        )

        raw = self._groq.complete_json(prompt, system=SYSTEM_LEGAL_ANALYST, max_tokens=4096)
        return self._normalize_defense(raw, style)

    def generate_cross_examination(
        self, witness_statement: str, case_context: str, side: str = "defense"
    ) -> list[dict]:
        """Generate cross-examination questions for a witness."""
        prompt = (
            f"Generate 15 pointed cross-examination questions for this witness. "
            f"Examining side: {side.upper()}. "
            f"For each question provide: question, purpose, expected_answer, follow_up_if_yes, follow_up_if_no. "
            f"Focus on: exposing contradictions, challenging credibility, controlling narrative.\n\n"
            f"Case Context: {case_context}\n\n"
            f"Witness Statement:\n{witness_statement[:2000]}\n\n"
            f"Return as JSON array."
        )
        raw = self._groq.complete_json(prompt, system=SYSTEM_LEGAL_ANALYST)
        if isinstance(raw, list):
            questions = raw
        else:
            questions = raw.get("questions", raw.get("cross_examination", []))
        if not questions:
            questions = self._fallback_cross_examination_questions(witness_statement, side)
        return questions

    def generate_legal_objections(self, argument_text: str) -> list[dict]:
        """Identify points where legal objections can be raised."""
        prompt = (
            f"Review this legal argument and identify all points where valid legal objections "
            f"can be raised under Indian court procedure. "
            f"Return JSON array with: objection_type, grounds, legal_basis, timing, suggested_wording.\n\n"
            f"Argument:\n{argument_text[:2000]}"
        )
        raw = self._groq.complete_json(prompt, system=SYSTEM_LEGAL_ANALYST)
        if isinstance(raw, list):
            return raw
        return raw.get("objections", [])

    def compare_argument_strength(self, prosecution: dict, defense: dict) -> dict:
        """Score and compare prosecution vs defense arguments."""
        pro_text = json.dumps(prosecution, ensure_ascii=False)[:1500]
        def_text = json.dumps(defense, ensure_ascii=False)[:1500]

        prompt = (
            f"Compare these prosecution and defense arguments for an Indian court case. "
            f"Score each side (0-10) on: evidence_strength, precedent_support, "
            f"logical_coherence, witness_strength, legal_accuracy. "
            f"Then predict likely winner and key battleground issues. "
            f"Return JSON with: prosecution_scores, defense_scores, "
            f"winner_prediction, confidence, key_battlegrounds (list of issues), "
            f"overall_prosecution_score, overall_defense_score.\n\n"
            f"PROSECUTION:\n{pro_text}\n\nDEFENSE:\n{def_text}"
        )
        raw = self._groq.complete_json(prompt, system=SYSTEM_LEGAL_ANALYST)
        return {
            "prosecution_scores": raw.get("prosecution_scores", {"evidence_strength": 7, "precedent_support": 6, "logical_coherence": 7, "witness_strength": 6, "legal_accuracy": 8}),
            "defense_scores": raw.get("defense_scores", {"evidence_strength": 5, "precedent_support": 6, "logical_coherence": 6, "witness_strength": 5, "legal_accuracy": 7}),
            "winner_prediction": raw.get("winner_prediction", "Prosecution"),
            "confidence": float(raw.get("confidence", 0.65)),
            "key_battlegrounds": raw.get("key_battlegrounds", ["Evidence admissibility", "Witness credibility"]),
            "overall_prosecution_score": float(raw.get("overall_prosecution_score", 6.8)),
            "overall_defense_score": float(raw.get("overall_defense_score", 5.8)),
        }

    # ── Internal helpers ──────────────────────────────────────────────────

    def _fallback_cross_examination_questions(self, statement: str, side: str) -> list[dict]:
        """Return template cross-examination questions when LLM is unavailable."""
        # Pull a short excerpt from the statement for contextual framing
        excerpt = statement[:120].replace("\n", " ").strip()
        prefix = "prosecution" if side == "prosecution" else "defense"
        return [
            {"question": f"You stated: '{excerpt}…' — are you absolutely certain that account is accurate?", "purpose": "Challenge statement accuracy", "expected_answer": "Yes, I am certain", "follow_up_if_yes": "Then why does your police statement differ from what you have said today?", "follow_up_if_no": "So the court should treat your testimony with caution?"},
            {"question": "Did you personally witness every event you have described, or are parts of your account based on what others told you?", "purpose": "Distinguish first-hand from hearsay", "expected_answer": "I saw it myself", "follow_up_if_yes": "Can you name any independent person who was present and can confirm your version?", "follow_up_if_no": "You are asking the court to convict on hearsay?"},
            {"question": "How much time passed between the incident and when you filed the complaint?", "purpose": "Challenge promptness and memory", "expected_answer": "A short time", "follow_up_if_yes": "What prevented you from reporting immediately?", "follow_up_if_no": "Memory fades with time — could your recollection be inaccurate?"},
            {"question": "Did you have any personal or financial dispute with the accused before this matter arose?", "purpose": "Expose motive to falsely implicate", "expected_answer": "No", "follow_up_if_yes": "Is it possible this complaint is motivated by that dispute rather than the truth?", "follow_up_if_no": "Then what explains the accused's claim that you have a personal vendetta against them?"},
            {"question": "Have you made any statements to third parties about this case before giving evidence today?", "purpose": "Check for prior inconsistent statements", "expected_answer": "No / minimal", "follow_up_if_yes": "Were those statements recorded? Do they match what you have said today?", "follow_up_if_no": "So no one outside this court has heard your account before now?"},
            {"question": "Can you produce any documentary evidence — receipts, messages, bank records — to corroborate your testimony?", "purpose": "Expose lack of documentary support", "expected_answer": "Yes / No", "follow_up_if_yes": "Were those documents submitted to the investigating officer at the time of the complaint?", "follow_up_if_no": "The court is therefore being asked to rely solely on your unverified word?"},
            {"question": "Is it possible you misunderstood the accused's intentions when the events you described occurred?", "purpose": "Introduce alternative interpretation", "expected_answer": "No", "follow_up_if_yes": "If there is any possibility of misunderstanding, that is reasonable doubt, is it not?", "follow_up_if_no": "Yet you had no prior relationship that would allow you to accurately judge their state of mind?"},
            {"question": "Were you under any pressure — from family, police, or any other party — to file or maintain this complaint?", "purpose": "Expose external influence", "expected_answer": "No", "follow_up_if_yes": "Who applied that pressure and what was their interest in the outcome?", "follow_up_if_no": "You acted entirely of your own free will and stand by every word?"},
            {"question": "Is your memory of specific conversations, dates, and amounts perfectly accurate after all this time?", "purpose": "Test reliability of detail", "expected_answer": "Yes", "follow_up_if_yes": "Then please tell the court the exact words used and the precise date — without hesitation.", "follow_up_if_no": "If your memory on details is uncertain, the entire account must be viewed with caution?"},
            {"question": f"As a {prefix}-side witness, do you stand to benefit in any way from a verdict against the accused?", "purpose": "Expose witness interest in outcome", "expected_answer": "No", "follow_up_if_yes": "That financial or personal interest colours your evidence, does it not?", "follow_up_if_no": "Then you would have no objection to the court scrutinising every detail of your statement?"},
        ]

    def _build_case_summary(self, case_data: dict) -> str:
        meta = case_data.get("metadata", case_data)
        charges = meta.get("charges", [])
        return (
            f"Case ID: {meta.get('case_id', 'UNKNOWN')}\n"
            f"Type: {meta.get('case_type', '')} — {meta.get('sub_type', '')}\n"
            f"Court: {meta.get('court', '')}\n"
            f"Charges: {', '.join(charges) if charges else 'Not specified'}\n"
            f"Status: {meta.get('status', '')}"
        )

    def _build_evidence_summary(self, analyses: list) -> str:
        if not analyses:
            return "No evidence analyzed yet."
        parts = []
        for i, a in enumerate(analyses[:10], 1):
            strength = a.get("evidence_strength", a.get("evidence_strength_score", "N/A"))
            parts.append(
                f"{i}. [{a.get('doc_type', a.get('type', 'Unknown')).upper()}] "
                f"{a.get('file_name', f'Evidence {i}')} — "
                f"Strength: {strength}/10 — "
                f"{str(a.get('summary', a.get('description', '')))[:200]}"
            )
        return "\n".join(parts)

    def _build_legal_context_str(self, context: dict) -> str:
        if not context:
            return "Legal context not yet retrieved."
        sections = context.get("applicable_sections", [])
        precedents = context.get("relevant_precedents", [])
        parts = []
        if sections:
            parts.append("Applicable Sections: " + ", ".join(
                s.get("section", "") for s in sections[:5]
            ))
        if precedents:
            parts.append("Key Precedents: " + "; ".join(
                p.get("case_name", "") for p in precedents[:3]
            ))
        return "\n".join(parts) or "Standard Indian criminal/civil procedure applies."

    def _build_precedents_str(self, precedents: list) -> str:
        if not precedents:
            return "No precedents retrieved."
        parts = []
        for p in precedents[:5]:
            parts.append(
                f"- {p.get('case_name', '')} [{p.get('citation', '')}]: "
                f"{p.get('legal_principle', p.get('held', ''))[:200]}"
            )
        return "\n".join(parts)

    def _normalize_prosecution(self, raw: dict, style: str) -> dict:
        return {
            "side": "prosecution",
            "style": style,
            "opening_statement": raw.get("opening_statement", raw.get("OPENING_STATEMENT",
                "The prosecution will prove beyond reasonable doubt that the accused is guilty of all charges.")),
            "charge_arguments": raw.get("charge_arguments", raw.get("CHARGE_ARGUMENTS", [])),
            "evidence_sequence": raw.get("evidence_sequence", raw.get("EVIDENCE_SEQUENCE", [])),
            "anticipated_defense": raw.get("anticipated_defense", raw.get("ANTICIPATED_DEFENSE", [])),
            "rebuttals": raw.get("rebuttals", raw.get("REBUTTALS", [])),
            "closing_statement": raw.get("closing_statement", raw.get("CLOSING_STATEMENT",
                "The evidence is clear and unambiguous. We urge the court to convict.")),
            "sentencing_recommendation": raw.get("sentencing_recommendation", raw.get("SENTENCING_RECOMMENDATION", "")),
            "cited_precedents": raw.get("cited_precedents", raw.get("CITED_PRECEDENTS", [])),
            "argument_strength_score": float(raw.get("argument_strength_score", 6.5)),
        }

    def _normalize_defense(self, raw: dict, style: str) -> dict:
        return {
            "side": "defense",
            "style": style,
            "opening_statement": raw.get("opening_statement", raw.get("OPENING_STATEMENT",
                "The defense will demonstrate that the prosecution has failed to prove its case beyond reasonable doubt.")),
            "charge_counter_arguments": raw.get("charge_counter_arguments", raw.get("CHARGE_COUNTER_ARGUMENTS", [])),
            "cross_examination": raw.get("cross_examination", raw.get("CROSS_EXAMINATION", [])),
            "defense_witnesses": raw.get("defense_witnesses", raw.get("DEFENSE_WITNESSES", [])),
            "evidence_challenges": raw.get("evidence_challenges", raw.get("EVIDENCE_CHALLENGES", [])),
            "closing_statement": raw.get("closing_statement", raw.get("CLOSING_STATEMENT",
                "Reasonable doubt exists on every charge. The accused deserves complete acquittal.")),
            "acquittal_grounds": raw.get("acquittal_grounds", raw.get("ACQUITTAL_GROUNDS", [])),
            "bail_application": raw.get("bail_application", raw.get("BAIL_APPLICATION", "")),
            "cited_precedents": raw.get("cited_precedents", raw.get("CITED_PRECEDENTS", [])),
            "argument_strength_score": float(raw.get("argument_strength_score", 5.5)),
        }
