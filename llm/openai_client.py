"""OpenAI client for GPT-4o text completions."""

import os
import json
from loguru import logger

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


class OpenAIClient:
    """Client for OpenAI API — text generation fallback."""

    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.1, max_tokens: int = 4096):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None

        if OPENAI_AVAILABLE:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self._client = OpenAI(api_key=api_key)
                logger.info(f"OpenAI client initialized with model: {model}")
            else:
                logger.warning("OPENAI_API_KEY not set")
        else:
            logger.warning("openai package not installed")

    def complete(self, prompt: str, system: str = "", **kwargs) -> str:
        if not self._client:
            return "OpenAI not configured. Set OPENAI_API_KEY."

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=kwargs.get("temperature", self.temperature),
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI error: {e}")
            return f"Error: {e}"

    def complete_json(self, prompt: str, system: str = "") -> dict:
        json_system = (system or "") + "\n\nIMPORTANT: Respond ONLY with valid JSON."
        raw = self.complete(prompt, system=json_system)
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0]
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return {"raw_response": raw, "parse_error": True}
