"""GPT-4V / GPT-4o vision client for evidence image analysis."""

import os
import base64
import json
from pathlib import Path
from loguru import logger

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


def _encode_image(image_path: str) -> str:
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


class VisionClient:
    """Client for GPT-4o vision — analyzes evidence images."""

    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self._client = None

        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self._client = OpenAI(api_key=api_key)
                logger.info(f"Vision client initialized with model: {model}")
            else:
                logger.warning("OPENAI_API_KEY not set — vision in mock mode")

    def analyze_image(self, image_path: str, prompt: str, system: str = "") -> str:
        """Analyze an image with a text prompt."""
        if not self._client:
            return self._mock_vision_response(image_path)

        try:
            ext = Path(image_path).suffix.lower().lstrip(".")
            mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
            b64 = _encode_image(image_path)

            messages = []
            if system:
                messages.append({"role": "system", "content": system})
            messages.append({
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    {"type": "text", "text": prompt},
                ],
            })

            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                max_tokens=1500,
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Vision API error: {e}")
            return self._mock_vision_response(image_path)

    def analyze_image_json(self, image_path: str, prompt: str, system: str = "") -> dict:
        """Analyze image and return parsed JSON."""
        json_prompt = prompt + "\n\nIMPORTANT: Respond ONLY with valid JSON."
        raw = self.analyze_image(image_path, json_prompt, system)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {
                "description": raw,
                "legal_relevance": "Unable to parse structured response",
                "evidence_strength": 5,
                "parse_error": True,
            }

    def _mock_vision_response(self, image_path: str) -> str:
        fname = Path(image_path).name
        return json.dumps({
            "description": f"Evidence image: {fname}. Mock analysis — OpenAI API key not configured.",
            "legal_relevance": "Image requires GPT-4V analysis. Set OPENAI_API_KEY for full functionality.",
            "evidence_strength": 6,
            "observations": ["Image loaded successfully", "Manual review recommended"],
            "supports_prosecution": "Cannot determine without API access",
            "supports_defense": "Cannot determine without API access",
            "chain_of_custody": "Image metadata should be verified",
            "forensic_notes": "Configure OPENAI_API_KEY for AI-powered forensic analysis",
            "mock_mode": True,
        })
