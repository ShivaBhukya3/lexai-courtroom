"""Testimony transcriber using OpenAI Whisper + LLM analysis."""

import json
from pathlib import Path
from loguru import logger

from llm.groq_client import GroqClient
from llm.prompt_templates import get_testimony_analysis_prompt, SYSTEM_LEGAL_ANALYST

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False


class TestimonyTranscriber:
    """Transcribe and analyze witness testimony audio."""

    def __init__(self, whisper_model: str = "base"):
        self._groq = GroqClient()
        self._whisper_model_name = whisper_model
        self._whisper = None

        if WHISPER_AVAILABLE:
            try:
                logger.info(f"Loading Whisper model: {whisper_model}")
                self._whisper = whisper.load_model(whisper_model)
            except Exception as e:
                logger.error(f"Failed to load Whisper: {e}")
        else:
            logger.warning("openai-whisper not installed — transcription will use mock data")

    def transcribe_testimony(self, audio_path: str) -> dict:
        """Transcribe audio testimony using Whisper."""
        path = Path(audio_path)
        if not path.exists():
            return {"error": f"Audio file not found: {audio_path}", "success": False}

        logger.info(f"Transcribing: {path.name}")

        if self._whisper:
            return self._whisper_transcribe(audio_path)
        else:
            return self._mock_transcription(audio_path)

    def _whisper_transcribe(self, audio_path: str) -> dict:
        """Run Whisper transcription pipeline."""
        try:
            result = self._whisper.transcribe(audio_path, verbose=False)
            text = result.get("text", "").strip()
            segments = result.get("segments", [])

            return {
                "transcript": text,
                "text": text,
                "duration_seconds": segments[-1]["end"] if segments else 0,
                "language": result.get("language", "en"),
                "word_count": len(text.split()),
                "segments": [
                    {
                        "start": round(s["start"], 2),
                        "end": round(s["end"], 2),
                        "text": s["text"].strip(),
                        "confidence": round(1 - s.get("no_speech_prob", 0.1), 2),
                    }
                    for s in segments
                ],
                "confidence_score": round(
                    1 - (sum(s.get("no_speech_prob", 0.1) for s in segments) / max(len(segments), 1)),
                    2,
                ),
                "file_name": Path(audio_path).name,
                "success": True,
            }
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            return {"error": str(e), "success": False}

    def _mock_transcription(self, audio_path: str) -> dict:
        """Return mock transcription when Whisper unavailable."""
        fname = Path(audio_path).name
        mock_text = (
            f"[Mock Transcription — {fname}] "
            "This is a placeholder transcription. "
            "Install openai-whisper to enable real audio transcription. "
            "The witness stated that on the date in question, they observed the events as described in the complaint. "
            "They confirmed the identity of the accused and stated they were present at the scene. "
            "The witness maintained their account under cross-examination without significant contradictions."
        )
        return {
            "transcript": mock_text,
            "text": mock_text,
            "duration_seconds": 120,
            "language": "en",
            "word_count": len(mock_text.split()),
            "segments": [{"start": 0, "end": 120, "text": mock_text, "confidence": 0.85}],
            "confidence_score": 0.85,
            "file_name": fname,
            "success": True,
            "mock_mode": True,
        }

    def analyze_testimony_content(self, transcript: str, case_context: str = "") -> dict:
        """Analyze testimony for legal significance using LLM."""
        if len(transcript) < 50:
            return {"error": "Transcript too short for analysis"}

        prompt = get_testimony_analysis_prompt(transcript[:4000], case_context or "General legal case")
        raw = self._groq.complete_json(prompt, system=SYSTEM_LEGAL_ANALYST)

        return {
            "key_statements": raw.get("KEY_STATEMENTS", raw.get("key_statements", [])),
            "credibility_score": float(raw.get("CREDIBILITY_SCORE", raw.get("credibility_score", 7.0))),
            "contradictions": raw.get("CONTRADICTIONS", raw.get("contradictions", [])),
            "prosecution_value": raw.get("PROSECUTION_VALUE", raw.get("prosecution_value", "")),
            "defense_value": raw.get("DEFENSE_VALUE", raw.get("defense_value", "")),
            "perjury_flags": raw.get("PERJURY_FLAGS", raw.get("perjury_flags", [])),
            "emotional_tone": raw.get("EMOTIONAL_TONE", raw.get("emotional_tone", "Neutral")),
            "summary": raw.get("SUMMARY", raw.get("summary", "")),
        }

    def extract_key_statements(self, transcript: str) -> list[dict]:
        """Extract legally significant statements from testimony."""
        prompt = (
            f"From this witness testimony, extract 5-10 key legally significant statements. "
            f"For each statement return JSON array with: "
            f"statement, legal_significance, supports_prosecution (bool), supports_defense (bool), "
            f"approximate_timestamp.\n\nTestimony:\n{transcript[:3000]}"
        )
        raw = self._groq.complete_json(prompt, system=SYSTEM_LEGAL_ANALYST)
        if isinstance(raw, list):
            return raw
        return raw.get("statements", raw.get("key_statements", []))

    def detect_inconsistencies(self, testimonies: list[dict]) -> list[dict]:
        """Cross-analyze multiple testimonies for contradictions."""
        if len(testimonies) < 2:
            return []

        summaries = []
        for i, t in enumerate(testimonies):
            text = t.get("transcript", t.get("text", ""))[:1000]
            summaries.append(f"Witness {i+1} ({t.get('file_name', f'Witness {i+1}')}):\n{text}")

        combined = "\n\n---\n\n".join(summaries)
        prompt = (
            f"Analyze these {len(testimonies)} witness testimonies and identify ALL contradictions "
            f"between them. For each contradiction return a JSON array with: "
            f"witness_a, witness_b, topic, witness_a_says, witness_b_says, severity (High/Medium/Low), "
            f"legal_implication.\n\nTestimonies:\n{combined}"
        )
        raw = self._groq.complete_json(prompt, system=SYSTEM_LEGAL_ANALYST)
        if isinstance(raw, list):
            return raw
        return raw.get("contradictions", [])

    def generate_testimony_summary(self, transcript: str) -> str:
        """Generate 3-paragraph narrative summary of testimony."""
        prompt = (
            f"Write a 3-paragraph professional summary of this witness testimony for court records. "
            f"Focus on: (1) Who the witness is and what they claim to have witnessed, "
            f"(2) Key facts they established, "
            f"(3) Credibility and consistency of the testimony.\n\n"
            f"Testimony:\n{transcript[:3000]}"
        )
        return self._groq.complete(prompt, system=SYSTEM_LEGAL_ANALYST, max_tokens=600)
