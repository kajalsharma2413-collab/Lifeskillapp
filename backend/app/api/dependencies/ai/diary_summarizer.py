# app/api/dependencies/ai/diary_summarizer.py
"""
Diary analysis using Ollama Cloud API.
Mirrors the same _call_ollama pattern from ollama_agent.py — no LangChain/LangGraph,
no localhost dependency. Uses OLLAMA_API_KEY + OLLAMA_MODEL from .env.
"""

import os
import json
import re
import logging
from dotenv import load_dotenv
import requests

load_dotenv()
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG  (same as ollama_agent.py)
# ─────────────────────────────────────────────────────────────────────────────

OLLAMA_CLOUD_URL  = "https://ollama.com/api/chat"
OLLAMA_LOCAL_HOST = os.environ.get("OLLAMA_HOST", "").strip().rstrip("/")
OLLAMA_MODEL      = os.environ.get("OLLAMA_MODEL", "gemma4:31b-cloud")
OLLAMA_API_KEY    = os.environ.get("OLLAMA_API_KEY", "").strip()


def _api_url() -> str:
    if OLLAMA_LOCAL_HOST:
        return f"{OLLAMA_LOCAL_HOST}/api/chat"
    return OLLAMA_CLOUD_URL


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM EXCEPTIONS
# ─────────────────────────────────────────────────────────────────────────────

class ContentFilterError(Exception):
    """Raised when diary content fails validation (e.g. empty, gibberish)."""
    pass


# ─────────────────────────────────────────────────────────────────────────────
# PROMPTS
# ─────────────────────────────────────────────────────────────────────────────

DIARY_SYSTEM_PROMPT = """You are a compassionate wellness assistant that analyzes diary entries.
Your job is to read a diary entry and return a structured JSON analysis.
You must respond with ONLY valid JSON — no markdown, no explanation, no text before or after.
Be empathetic, supportive, and non-judgmental in your analysis.
Do NOT include any thinking tokens or chain-of-thought in your response."""

DIARY_ANALYSIS_PROMPT = """Read this diary entry and return ONLY a JSON object. No markdown. No extra text.

Diary Entry:
{diary_entry}

Return this exact JSON structure:

{{
  "summary": "A warm, empathetic 2-3 sentence summary of the person's emotional state and key experiences described.",
  "score": 6,
  "themes": ["theme1", "theme2"],
  "suggestions": "One gentle, actionable suggestion for the person's wellbeing."
}}

Rules:
- summary: 2-3 sentences. Empathetic and supportive. Reflect what they wrote, don't project.
- score: integer 1-10 representing overall emotional wellbeing.
    1-2 = severe distress  3-4 = struggling  5-6 = mixed/neutral  7-8 = positive  9-10 = excellent
- themes: 2-4 short strings (e.g. "stress", "gratitude", "loneliness", "achievement")
- suggestions: one kind, practical sentence. Never preachy."""

CONTENT_VALIDATION_PROMPT = """Is the following text a valid diary entry worth analyzing?
A valid entry has at least a few words expressing thoughts, feelings, or events.
Invalid entries include: completely empty text, random characters/gibberish, or single words with no meaning.

Text: {diary_entry}

Return ONLY this JSON:
{{"is_valid": true, "reason": "brief reason"}}"""


# ─────────────────────────────────────────────────────────────────────────────
# CORE HTTP CALLER  (identical pattern to ollama_agent.py)
# ─────────────────────────────────────────────────────────────────────────────

