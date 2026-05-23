# app/api/dependencies/ai/rag_chatbot/shared.py
"""
Ollama Cloud API callers for the RAG chatbot.
- No LangChain/LangGraph LLM integration (uses direct requests)
- Bulletproof JSON parsing with plain-text fallback for models that ignore format:json
"""

import json
import logging
import os
import re
from typing import List, Literal, TypedDict

import requests
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from pydantic import BaseModel, Field

log = logging.getLogger(__name__)

# ── Ollama Cloud config ───────────────────────────────────────────────────────
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "").strip()
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL", "gemma4:31b-cloud")
OLLAMA_HOST    = os.getenv("OLLAMA_HOST", "").strip().rstrip("/")
OLLAMA_URL     = f"{OLLAMA_HOST}/api/chat" if OLLAMA_HOST else "https://ollama.com/api/chat"

VALID_ROUTES = {"rag", "answer", "web", "end"}


# ── Pydantic schemas (UNCHANGED) ─────────────────────────────────────────────
class RouteDecision(BaseModel):
    route: Literal["rag", "answer", "web", "end"]
    reply: str | None = Field(None, description="Filled only when route == 'end'")
    reasoning: str = Field(description="Brief explanation for the routing decision")


class RagJudge(BaseModel):
    sufficient: bool = Field(description="Whether RAG results are sufficient")
    reasoning: str = Field(description="Why the RAG content is/isn't sufficient")


# ── Core HTTP caller ──────────────────────────────────────────────────────────
def _lc_to_ollama_messages(messages: list) -> list[dict]:
    result = []
    for m in messages:
        if isinstance(m, SystemMessage):
            result.append({"role": "system", "content": m.content})
        elif isinstance(m, HumanMessage):
            result.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            result.append({"role": "assistant", "content": m.content})
        elif isinstance(m, tuple) and len(m) == 2:
            role_map = {"system": "system", "user": "user", "assistant": "assistant",
                        "human": "user", "ai": "assistant"}
            result.append({"role": role_map.get(m[0], "user"), "content": m[1]})
    return result


def _call_ollama_raw(messages: list, temperature: float = 0.0,
                     use_json_format: bool = False, timeout: int = 60) -> str:
    headers = {"Content-Type": "application/json"}
    if OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

    body: dict = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": _lc_to_ollama_messages(messages),
        "options": {"temperature": temperature},
    }
    if use_json_format:
        body["format"] = "json"

    try:
        resp = requests.post(OLLAMA_URL, json=body, headers=headers, timeout=timeout)
    except requests.Timeout:
        raise RuntimeError(f"Ollama API timed out after {timeout}s")
    except requests.ConnectionError as e:
        raise RuntimeError(f"Ollama API connection failed: {e}")

    if resp.status_code == 401:
        raise RuntimeError("Ollama 401: check OLLAMA_API_KEY")
    if resp.status_code == 404:
        raise RuntimeError(f"Ollama 404: model '{OLLAMA_MODEL}' not found")
    if resp.status_code != 200:
        raise RuntimeError(f"Ollama HTTP {resp.status_code}: {resp.text[:400]}")

    return resp.json().get("message", {}).get("content", "")


