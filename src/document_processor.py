"""Multimodal document processor — PDF, DOCX, images, audio."""

import re
import json
from pathlib import Path
from typing import Any
from loguru import logger

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

try:
    import spacy
    _nlp = None
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    _nlp = None

from llm.groq_client import GroqClient
from llm.vision_client import VisionClient
from llm.prompt_templates import SYSTEM_DOCUMENT_ANALYST


IPC_PATTERN = re.compile(r"\b(?:IPC\s*)?[Ss]ection[s]?\s*(\d{2,3}[A-Z]?)\b|"
                          r"\bIPC\s+(\d{2,3}[A-Z]?)\b|"
                          r"\b(\d{2,3}[A-Z]?)\s+IPC\b", re.IGNORECASE)

DATE_PATTERN = re.compile(
    r"\b(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})\b|"
    r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b",
    re.IGNORECASE
)

MONEY_PATTERN = re.compile(
    r"(?:Rs\.?|₹|INR)\s*[\d,]+(?:\.\d{2})?(?:\s*(?:lakhs?|crores?|thousands?))?|"
    r"[\d,]+\s*(?:lakhs?|crores?)\s*(?:rupees?)?",
    re.IGNORECASE
)

CASE_NUM_PATTERN = re.compile(
    r"\b(?:FIR\s*No\.?|Case\s*No\.?|Suit\s*No\.?|C\.S\.)\s*[\d/]+(?:/\d{4})?",
    re.IGNORECASE
)


def _get_nlp():
    global _nlp
    if _nlp is None and SPACY_AVAILABLE:
        try:
            _nlp = spacy.load("en_core_web_sm")
        except OSError:
            logger.warning("spaCy model not found. Run: python -m spacy download en_core_web_sm")
    return _nlp