def _call_ollama(system_prompt: str, user_prompt: str, timeout: int = 60) -> str:
    """
    Call Ollama Cloud API with system + user message.
    Returns raw string content. Raises RuntimeError on failure.
    """
    headers = {"Content-Type": "application/json"}
    if OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

    body = {
        "model":   OLLAMA_MODEL,
        "stream":  False,
        "format":  "json",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "options": {
            "temperature": 0.7,
            "top_p":       0.9,
            "num_predict": 1000,
        },
    }

    url = _api_url()
    log.info("Diary summarizer Ollama call: url=%s model=%s", url, OLLAMA_MODEL)

    try:
        resp = requests.post(url, json=body, headers=headers, timeout=timeout)
    except requests.Timeout:
        raise RuntimeError(f"Ollama API timed out after {timeout}s")
    except requests.ConnectionError as e:
        raise RuntimeError(f"Ollama API connection failed: {e}")

    if resp.status_code == 401:
        raise RuntimeError(
            "Ollama API 401 Unauthorized. "
            "Check OLLAMA_API_KEY at https://ollama.com/settings/keys"
        )
    if resp.status_code == 404:
        raise RuntimeError(
            f"Ollama Cloud: model '{OLLAMA_MODEL}' not found. "
            "Use gemma4:31b-cloud for cloud API."
        )
    if resp.status_code != 200:
        raise RuntimeError(f"Ollama HTTP {resp.status_code}: {resp.text[:400]}")

    return resp.json().get("message", {}).get("content", "")


def _parse_json(raw: str) -> dict:
    """Try to parse JSON from model response, stripping markdown fences if needed."""
    if not raw:
        raise RuntimeError("Empty response from Ollama")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    cleaned = re.sub(r'^```(?:json)?\s*', '', raw.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r'\s*```$', '', cleaned.strip(), flags=re.MULTILINE)
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Failed to parse Ollama JSON response: {e}\nRaw: {raw[:300]}")


# ─────────────────────────────────────────────────────────────────────────────
# DIARY ANALYSIS WORKFLOW
# ─────────────────────────────────────────────────────────────────────────────

class DiaryAnalysisWorkflow:
    """
    Replaces the LangGraph-based workflow with direct Ollama Cloud API calls.
    Drop-in replacement — same analyze_diary() interface.
    """

    def analyze_diary(self, diary_entry: str) -> dict:
        """
        Validate and analyze a diary entry.

        Returns:
            dict with keys: summary, score, themes, suggestions

        Raises:
            ContentFilterError: if entry is invalid/empty
            RuntimeError: if Ollama API call fails
        """
        # Step 1: Validate content
        self._validate_content(diary_entry)

        # Step 2: Analyze
        return self._analyze(diary_entry)

    def _validate_content(self, diary_entry: str) -> None:
        """Raise ContentFilterError if the entry isn't worth analyzing."""
        # Fast local check first — skip API call for obviously empty entries
        if not diary_entry or not diary_entry.strip():
            raise ContentFilterError(
                "Sorry, we couldn't process your diary entry. Please try writing it again."
            )
        if len(diary_entry.strip()) < 10:
            raise ContentFilterError(
                "Your diary entry is too short. Please write a bit more so we can analyze it."
            )

        # Ask the model for gibberish/validity check
        prompt = CONTENT_VALIDATION_PROMPT.format(diary_entry=diary_entry[:500])
        try:
            raw = _call_ollama(DIARY_SYSTEM_PROMPT, prompt, timeout=30)
            result = _parse_json(raw)
            if not result.get("is_valid", True):
                raise ContentFilterError(
                    "Sorry, we couldn't process your diary entry. Please try writing it again."
                )
        except ContentFilterError:
            raise
        except Exception as e:
            # If validation call fails, log and proceed — don't block the user
            log.warning("Content validation failed (proceeding anyway): %s", e)

    def _analyze(self, diary_entry: str) -> dict:
        """Run the main diary analysis and return structured result."""
        prompt = DIARY_ANALYSIS_PROMPT.format(diary_entry=diary_entry)
        raw = _call_ollama(DIARY_SYSTEM_PROMPT, prompt, timeout=60)
        result = _parse_json(raw)
        return self._validate_result(result)

    def _validate_result(self, obj: dict) -> dict:
        """Ensure the result has all required fields with correct types."""
        # score: clamp to 1-10
        try:
            obj["score"] = max(1, min(10, int(obj.get("score", 5))))
        except (TypeError, ValueError):
            obj["score"] = 5

        # summary: must be a non-empty string
        if not isinstance(obj.get("summary"), str) or not obj["summary"].strip():
            obj["summary"] = "Your entry has been recorded."

        # themes: must be a list
        if not isinstance(obj.get("themes"), list):
            obj["themes"] = []

        # suggestions: must be a string
        if not isinstance(obj.get("suggestions"), str):
            obj["suggestions"] = "Take a moment to reflect on how you're feeling today."

        return obj