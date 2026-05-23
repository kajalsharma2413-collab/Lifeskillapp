"""
langchain_utils.py — RAG chatbot contextualization chain

FIXED: Replaced ChatOllama (which hardcoded localhost:11434) with a direct
`requests` call to the Ollama Cloud API, matching the pattern used by
ollama_agent.py and diary_summarizer.py.

The public interface is unchanged:
    contextualise_chain.invoke({"chat_history": [...], "input": "..."}) -> str
"""

import logging
import os

import requests
from langchain_core.messages import AIMessage, HumanMessage

logger = logging.getLogger(__name__)

# ── Ollama Cloud config ───────────────────────────────────────────────────────
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL", "gemma4:31b-cloud")
OLLAMA_HOST    = os.getenv("OLLAMA_HOST", "").rstrip("/")
OLLAMA_URL     = f"{OLLAMA_HOST}/api/chat" if OLLAMA_HOST else "https://ollama.com/api/chat"

# ── System prompt ─────────────────────────────────────────────────────────────
_CONTEXTUALISE_SYSTEM = (
    "Given a chat history with a child (aged 7-14), make their latest question clearer if needed.\n"
    "\n"
    "CHILD-FRIENDLY RULES:\n"
    "- NEVER change personal questions like 'What is my name?' or 'I am [name]' — keep exactly as asked\n"
    "- If they say 'that thing', 'it', 'what we talked about', add the specific topic from history\n"
    "- If the question is already clear, don't change it\n"
    "- Keep language simple and friendly for children\n"
    "- Don't make questions sound too formal or adult-like\n"
    "\n"
    "Examples for kids:\n"
    "- 'What is my name?' → 'What is my name?' (don't change personal questions!)\n"
    "- 'Tell me more about that' → 'Tell me more about earthquakes' (if previous topic was earthquakes)\n"
    "- 'What happens in it?' → 'What happens in a tsunami?' (if discussing tsunamis)\n"
    "- 'Can you repeat that?' → 'Can you repeat that information about emergency kits?'\n"
    "\n"
    "Return ONLY the (possibly improved) question, nothing else."
)


def _lc_messages_to_ollama(messages: list) -> list[dict]:
    """
    Convert a list of LangChain HumanMessage / AIMessage objects into the
    Ollama messages format  [{"role": "user"|"assistant", "content": "..."}].
    """
    ollama_msgs = []
    for m in messages:
        if isinstance(m, HumanMessage):
            ollama_msgs.append({"role": "user", "content": m.content})
        elif isinstance(m, AIMessage):
            ollama_msgs.append({"role": "assistant", "content": m.content})
        # skip SystemMessage or anything unexpected
    return ollama_msgs


def _call_ollama_contextualise(chat_history: list, question: str) -> str:
    """
    Build an Ollama Cloud request that includes the full chat history so the
    model can resolve references in the child's latest question.
    """
    headers = {"Content-Type": "application/json"}
    if OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

    # Start with the system prompt, then the conversation history, then the new question
    messages = [{"role": "system", "content": _CONTEXTUALISE_SYSTEM}]
    messages.extend(_lc_messages_to_ollama(chat_history))
    messages.append({"role": "user", "content": question})

    body = {
        "model": OLLAMA_MODEL,
        "stream": False,
        # No "format": "json" here — we want a plain text response (the reworded question)
        "messages": messages,
        "options": {"temperature": 0.0},   # deterministic — same as the original
    }

    resp = requests.post(OLLAMA_URL, json=body, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()["message"]["content"].strip()


# ── Drop-in replacement for the old LangChain chain ──────────────────────────

class _ContextualiseChain:
    """
    Mimics the .invoke() interface of the old LangChain chain so that
    rag_chat.py needs zero changes:

        contextualise_chain.invoke({
            "chat_history": messages,   # list of LangChain messages
            "input": query_input.question,
        }) -> str
    """

    def invoke(self, inputs: dict) -> str:
        chat_history = inputs.get("chat_history", [])
        question     = inputs.get("input", "")

        if not question:
            return question

        try:
            result = _call_ollama_contextualise(chat_history, question)
            logger.debug(f"Contextualised '{question}' → '{result}'")
            return result
        except Exception as e:
            # Graceful degradation: return the original question unchanged
            logger.warning(
                f"Contextualisation failed, using original question. Error: {e}"
            )
            return question

    # Allow the chain to be used with .with_config() just like a LangChain runnable
    def with_config(self, **_kwargs):
        return self


contextualise_chain = _ContextualiseChain()