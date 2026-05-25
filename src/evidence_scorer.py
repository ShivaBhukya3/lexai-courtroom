"""Evidence strength scorer and evidence matrix builder."""

from loguru import logger
from llm.groq_client import GroqClient
from llm.prompt_templates import SYSTEM_LEGAL_ANALYST


class EvidenceScorer:
    """Score evidence strength and build evidence-charge matrices."""

    def __init__(self):
        self._groq = GroqClient()

    def score_evidence_item(self, evidence: dict, charges: list[str]) -> dict:
        """Score a single evidence item against all charges."""
        prompt = (
            f"Score this evidence item for an Indian court case.\n"
            f"Evidence: {evidence.get('file_name', 'Unknown')} — {evidence.get('summary', evidence.get('description', ''))[:300]}\n"
            f"Charges: {', '.join(charges)}\n\n"
            f"Return JSON with: overall_strength (1-10), relevance_score (1-10), "
            f"reliability_score (1-10), charge_relevance (dict mapping each charge to: "
            f"supports/neutral/contradicts and score), admissibility_concerns (list)."
        )
        raw = self._groq.complete_json(prompt, system=SYSTEM_LEGAL_ANALYST)
        return {
            "evidence_id": evidence.get("file_name", "unknown"),
            "overall_strength": float(raw.get("overall_strength", 5)),
            "relevance_score": float(raw.get("relevance_score", 5)),
            "reliability_score": float(raw.get("reliability_score", 5)),
            "charge_relevance": raw.get("charge_relevance", {}),
            "admissibility_concerns": raw.get("admissibility_concerns", []),
        }

    def build_evidence_matrix(self, evidence_list: list[dict], charges: list[str]) -> dict:
        """Build evidence vs charges matrix."""
        matrix = {ev.get("file_name", f"Evidence {i+1}"): {} for i, ev in enumerate(evidence_list)}
        for ev in evidence_list:
            name = ev.get("file_name", "unknown")
            for charge in charges:
                score = ev.get("evidence_strength", ev.get("evidence_strength_avg", 5))
                matrix[name][charge] = {
                    "status": "Supports" if score >= 6 else "Neutral" if score >= 4 else "Contradicts",
                    "score": score,
                }
        return matrix

    def calculate_aggregate_strength(self, evidence_list: list[dict]) -> dict:
        """Calculate aggregate evidence strength metrics."""
        if not evidence_list:
            return {"avg_strength": 0, "max_strength": 0, "total_items": 0}

        strengths = [
            float(e.get("evidence_strength", e.get("evidence_strength_score", 5)))
            for e in evidence_list
        ]
        return {
            "avg_strength": round(sum(strengths) / len(strengths), 2),
            "max_strength": max(strengths),
            "min_strength": min(strengths),
            "total_items": len(evidence_list),
            "strong_count": sum(1 for s in strengths if s >= 7),
            "weak_count": sum(1 for s in strengths if s < 4),
        }