# ── JSON parsing with plain-text fallback ─────────────────────────────────────
def _parse_json(raw: str) -> dict:
    """
    Try every reasonable way to extract a JSON dict from the model response.
    Never raises — always returns a dict (may be empty on total failure).
    """
    if not raw or not raw.strip():
        return {}

    # 1. Direct parse
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 2. Strip markdown fences
    cleaned = re.sub(r'```(?:json)?\s*', '', raw, flags=re.IGNORECASE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 3. Extract first {...} block
    match = re.search(r'\{[^{}]*\}', cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # 4. Try largest {...} block (handles nested)
    match = re.search(r'\{.*\}', cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # 5. Give up — return empty dict, callers will use defaults
    log.warning("_parse_json: could not parse JSON, raw=%s", raw[:200])
    return {}


def _parse_route_decision(raw: str) -> RouteDecision:
    """
    Parse RouteDecision from model response.
    Falls back to extracting route keyword from plain text when JSON fails.
    This handles responses like:
        'Route: answer\nReasoning: ...'
        'I would route this to rag because...'
    """
    data = _parse_json(raw)

    # If JSON gave us a valid route, use it
    if data.get("route") in VALID_ROUTES:
        return RouteDecision(
            route=data["route"],
            reply=data.get("reply"),
            reasoning=data.get("reasoning", ""),
        )

    # Plain-text fallback: scan for route keyword
    text_lower = raw.lower()

    # Check for explicit "Route: X" pattern first
    route_match = re.search(r'\broute[:\s]+(\w+)', text_lower)
    if route_match and route_match.group(1) in VALID_ROUTES:
        route = route_match.group(1)
    else:
        # Infer from keywords in the reasoning text
        if any(w in text_lower for w in ["rag", "disaster", "comic", "safety comic", "educational comic"]):
            route = "rag"
        elif any(w in text_lower for w in ["web", "search", "current", "recent", "news", "location"]):
            route = "web"
        elif any(w in text_lower for w in ["end", "greeting", "hello", "goodbye", "small talk"]):
            route = "end"
        else:
            route = "answer"  # safe default

    # Extract reasoning: everything after "Reasoning:" if present
    reasoning_match = re.search(r'reasoning[:\s]+(.+)', raw, re.IGNORECASE | re.DOTALL)
    reasoning = reasoning_match.group(1).strip()[:300] if reasoning_match else raw.strip()[:200]

    log.info("_parse_route_decision: plain-text fallback → route=%s", route)
    return RouteDecision(route=route, reasoning=reasoning)


def _parse_rag_judge(raw: str) -> RagJudge:
    """
    Parse RagJudge from model response.
    Falls back to keyword scan when JSON fails.
    """
    data = _parse_json(raw)
    if "sufficient" in data:
        return RagJudge(
            sufficient=bool(data["sufficient"]),
            reasoning=data.get("reasoning", ""),
        )

    # Plain-text fallback
    text_lower = raw.lower()
    sufficient = any(w in text_lower for w in ["sufficient", "yes", "enough", "adequate", "can answer"])
    insufficient = any(w in text_lower for w in ["insufficient", "not enough", "no ", "inadequate", "cannot answer", "need web"])
    if insufficient:
        sufficient = False

    log.info("_parse_rag_judge: plain-text fallback → sufficient=%s", sufficient)
    return RagJudge(sufficient=sufficient, reasoning=raw.strip()[:300])


# ── Structured-output LLM wrappers ───────────────────────────────────────────

class _RouterLLM:
    """Invokes Ollama and parses RouteDecision with plain-text fallback."""
    def invoke(self, messages: list) -> RouteDecision:
        raw = _call_ollama_raw(messages, temperature=0.0, use_json_format=True, timeout=60)
        return _parse_route_decision(raw)
    def with_config(self, **_): return self


class _JudgeLLM:
    """Invokes Ollama and parses RagJudge with plain-text fallback."""
    def invoke(self, messages: list) -> RagJudge:
        raw = _call_ollama_raw(messages, temperature=0.0, use_json_format=True, timeout=60)
        return _parse_rag_judge(raw)
    def with_config(self, **_): return self


class _PlainLLM:
    """Invokes Ollama and returns AIMessage."""
    def __init__(self, temperature: float = 0.7): self._temperature = temperature
    def invoke(self, messages: list) -> AIMessage:
        content = _call_ollama_raw(messages, temperature=self._temperature,
                                   use_json_format=False, timeout=90)
        return AIMessage(content=content)
    def with_config(self, **_): return self


# ── LLM instances (drop-in replacements) ─────────────────────────────────────
router_llm = _RouterLLM()
judge_llm  = _JudgeLLM()
answer_llm = _PlainLLM(temperature=0.7)


# ── Shared state type (UNCHANGED) ─────────────────────────────────────────────
class AgentState(TypedDict, total=False):
    messages: List[BaseMessage]
    original_question: str
    contextualized_question: str
    route: Literal["rag", "answer", "web", "end"]
    rag: str
    web: str
    routing_reasoning: str
    processing_notes: str
