"""Case summarizer — executive summaries, fact sheets, risk assessments."""

from loguru import logger
from llm.groq_client import GroqClient
from llm.prompt_templates import SYSTEM_LEGAL_ANALYST


class CaseSummarizer:
    """Generate professional case summaries and risk assessments."""

    def __init__(self):
        self._groq = GroqClient()

    def generate_executive_summary(self, case_data: dict) -> str:
        """Generate a 1-page executive summary for senior advocates."""
        meta = case_data.get("metadata", case_data)
        prompt = (
            f"Create a concise executive summary of this Indian court case for a senior advocate.\n\n"
            f"Case: {meta.get('case_id', 'UNKNOWN')} | {meta.get('case_type', '')} | {meta.get('court', '')}\n"
            f"Plaintiff/Complainant: {_format_party(meta.get('plaintiff', meta.get('complainant', {})))}\n"
            f"Defendant/Accused: {_format_party(meta.get('defendant', meta.get('accused', {})))}\n"
            f"Charges: {', '.join(meta.get('charges', []))}\n"
            f"Status: {meta.get('status', '')}\n"
            f"Key Facts: {'; '.join(meta.get('key_facts', []))}\n\n"
            f"Include: Case overview, key parties, core legal issues, current status, "
            f"critical deadlines, recommended next steps, risk level (High/Medium/Low). "
            f"Professional tone. Under 400 words."
        )
        return self._groq.complete(prompt, system=SYSTEM_LEGAL_ANALYST, max_tokens=700)

    def generate_fact_sheet(self, case_data: dict) -> dict:
        """Generate a structured fact sheet."""
        meta = case_data.get("metadata", case_data)
        return {
            "case_number": meta.get("case_id", meta.get("fir_number", "N/A")),
            "court": meta.get("court", "N/A"),
            "case_type": f"{meta.get('case_type', '')} — {meta.get('sub_type', '')}",
            "parties": {
                "plaintiff_complainant": _format_party(meta.get("plaintiff", meta.get("complainant", {}))),
                "defendant_accused": _format_party(meta.get("defendant", meta.get("accused", {}))),
            },
            "charges": meta.get("charges", []),
            "key_dates": {
                "filing_date": meta.get("filing_date", "N/A"),
                "next_hearing": meta.get("next_hearing", "N/A"),
                "hearing_dates": meta.get("hearing_dates", []),
            },
            "evidence_summary": meta.get("evidence", meta.get("documents", [])),
            "witnesses": meta.get("witnesses", []),
            "current_status": meta.get("status", "N/A"),
            "applicable_law": meta.get("applicable_law", []),
            "key_facts": meta.get("key_facts", []),
        }

    def generate_chronological_timeline(self, case_data: dict) -> list[dict]:
        """Build a chronological timeline of all case events."""
        meta = case_data.get("metadata", case_data)
        events = []

        def add_event(date: str, event: str, doc: str, impact: str, significance: str = "Medium"):
            if date and date != "N/A":
                events.append({
                    "date": date,
                    "event": event,
                    "document_source": doc,
                    "legal_impact": impact,
                    "significance": significance,
                })

        # Filing
        add_event(
            meta.get("filing_date", meta.get("arrest_date", "")),
            f"Case filed — {meta.get('case_type', 'Case')} registered",
            "FIR/Complaint",
            "Initiates legal proceedings",
            "High",
        )

        # Arrest
        if meta.get("arrest_date"):
            add_event(meta["arrest_date"], "Accused arrested", "Arrest warrant", "Liberty curtailed", "High")

        # Chargesheet
        if meta.get("chargesheet_date"):
            add_event(meta["chargesheet_date"], "Chargesheet filed", "Police chargesheet", "Formal charges framed", "High")

        # Hearing dates
        for i, date in enumerate(meta.get("hearing_dates", []), 1):
            add_event(date, f"Hearing No. {i}", "Court order", "Case progression", "Medium")

        # Next hearing
        if meta.get("next_hearing"):
            add_event(meta["next_hearing"], "Next scheduled hearing", "Court calendar", "Upcoming proceedings", "Medium")

        # Document-specific dates
        for doc in meta.get("documents", []):
            if doc.get("date"):
                add_event(doc["date"], f"Document: {doc.get('name', 'Unknown')}", doc.get("type", "Document"), "Evidence on record", "Low")

        # Sort by date
        events.sort(key=lambda x: x["date"])
        return events

    def identify_legal_issues(self, case_data: dict) -> list[dict]:
        """Identify key legal questions to be decided."""
        meta = case_data.get("metadata", case_data)
        charges = meta.get("charges", [])
        key_facts = meta.get("key_facts", [])

        prompt = (
            f"Identify the 5 key legal issues/questions to be decided in this Indian court case.\n"
            f"Charges: {', '.join(charges)}\n"
            f"Key Facts: {'; '.join(key_facts)}\n\n"
            f"For each issue return JSON array with: "
            f"issue, relevant_law, prosecution_position, defense_position, complexity (High/Medium/Low)."
        )
        raw = self._groq.complete_json(prompt, system=SYSTEM_LEGAL_ANALYST)
        if isinstance(raw, list):
            return raw
        return raw.get("legal_issues", raw.get("issues", [
            {
                "issue": f"Whether the accused is guilty under {charges[0] if charges else 'the charged sections'}",
                "relevant_law": charges[0] if charges else "IPC",
                "prosecution_position": "Accused is guilty beyond reasonable doubt",
                "defense_position": "Prosecution has not discharged burden of proof",
                "complexity": "High",
            }
        ]))

    def generate_risk_assessment(self, case_data: dict, client_side: str = "defense") -> dict:
        """Generate risk analysis for client — prosecution or defense side."""
        meta = case_data.get("metadata", case_data)
        charges = meta.get("charges", [])

        prompt = (
            f"Perform a legal risk assessment for the {client_side.upper()} side.\n"
            f"Case: {meta.get('case_type', '')} — {', '.join(charges)}\n"
            f"Key Facts: {'; '.join(meta.get('key_facts', []))}\n\n"
            f"Return JSON with: overall_risk (High/Medium/Low), conviction_probability (0-1), "
            f"key_risks (list), mitigation_strategies (list), evidence_risks (list), "
            f"procedural_risks (list), estimated_duration, financial_exposure, reputation_risk."
        )
        raw = self._groq.complete_json(prompt, system=SYSTEM_LEGAL_ANALYST)

        return {
            "overall_risk": raw.get("overall_risk", "Medium"),
            "conviction_probability": float(raw.get("conviction_probability", 0.5)),
            "key_risks": raw.get("key_risks", ["Evidence against client", "Witness testimony"]),
            "mitigation_strategies": raw.get("mitigation_strategies", ["Challenge evidence", "Build alibi"]),
            "evidence_risks": raw.get("evidence_risks", []),
            "procedural_risks": raw.get("procedural_risks", []),
            "estimated_duration": raw.get("estimated_duration", "12-24 months"),
            "financial_exposure": raw.get("financial_exposure", "Depends on charges"),
            "reputation_risk": raw.get("reputation_risk", "Moderate"),
            "client_side": client_side,
        }


def _format_party(party: dict) -> str:
    if not party:
        return "N/A"
    parts = [party.get("name", "Unknown")]
    if party.get("age"):
        parts.append(f"Age: {party['age']}")
    if party.get("occupation"):
        parts.append(party["occupation"])
    return ", ".join(parts)
