# app/api/dependencies/ai/mentor_chatbot/mentor_agent.py
"""
FIXED: Replaced ChatOllama (localhost:11434) with direct requests calls to
Ollama Cloud API — same pattern as diary_summarizer.py and rag_chatbot/shared.py.

Public interface is UNCHANGED:
    MentorAgent(model_name=..., api_key=...) — init args kept for compat, ignored
    .process_conversation(child_input, child_profile, chat_history) -> str
    .generate_initial_response(child_profile) -> str
"""

import json
import logging
import os
import re

import requests
from dotenv import load_dotenv
from langgraph.graph import END, START, StateGraph

from .models import ChatState, ChildProfile, MentorResponse

logger = logging.getLogger(__name__)
load_dotenv()

# ── Ollama Cloud config ───────────────────────────────────────────────────────
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "").strip()
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL", "gemma4:31b-cloud")
OLLAMA_HOST    = os.getenv("OLLAMA_HOST", "").strip().rstrip("/")
OLLAMA_URL     = f"{OLLAMA_HOST}/api/chat" if OLLAMA_HOST else "https://ollama.com/api/chat"


# ── Core HTTP caller ──────────────────────────────────────────────────────────

def _call_ollama(messages: list[dict], temperature: float = 0.7,
                 as_json: bool = False, timeout: int = 90) -> str:
    """POST to Ollama Cloud and return raw string content."""
    headers = {"Content-Type": "application/json"}
    if OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

    body: dict = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": messages,
        "options": {"temperature": temperature},
    }
    if as_json:
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


def _call_ollama_structured(messages: list[dict], temperature: float = 0.0) -> MentorResponse:
    """Call Ollama expecting a JSON response, parse into MentorResponse."""
    raw = _call_ollama(messages, temperature=temperature, as_json=True)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Strip markdown fences and retry
        cleaned = re.sub(r'^```(?:json)?\s*', '', raw.strip(), flags=re.MULTILINE)
        cleaned = re.sub(r'\s*```$', '', cleaned.strip(), flags=re.MULTILINE)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback: treat the whole text as the response field
            return MentorResponse(response=raw.strip())
    return MentorResponse(**data)


# ── Mentor Agent ──────────────────────────────────────────────────────────────

