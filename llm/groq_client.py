"""Groq LLM client for fast inference using Llama3-70B."""

import os
import json
from typing import Any, Generator
from loguru import logger

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False


class GroqClient:
    """Client for Groq API — primary LLM for text generation."""

    def __init__(self, model: str = "llama-3.3-70b-versatile", temperature: float = 0.1, max_tokens: int = 4096):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self._client = None

        if GROQ_AVAILABLE:
            api_key = os.getenv("GROQ_API_KEY")
            if api_key:
                self._client = Groq(api_key=api_key)
                logger.info(f"Groq client initialized with model: {model}")
            else:
                logger.warning("GROQ_API_KEY not set — Groq client in mock mode")
        else:
            logger.warning("groq package not installed — using mock responses")

    def complete(self, prompt: str, system: str = "", **kwargs) -> str:
        """Send a completion request and return the response text."""
        if not self._client:
            return self._mock_response(prompt)

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
            logger.error(f"Groq API error: {e}")
            return self._mock_response(prompt)

    def complete_json(self, prompt: str, system: str = "", **kwargs) -> dict:
        """Request JSON output and parse it."""
        json_system = (system or "") + "\n\nIMPORTANT: Respond ONLY with valid JSON. No markdown, no explanation."
        raw = self.complete(prompt, system=json_system, **kwargs)

        # Strip markdown code fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[-1]
            raw = raw.rsplit("```", 1)[0]

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("Failed to parse JSON response — returning raw text")
            return {"raw_response": raw, "parse_error": True}

    def stream(self, prompt: str, system: str = "") -> Generator[str, None, None]:
        """Stream response tokens."""
        if not self._client:
            yield self._mock_response(prompt)
            return

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        try:
            stream = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
        except Exception as e:
            logger.error(f"Groq stream error: {e}")
            yield self._mock_response(prompt)

    def _mock_response(self, prompt: str) -> str:
        """Return a mock response when API is unavailable."""
        _pl = prompt.lower()
        if ("generate" in _pl and "cross-examination questions" in _pl) or "witness statement" in _pl:
            return json.dumps({
                "questions": [
                    {"question": "Is it not true that you did not personally witness the transaction you described?", "purpose": "Challenge direct knowledge", "expected_answer": "I was present", "follow_up_if_yes": "Then why does your statement say otherwise?", "follow_up_if_no": "So your evidence is hearsay — you are telling the court what others told you?"},
                    {"question": "How certain are you about the exact date you mentioned in your statement?", "purpose": "Test memory reliability", "expected_answer": "Very certain", "follow_up_if_yes": "Then why does your initial police statement mention a different date?", "follow_up_if_no": "So your testimony on dates is not reliable?"},
                    {"question": "Did you have any financial dealings with the accused before this incident?", "purpose": "Reveal prior relationship / bias", "expected_answer": "No", "follow_up_if_yes": "Were those dealings amicable, or were there disputes?", "follow_up_if_no": "Then what is your motive for testifying against the accused?"},
                    {"question": "Have you ever made a complaint that was later found to be incorrect or withdrawn?", "purpose": "Attack credibility", "expected_answer": "No", "follow_up_if_yes": "Can you explain the circumstances of that complaint?", "follow_up_if_no": "So this is the first time you have involved yourself in legal proceedings?"},
                    {"question": "Who else was present when the alleged incident occurred?", "purpose": "Establish corroboration gaps", "expected_answer": "I was alone / several people", "follow_up_if_yes": "Why have none of those witnesses come forward to support your account?", "follow_up_if_no": "So there is no independent witness to corroborate your version of events?"},
                    {"question": "Is it possible that you misunderstood the accused's intentions at the time?", "purpose": "Introduce alternative interpretation", "expected_answer": "No, I understood clearly", "follow_up_if_yes": "Then your testimony is based on an assumption, not a fact?", "follow_up_if_no": "Yet you had no prior dealings with the accused to know their usual conduct?"},
                    {"question": "How much time elapsed between the alleged incident and when you first reported it to authorities?", "purpose": "Challenge prompt reporting / freshness", "expected_answer": "Immediately / few days", "follow_up_if_yes": "What prevented you from reporting immediately?", "follow_up_if_no": "A delay of that length — did it affect the accuracy of your recollection?"},
                    {"question": "Were you under any pressure from a third party to file this complaint?", "purpose": "Expose external influence", "expected_answer": "No", "follow_up_if_yes": "Who pressured you, and what did they stand to gain?", "follow_up_if_no": "So you acted entirely on your own initiative?"},
                    {"question": "Can you produce any documentary evidence — receipts, messages, emails — that supports your statement?", "purpose": "Test evidential basis", "expected_answer": "Yes / No", "follow_up_if_yes": "Were those documents produced before the investigating officer?", "follow_up_if_no": "Then the court is being asked to convict solely on your uncorroborated word?"},
                    {"question": "Is it not a fact that your statement today differs in material particulars from what you told the police?", "purpose": "Highlight inconsistencies", "expected_answer": "No, it is consistent", "follow_up_if_yes": "Which version should the court believe — the one you gave under oath today or the one you gave to the police?", "follow_up_if_no": "I put it to you that the discrepancies show your account is unreliable."},
                ]
            })
        # Defense check must come before prosecution — defense prompts mention "prosecution" too
        if "generate full defense" in _pl or "defense case structure" in _pl or "acquittal" in _pl:
            return json.dumps({
                "opening_statement": "The defense will demonstrate that the prosecution has failed to discharge its burden of proof beyond reasonable doubt.",
                "charge_counter_arguments": [{"charge": "Primary charge", "prosecution_gaps": ["Lack of direct evidence", "No eyewitness"], "alternative_explanation": "The accused was not present at the scene and has credible alibi witnesses."}],
                "closing_statement": "Reasonable doubt exists on every charge. The accused deserves complete acquittal.",
                "acquittal_grounds": ["Insufficient evidence", "Benefit of doubt", "Prosecution failed to prove mens rea"],
                "argument_strength_score": 6.8,
                "cited_precedents": ["Kali Ram v. State of Himachal Pradesh (1973)", "State of UP v. Krishna Gopal (1988)"],
                "mock_mode": True,
            })
        if "prosecution" in _pl or "generate full prosecution" in _pl:
            return json.dumps({
                "opening_statement": "The prosecution will demonstrate beyond reasonable doubt that the accused committed the charged offences through direct and circumstantial evidence.",
                "charge_arguments": [{"charge": "Primary charge", "elements": ["Actus reus established", "Mens rea evident from conduct"], "evidence": ["Documentary evidence", "Witness testimony"], "precedents": ["Relevant Supreme Court precedent"]}],
                "closing_statement": "The evidence is clear and unambiguous. We urge the court to convict and impose appropriate sentence.",
                "sentencing_recommendation": "Maximum sentence warranted given the gravity of the offence.",
                "argument_strength_score": 7.2,
                "cited_precedents": ["Bachan Singh v. State of Punjab (1980)", "State of Maharashtra v. Sharad Sridhar Shardkar (1984)"],
                "mock_mode": True,
            })
        return (
            "LexAI Mock Response: API key not configured. "
            "Please set GROQ_API_KEY in your .env file. "
            "Get a free key at https://console.groq.com"
        )
