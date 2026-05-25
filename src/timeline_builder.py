"""Build chronological case timelines from documents and metadata."""

import re
from datetime import datetime
from pathlib import Path
from loguru import logger

from llm.groq_client import GroqClient
from llm.prompt_templates import SYSTEM_LEGAL_ANALYST

DATE_RE = re.compile(
    r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b|"
    r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[\.,]?\s+\d{4})\b",
    re.IGNORECASE,
)


class TimelineBuilder:
    """Extract and organize case events into chronological timeline."""

    def __init__(self):
        self._groq = GroqClient()

    def build_from_case_data(self, case_data: dict, documents: list[dict]) -> list[dict]:
        """Build full timeline from metadata + extracted document dates."""
        events = []

        # From metadata
        meta = case_data.get("metadata", case_data)
        events.extend(self._extract_metadata_events(meta))

        # From documents
        for doc in documents:
            events.extend(self._extract_document_events(doc))

        # Sort and deduplicate
        seen = set()
        unique_events = []
        for e in events:
            key = (e.get("date", ""), e.get("event", "")[:30])
            if key not in seen:
                seen.add(key)
                unique_events.append(e)

        unique_events.sort(key=lambda x: self._parse_date(x.get("date", "")))
        for i, e in enumerate(unique_events):
            e["sequence"] = i + 1

        return unique_events

    def extract_dates_from_text(self, text: str, source: str = "Document") -> list[dict]:
        """Extract all dates from document text with context."""
        events = []
        for match in DATE_RE.finditer(text):
            date_str = match.group(1) or match.group(2)
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context = text[start:end].strip()

            events.append({
                "date": date_str,
                "event": context[:150],
                "document_source": source,
                "legal_impact": "Recorded in document",
                "significance": "Low",
                "extracted": True,
            })
        return events[:20]

    def _extract_metadata_events(self, meta: dict) -> list[dict]:
        events = []
        field_map = {
            "filing_date": ("Case filed / FIR registered", "Initiates legal proceedings", "High"),
            "arrest_date": ("Accused arrested", "Liberty curtailed — custody begins", "High"),
            "chargesheet_date": ("Chargesheet filed by police", "Formal charges framed for trial", "High"),
            "next_hearing": ("Next scheduled hearing", "Upcoming court date", "Medium"),
        }
        for field, (event_name, impact, sig) in field_map.items():
            date = meta.get(field, "")
            if date and date != "N/A":
                events.append({
                    "date": date,
                    "event": event_name,
                    "document_source": "Case Metadata",
                    "legal_impact": impact,
                    "significance": sig,
                })

        for i, date in enumerate(meta.get("hearing_dates", []), 1):
            events.append({
                "date": date,
                "event": f"Court Hearing #{i}",
                "document_source": "Court Records",
                "legal_impact": "Case arguments heard",
                "significance": "Medium",
            })

        for doc in meta.get("documents", []):
            if doc.get("date"):
                events.append({
                    "date": doc["date"],
                    "event": f"Document: {doc.get('name', 'Unknown')}",
                    "document_source": doc.get("type", "Document"),
                    "legal_impact": "Evidence on record",
                    "significance": "Low",
                })

        return events

    def _extract_document_events(self, doc: dict) -> list[dict]:
        events = []
        text = doc.get("text", "")
        if text:
            events.extend(self.extract_dates_from_text(text, doc.get("file_name", "Document")))
        return events

    def _parse_date(self, date_str: str) -> str:
        """Normalize date string for sorting."""
        if not date_str:
            return "9999-12-31"
        for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d", "%d %B %Y", "%d %b %Y"):
            try:
                return datetime.strptime(date_str.strip(), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
        return date_str
