"""Build contextual prompts from retrieved legal documents."""

from loguru import logger


class ContextBuilder:
    """Assemble retrieved chunks into LLM-ready context strings."""

    def build_argument_context(
        self,
        sections: list[dict],
        precedents: list[dict],
        max_length: int = 3000,
    ) -> str:
        """Build context string for argument generation."""
        parts = []
        current_len = 0

        if sections:
            parts.append("=== APPLICABLE LEGAL SECTIONS ===")
            for s in sections:
                chunk = f"\n{s['section']} — {s['title']}\n{s['description'][:300]}\nPunishment: {s.get('punishment', 'N/A')}"
                if current_len + len(chunk) > max_length:
                    break
                parts.append(chunk)
                current_len += len(chunk)

        if precedents:
            parts.append("\n=== RELEVANT PRECEDENTS ===")
            for p in precedents:
                chunk = f"\n{p['case_name']} [{p.get('citation', '')}]\nPrinciple: {p.get('legal_principle', '')[:300]}"
                if current_len + len(chunk) > max_length:
                    break
                parts.append(chunk)
                current_len += len(chunk)

        return "\n".join(parts)

    def build_research_context(self, results: list[dict], max_length: int = 2000) -> str:
        """Build context for legal research queries."""
        parts = []
        current_len = 0

        for r in results:
            text = r.get("_text", "")
            if current_len + len(text) > max_length:
                text = text[:max_length - current_len]

            parts.append(f"[Source: {r.get('_source', 'legal_db')} | Score: {r.get('relevance_score', 0):.2f}]")
            parts.append(text)
            current_len += len(text)

            if current_len >= max_length:
                break

        return "\n\n".join(parts)

    def build_case_context(self, case_data: dict) -> str:
        """Build case summary context string."""
        meta = case_data.get("metadata", case_data)
        return (
            f"Case: {meta.get('case_id', 'UNKNOWN')} | "
            f"Type: {meta.get('case_type', '')} | "
            f"Court: {meta.get('court', '')} | "
            f"Charges: {', '.join(meta.get('charges', []))} | "
            f"Status: {meta.get('status', '')}"
        )
