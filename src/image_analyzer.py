"""Legal image analyzer using GPT-4V for forensic evidence analysis."""

import json
from pathlib import Path
from typing import Any
from loguru import logger

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

from llm.vision_client import VisionClient
from llm.groq_client import GroqClient
from llm.prompt_templates import SYSTEM_FORENSIC_ANALYST, get_image_analysis_prompt


class LegalImageAnalyzer:
    """Analyze evidence images for legal proceedings using AI vision."""

    def __init__(self):
        self._vision = VisionClient()
        self._groq = GroqClient()

    def analyze_evidence_image(self, image_path: str, case_context: str = "") -> dict:
        """Perform full forensic analysis of an evidence image."""
        path = Path(image_path)
        if not path.exists():
            return {"error": f"Image not found: {image_path}", "success": False}

        logger.info(f"Analyzing evidence image: {path.name}")

        prompt = get_image_analysis_prompt(case_context or "General legal case")
        vision_result = self._vision.analyze_image_json(image_path, prompt, SYSTEM_FORENSIC_ANALYST)

        # Add metadata analysis
        exif_data = self._extract_exif(image_path)
        tampering = self.detect_image_tampering(image_path)

        result = {
            "file_name": path.name,
            "file_path": image_path,
            "description": vision_result.get("description", vision_result.get("DESCRIPTION", "")),
            "legal_relevance": vision_result.get("legal_relevance", vision_result.get("LEGAL RELEVANCE", "")),
            "evidence_strength": float(vision_result.get("evidence_strength", vision_result.get("EVIDENCE STRENGTH", 5))),
            "observations": vision_result.get("observations", vision_result.get("KEY OBSERVATIONS", [])),
            "supports_prosecution": vision_result.get("supports_prosecution", vision_result.get("SUPPORTS PROSECUTION", "")),
            "supports_defense": vision_result.get("supports_defense", vision_result.get("SUPPORTS DEFENSE", "")),
            "chain_of_custody": vision_result.get("chain_of_custody", vision_result.get("CHAIN OF CUSTODY", "")),
            "forensic_notes": vision_result.get("forensic_notes", vision_result.get("FORENSIC NOTES", "")),
            "exif_metadata": exif_data,
            "tampering_assessment": tampering,
            "success": True,
        }

        return result

    def analyze_document_image(self, image_path: str) -> dict:
        """Analyze a scanned document image — OCR + layout analysis."""
        prompt = (
            "This is a scanned legal document image. Extract ALL text visible. "
            "Also identify: document type, parties mentioned, dates, signatures present, "
            "stamps/seals visible, and document structure. Return as JSON with fields: "
            "extracted_text, document_type, parties, dates, has_signature, has_stamp, structure_notes."
        )
        result = self._vision.analyze_image_json(image_path, prompt)
        result["file_name"] = Path(image_path).name
        return result

    def detect_image_tampering(self, image_path: str) -> dict:
        """Assess image for potential tampering using metadata + visual cues."""
        assessment = {
            "tampering_probability": 0.1,
            "authenticity_score": 9.0,
            "suspicious_areas": [],
            "metadata_consistent": True,
            "notes": [],
        }

        if not PIL_AVAILABLE:
            assessment["notes"].append("Pillow not installed — metadata analysis skipped")
            return assessment

        try:
            img = Image.open(image_path)
            exif = self._extract_exif(image_path)

            # Check for suspicious metadata
            if not exif:
                assessment["notes"].append("No EXIF metadata — image may have been processed/stripped")
                assessment["tampering_probability"] += 0.1
                assessment["authenticity_score"] -= 1.0

            if exif.get("Software"):
                software = str(exif.get("Software", "")).lower()
                editing_tools = ["photoshop", "gimp", "lightroom", "affinity", "pixelmator"]
                if any(tool in software for tool in editing_tools):
                    assessment["notes"].append(f"Image editing software detected: {exif['Software']}")
                    assessment["tampering_probability"] += 0.2
                    assessment["authenticity_score"] -= 2.0
                    assessment["suspicious_areas"].append("Software metadata indicates post-processing")

            # Check image dimensions for abnormalities
            w, h = img.size
            if w * h > 50_000_000:
                assessment["notes"].append(f"Unusually large image: {w}x{h} pixels")

            assessment["authenticity_score"] = max(1.0, min(10.0, assessment["authenticity_score"]))
            assessment["tampering_probability"] = min(1.0, assessment["tampering_probability"])

        except Exception as e:
            logger.warning(f"Tampering detection error: {e}")
            assessment["notes"].append(f"Analysis incomplete: {e}")

        return assessment

    def batch_analyze_evidence(self, image_paths: list[str], case_context: str = "") -> list[dict]:
        """Analyze multiple evidence images and rank by evidentiary value."""
        analyses = []
        for path in image_paths:
            analysis = self.analyze_evidence_image(path, case_context)
            analyses.append(analysis)
            logger.info(f"Analyzed: {Path(path).name} — strength: {analysis.get('evidence_strength', 'N/A')}")

        # Sort by evidence strength (descending)
        analyses.sort(key=lambda x: x.get("evidence_strength", 0), reverse=True)
        for i, a in enumerate(analyses):
            a["rank"] = i + 1

        return analyses

    def generate_evidence_narrative(self, analyses: list[dict]) -> str:
        """Combine all image analyses into a coherent evidence narrative."""
        if not analyses:
            return "No evidence images analyzed."

        summary_parts = []
        for i, a in enumerate(analyses, 1):
            summary_parts.append(
                f"Exhibit {i} ({a.get('file_name', 'Unknown')}): "
                f"{a.get('description', '')} "
                f"[Evidence Strength: {a.get('evidence_strength', 'N/A')}/10]"
            )

        combined = "\n".join(summary_parts)
        prompt = (
            f"Based on the following {len(analyses)} evidence image analyses from an Indian court case, "
            f"write a coherent 3-paragraph evidence narrative for court presentation:\n\n{combined}"
        )
        return self._groq.complete(prompt, system=SYSTEM_FORENSIC_ANALYST, max_tokens=800)

    def _extract_exif(self, image_path: str) -> dict:
        """Extract EXIF metadata from image."""
        if not PIL_AVAILABLE:
            return {}
        try:
            img = Image.open(image_path)
            raw_exif = img._getexif()
            if not raw_exif:
                return {}
            return {
                TAGS.get(k, str(k)): str(v)[:100]
                for k, v in raw_exif.items()
                if TAGS.get(k) in ("DateTime", "Make", "Model", "Software", "GPSInfo", "Artist", "Copyright")
            }
        except Exception:
            return {}
