"""Legal RAG retriever — search precedents, sections, and legal context."""

from loguru import logger
from rag.vector_store import LegalVectorStore
from llm.groq_client import GroqClient
from llm.prompt_templates import SYSTEM_LEGAL_ANALYST


class LegalRAGRetriever:
    """Retrieve relevant legal documents using RAG pipeline."""

    def __init__(self):
        self._store = LegalVectorStore()
        self._groq = GroqClient()
        self._ensure_index()

    def _ensure_index(self) -> None:
        if not self._store.is_built():
            logger.info("Building legal index for first time...")
            self._store.build_index()

    def build_legal_index(self) -> None:
        """(Re)build the FAISS legal index."""
        self._store.build_index()

    def search_precedents(self, query: str, top_k: int = 8) -> list[dict]:
        """Find most relevant case precedents."""
        results = self._store.search(query, top_k=top_k * 2)
        precedents = [
            r for r in results
            if r.get("_source") in ("case_precedents", "supreme_court_judgments", "high_court_judgments")
        ][:top_k]

        return [
            {
                "case_name": r.get("case_name", "Unknown"),
                "citation": r.get("citation", "N/A"),
                "court": r.get("court", "N/A"),
                "year": r.get("year"),
                "held": r.get("held", r.get("key_ratio", "")),
                "legal_principle": r.get("legal_principle", ""),
                "relevant_sections": r.get("relevant_sections", []),
                "relevance_score": round(r.get("relevance_score", 0), 4),
                "summary": r.get("summary", r.get("facts", ""))[:300],
            }
            for r in precedents
        ]

    def search_legal_sections(self, query: str, top_k: int = 5) -> list[dict]:
        """Find applicable IPC/CrPC sections."""
        results = self._store.search(query, top_k=top_k * 3)
        sections = [
            r for r in results
            if r.get("_source") in ("ipc_sections", "crpc_sections")
        ][:top_k]

        return [
            {
                "section": r.get("section", "Unknown"),
                "title": r.get("title", ""),
                "description": r.get("description", ""),
                "punishment": r.get("punishment", "N/A"),
                "bailable": r.get("bailable"),
                "cognizable": r.get("cognizable"),
                "keywords": r.get("keywords", []),
                "relevance_score": round(r.get("relevance_score", 0), 4),
                "source": r.get("_source", ""),
            }
            for r in sections
        ]

    def get_legal_context(self, case_summary: str) -> dict:
        """Get comprehensive legal context for a case."""
        applicable_sections = self.search_legal_sections(case_summary, top_k=5)
        relevant_precedents = self.search_precedents(case_summary, top_k=8)

        # Generate sentencing guidelines via LLM
        sections_text = ", ".join(s["section"] for s in applicable_sections)
        prompt = (
            f"For an Indian court case involving {sections_text}, provide: "
            f"1) typical sentencing range, 2) bail eligibility, 3) key legal tests to apply. "
            f"Keep it concise and cite sections."
        )
        sentencing = self._groq.complete(prompt, system=SYSTEM_LEGAL_ANALYST, max_tokens=500)

        return {
            "applicable_sections": applicable_sections,
            "relevant_precedents": relevant_precedents,
            "sentencing_guidelines": sentencing,
            "similar_case_outcomes": relevant_precedents[:3],
        }

    def find_similar_cases(self, case_facts: str, top_k: int = 5) -> list[dict]:
        """Find cases most similar to the current case."""
        return self.search_precedents(case_facts, top_k=top_k)

    def get_defense_precedents(self, charges: list[str]) -> list[dict]:
        """Find precedents favorable to defense."""
        query = f"acquittal bail defense {' '.join(charges)} insufficient evidence reasonable doubt"
        return self.search_precedents(query, top_k=6)

    def get_prosecution_precedents(self, charges: list[str]) -> list[dict]:
        """Find precedents favorable to prosecution."""
        query = f"conviction sentence {' '.join(charges)} guilty evidence established"
        return self.search_precedents(query, top_k=6)

    def ask_legal_question(self, question: str, case_context: str = "") -> str:
        """Answer a legal question using RAG context."""
        # Retrieve relevant context
        sections = self.search_legal_sections(question, top_k=3)
        precedents = self.search_precedents(question, top_k=4)

        context_parts = []
        if sections:
            context_parts.append("RELEVANT SECTIONS:\n" + "\n".join(
                f"- {s['section']}: {s['title']} — {s['description'][:200]}" for s in sections
            ))
        if precedents:
            context_parts.append("RELEVANT PRECEDENTS:\n" + "\n".join(
                f"- {p['case_name']} [{p['citation']}]: {p['legal_principle'][:200]}" for p in precedents
            ))

        context = "\n\n".join(context_parts) or "No specific context found in database."

        prompt = (
            f"Answer this Indian legal question using the provided context.\n\n"
            f"QUESTION: {question}\n\n"
            f"CASE CONTEXT: {case_context or 'General query'}\n\n"
            f"LEGAL DATABASE CONTEXT:\n{context}\n\n"
            f"Provide: direct answer, legal basis, caveats, practical implications."
        )
        return self._groq.complete(prompt, system=SYSTEM_LEGAL_ANALYST, max_tokens=1000)