class MultimodalDocumentProcessor:
    """Process legal documents of any type — PDF, DOCX, images, audio."""

    SUPPORTED_TYPES = {
        "pdf": "pdf",
        "docx": "docx",
        "doc": "docx",
        "txt": "text",
        "jpg": "image",
        "jpeg": "image",
        "png": "image",
        "bmp": "image",
        "mp3": "audio",
        "mp4": "audio",
        "wav": "audio",
        "m4a": "audio",
        "ogg": "audio",
    }

    def __init__(self):
        self._groq = GroqClient()
        self._vision = VisionClient()

    def process_document(self, file_path: str) -> dict:
        """Auto-detect file type and route to appropriate processor."""
        path = Path(file_path)
        if not path.exists():
            return {"error": f"File not found: {file_path}", "success": False}

        ext = path.suffix.lower().lstrip(".")
        doc_type = self.SUPPORTED_TYPES.get(ext, "unknown")

        logger.info(f"Processing {doc_type}: {path.name}")

        processors = {
            "pdf": self.extract_pdf,
            "docx": self.extract_docx,
            "text": self._extract_text_file,
            "image": self.extract_image_text,
            "audio": self.extract_audio,
        }

        if doc_type not in processors:
            return {"error": f"Unsupported file type: {ext}", "success": False}

        result = processors[doc_type](file_path)
        result["file_name"] = path.name
        result["file_path"] = str(path)
        result["doc_type"] = doc_type
        result["success"] = True

        if result.get("text"):
            result["entities"] = self.extract_entities(result["text"])
            result["legal_charges"] = self.identify_legal_charges(result["text"])
            result["summary"] = self.get_document_summary(result["text"])

        return result

    def extract_pdf(self, file_path: str) -> dict:
        """Extract text from PDF using PyMuPDF."""
        if not PYMUPDF_AVAILABLE:
            return self._pdf_fallback(file_path)

        try:
            doc = fitz.open(file_path)
            pages_text = []
            full_text = []

            for page_num, page in enumerate(doc):
                text = page.get_text("text")
                pages_text.append({"page": page_num + 1, "text": text})
                full_text.append(text)

            combined = "\n\n".join(full_text)
            doc.close()

            return {
                "text": combined,
                "page_count": len(pages_text),
                "word_count": len(combined.split()),
                "language": "en",
                "pages": pages_text,
                "raw_dates": DATE_PATTERN.findall(combined),
                "raw_amounts": MONEY_PATTERN.findall(combined),
                "case_numbers": CASE_NUM_PATTERN.findall(combined),
            }
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return {"text": "", "error": str(e), "page_count": 0}

    def _pdf_fallback(self, file_path: str) -> dict:
        """Fallback PDF reader using basic text extraction."""
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            text = content.decode("utf-8", errors="ignore")
            text = re.sub(r"[^\x20-\x7E\n]", " ", text)
            return {"text": text[:5000], "word_count": len(text.split()), "page_count": 1, "note": "PyMuPDF not available — basic extraction"}
        except Exception as e:
            return {"text": "", "error": str(e)}

    def extract_docx(self, file_path: str) -> dict:
        """Extract text from DOCX file."""
        if not DOCX_AVAILABLE:
            return {"text": "python-docx not installed.", "word_count": 0}

        try:
            doc = DocxDocument(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            combined = "\n\n".join(paragraphs)
            return {
                "text": combined,
                "word_count": len(combined.split()),
                "paragraph_count": len(paragraphs),
                "language": "en",
            }
        except Exception as e:
            logger.error(f"DOCX extraction error: {e}")
            return {"text": "", "error": str(e)}

    def _extract_text_file(self, file_path: str) -> dict:
        """Extract text from plain text file."""
        try:
            text = Path(file_path).read_text(encoding="utf-8", errors="ignore")
            return {"text": text, "word_count": len(text.split()), "language": "en"}
        except Exception as e:
            return {"text": "", "error": str(e)}

    def extract_image_text(self, file_path: str) -> dict:
        """Extract text from image via OCR + GPT-4V analysis."""
        result = {"text": "", "ocr_text": "", "vision_analysis": {}}

        # OCR extraction
        if OCR_AVAILABLE:
            try:
                img = Image.open(file_path)
                ocr_text = pytesseract.image_to_string(img)
                result["ocr_text"] = ocr_text.strip()
                result["text"] = ocr_text.strip()
            except Exception as e:
                logger.warning(f"OCR failed: {e}")

        # GPT-4V analysis
        vision_prompt = (
            "Analyze this legal evidence image. Describe: 1) What is shown, "
            "2) Any text visible, 3) Legal relevance, 4) Evidence strength (1-10), "
            "5) Key observations. Return as JSON."
        )
        vision_result = self._vision.analyze_image_json(file_path, vision_prompt)
        result["vision_analysis"] = vision_result

        if not result["text"] and vision_result.get("description"):
            result["text"] = vision_result["description"]

        result["word_count"] = len(result["text"].split())
        return result

    def extract_audio(self, file_path: str) -> dict:
        """Transcribe audio using Whisper."""
        try:
            import whisper
            model = whisper.load_model("base")
            transcription = model.transcribe(file_path)
            text = transcription.get("text", "")
            segments = transcription.get("segments", [])
            return {
                "text": text,
                "transcript": text,
                "duration_seconds": segments[-1]["end"] if segments else 0,
                "language": transcription.get("language", "en"),
                "word_count": len(text.split()),
                "segments": [{"start": s["start"], "end": s["end"], "text": s["text"]} for s in segments],
                "confidence_score": 0.85,
            }
        except ImportError:
            logger.warning("openai-whisper not installed — audio transcription unavailable")
            return {
                "text": f"[Audio file: {Path(file_path).name}. Install openai-whisper for transcription.]",
                "transcript": "",
                "duration_seconds": 0,
                "language": "en",
                "word_count": 0,
                "segments": [],
            }
        except Exception as e:
            logger.error(f"Audio transcription error: {e}")
            return {"text": "", "error": str(e)}

    def extract_entities(self, text: str) -> dict:
        """Extract named entities using spaCy + regex."""
        entities: dict[str, list] = {
            "persons": [],
            "organizations": [],
            "locations": [],
            "dates": [],
            "money": [],
            "case_numbers": [],
            "ipc_sections": [],
        }

        # Regex extractions
        entities["dates"] = [d[0] or d[1] for d in DATE_PATTERN.findall(text) if d[0] or d[1]]
        entities["money"] = MONEY_PATTERN.findall(text)
        entities["case_numbers"] = CASE_NUM_PATTERN.findall(text)
        entities["ipc_sections"] = list(set(
            m[0] or m[1] or m[2]
            for m in IPC_PATTERN.findall(text)
            if any(m)
        ))

        # spaCy NER
        nlp = _get_nlp()
        if nlp:
            try:
                doc = nlp(text[:10000])
                for ent in doc.ents:
                    if ent.label_ == "PERSON" and ent.text not in entities["persons"]:
                        entities["persons"].append(ent.text)
                    elif ent.label_ in ("ORG", "NORP") and ent.text not in entities["organizations"]:
                        entities["organizations"].append(ent.text)
                    elif ent.label_ in ("GPE", "LOC") and ent.text not in entities["locations"]:
                        entities["locations"].append(ent.text)
            except Exception as e:
                logger.warning(f"spaCy NER error: {e}")

        # Deduplicate and limit
        for key in entities:
            entities[key] = list(dict.fromkeys(entities[key]))[:20]

        return entities

    def identify_legal_charges(self, text: str) -> list[dict]:
        """Identify IPC/CrPC sections mentioned in the document."""
        charges = []
        sections_found = set()

        for match in IPC_PATTERN.finditer(text):
            section_num = match.group(1) or match.group(2) or match.group(3)
            if section_num and section_num not in sections_found:
                sections_found.add(section_num)
                charges.append({
                    "section": f"IPC {section_num}",
                    "section_number": section_num,
                    "context": text[max(0, match.start()-50):match.end()+50].strip(),
                })

        return charges

    def get_document_summary(self, text: str) -> str:
        """Generate a bullet-point summary via LLM."""
        if len(text) < 100:
            return "Document too short for summary."

        prompt = (
            f"Summarize this Indian legal document in exactly 5 bullet points. "
            f"Focus only on legally relevant facts: parties, charges, key events, evidence.\n\n"
            f"Document (first 3000 chars):\n{text[:3000]}"
        )
        return self._groq.complete(prompt, system=SYSTEM_DOCUMENT_ANALYST, max_tokens=500)