class MentorAgent:
    """Mentor chatbot agent using LangGraph workflow — now calls Ollama Cloud directly."""

    def __init__(self, model_name: str | None = None, api_key: str | None = None):
        self._create_workflow()

    def _create_workflow(self) -> None:
        graph = StateGraph(ChatState)
        graph.add_node("context_analysis", self._context_analysis_node)
        graph.add_node("mentor_response", self._mentor_response_node)
        graph.add_edge(START, "context_analysis")
        graph.add_edge("context_analysis", "mentor_response")
        graph.add_edge("mentor_response", END)
        self.workflow = graph.compile()
        logger.info("Mentor chatbot workflow created")

    # ── Node 1: Context analysis ──────────────────────────────────────────────

    def _context_analysis_node(self, state: ChatState) -> ChatState:
        try:
            child_input  = state["child_input"]
            profile      = state["child_profile"]
            chat_history = state.get("chat_history", [])

            history_context = "This is the beginning of our conversation."
            if chat_history:
                recent = chat_history[-6:]
                history_context = "\n".join(
                    f"{'Child' if m['role'] == 'user' else 'Mentor'}: {m['content']}"
                    for m in recent
                )

            past_context = ""
            if profile.past_summaries:
                past_context = "\n\nPast conversation summaries:\n" + "\n".join(
                    f"- {s}" for s in profile.past_summaries[-6:]
                )

            prompt = (
                f"You are analyzing a conversation with {profile.user_name}, "
                f"a child aged {profile.age}.\n\n"
                f"Child's latest message:\n{child_input}\n\n"
                f"Recent conversation:\n{history_context}\n\n"
                f"Child's diary entry:\n{profile.current_diary_entry}"
                f"{past_context}\n\n"
                "Analyze and summarize:\n"
                "1. Their current emotional tone and feelings.\n"
                "2. How this relates to their diary entry and past experiences.\n"
                "3. The type of support, encouragement, or guidance they most need right now.\n"
                "4. How to naturally continue the flow of the conversation using their name appropriately.\n\n"
                f"Keep the analysis short (4–6 sentences). Consider their age ({profile.age})."
            )

            messages = [{"role": "user", "content": prompt}]
            state["current_context"] = _call_ollama(messages, temperature=0.3, timeout=60)
        except Exception as e:
            logger.error(f"Context analysis error: {e}")
            state["current_context"] = "Unable to analyze context — will provide supportive response."
        return state

    # ── Node 2: Mentor response ───────────────────────────────────────────────

    def _mentor_response_node(self, state: ChatState) -> ChatState:
        try:
            profile      = state["child_profile"]
            chat_history = state.get("chat_history", [])

            recent_chat = "This is the start of our conversation."
            if chat_history:
                recent_chat = "\n".join(
                    f"{'Child' if m['role'] == 'user' else 'Mentor'}: {m['content']}"
                    for m in chat_history[-4:]
                )

            past_summaries_text = "No previous conversations."
            if profile.past_summaries:
                past_summaries_text = "\n".join(f"- {s}" for s in profile.past_summaries)

            system_prompt = (
                "You are a calm, caring mentor for children ages 7–14. "
                "Your voice should feel like a kind older sibling or a gentle teacher: warm, reassuring, and safe. "
                "Always prioritize the child's emotional safety and keep language age-appropriate.\n\n"
                "Rules:\n"
                "- Sanitize profanity: translate to neutral phrases (e.g. 'really upset', 'very frustrated').\n"
                "- Validate first — name the feeling and acknowledge it. Use their name naturally.\n"
                "- Age-appropriate length: ages 7–9 short sentences; ages 10–14 3–5 sentences.\n"
                "- Offer 1–2 concrete, low-effort coping suggestions.\n"
                "- Ask one caring follow-up question.\n"
                "- Never minimize the child's feelings.\n"
                "- Safety escalation: if the diary suggests harm or danger, gently instruct them to tell a trusted adult.\n"
                "- For internet/search questions, refer them to 'Sakai' — a chatbot with web search and natural disaster comics.\n"
                "- Respond ONLY with a JSON object: {\"response\": \"<your reply>\"}"
            )

            user_prompt = (
                f"Child's Name: {profile.user_name}\n"
                f"Child's Age: {profile.age}\n"
                f"Child's Current Input: {state['child_input']}\n\n"
                f"Context Analysis: {state['current_context']}\n\n"
                f"Diary Entry for Today: {profile.current_diary_entry}\n\n"
                f"Past Experiences Summary: {past_summaries_text}\n\n"
                f"Recent Conversation:\n{recent_chat}\n\n"
                "Based on the above, respond as their caring mentor."
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ]
            result = _call_ollama_structured(messages, temperature=0.7)
            state["mentor_response"] = result.response
        except Exception as e:
            logger.error(f"Mentor response error: {e}")
            state["mentor_response"] = (
                "I'm here to listen and support you. Can you tell me more about what's on your mind?"
            )
        return state

    # ── Public API (UNCHANGED) ────────────────────────────────────────────────

    def process_conversation(
        self, child_input: str, child_profile: ChildProfile, chat_history: list[dict]
    ) -> str:
        try:
            result = self.workflow.invoke({
                "child_input":    child_input,
                "child_profile":  child_profile,
                "current_context": "",
                "mentor_response": "",
                "chat_history":   chat_history,
            })
            return result["mentor_response"]
        except Exception as e:
            logger.error(f"Workflow error: {e}")
            return "I'm here to support you. Could you tell me a bit more about what's on your mind?"

    def generate_initial_response(self, child_profile: ChildProfile) -> str:
        try:
            past_context = ""
            if child_profile.past_summaries:
                past_context = (
                    "\n\nI remember our past conversations where we talked about:\n"
                    + "\n".join(f"- {s}" for s in child_profile.past_summaries[-3:])
                )

            system_prompt = (
                "You are a warm, caring mentor speaking to a child.\n"
                "- Address them by name naturally and warmly.\n"
                "- Read their diary entry with empathy.\n"
                "- Reference past experiences if available.\n"
                "- Acknowledge their emotions appropriately for their age.\n"
                "- Offer gentle encouragement or validation.\n"
                "- Ask one caring follow-up question.\n"
                "- Keep it warm, age-appropriate, and safe.\n"
                "- Respond ONLY with a JSON object: {\"response\": \"<your reply>\"}"
            )

            user_prompt = (
                f"Child's Name: {child_profile.user_name}\n"
                f"Child's Age: {child_profile.age}\n\n"
                f"Today's diary entry:\n{child_profile.current_diary_entry}"
                f"{past_context}\n\n"
                "Generate a warm initial response that acknowledges their diary entry and shows you care."
            )

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ]
            result = _call_ollama_structured(messages, temperature=0.7)
            return result.response
        except Exception as e:
            logger.error(f"Initial response error: {e}")
            return (
                "Hello! Thank you for sharing your diary entry with me. "
                "I can tell you put thought into writing it. How are you feeling about everything you shared?"
            )
