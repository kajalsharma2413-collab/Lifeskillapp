"""
generator.py — SmartQuestionGenerator

FIXED: Replaced ChatOllama (which hardcoded localhost:11434) with direct
`requests` calls to the Ollama Cloud API, matching the pattern used by
ollama_agent.py and diary_summarizer.py.

The LangGraph state-machine (generate → validate → fix → fallback) is kept
exactly as before; only the LLM call inside _generate_node is changed.
"""

import json
import logging
import os
import random
import re
from typing import Annotated

import requests
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

from .models import GeneratedQuestion

logger = logging.getLogger(__name__)

# ── Ollama Cloud config ───────────────────────────────────────────────────────
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")
OLLAMA_MODEL   = os.getenv("OLLAMA_MODEL", "gemma4:31b-cloud")
OLLAMA_HOST    = os.getenv("OLLAMA_HOST", "").rstrip("/")
OLLAMA_URL     = f"{OLLAMA_HOST}/api/chat" if OLLAMA_HOST else "https://ollama.com/api/chat"


def _call_ollama(system_prompt: str, user_prompt: str, temperature: float = 0.8) -> str:
    """
    Direct HTTP call to the Ollama Cloud API.
    Returns the raw text content of the model's reply.
    """
    headers = {"Content-Type": "application/json"}
    if OLLAMA_API_KEY:
        headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

    body = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": "json",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        "options": {"temperature": temperature},
    }

    resp = requests.post(OLLAMA_URL, json=body, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()["message"]["content"]


def _parse_json(raw: str) -> dict:
    """
    4-layer JSON parsing with fallbacks (same pattern as ollama_agent.py):
      1. Direct parse
      2. Strip markdown fences then parse
      3. Regex-extract first {...} block then parse
      4. Fix common escape issues then parse
    """
    # 1. Direct
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # 2. Strip fences
    cleaned = re.sub(r"```(?:json)?", "", raw).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # 3. Extract first JSON object
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # 4. Fix escape issues
    try:
        return json.loads(cleaned.replace("\\'", "'").replace('\\"', '"'))
    except json.JSONDecodeError as e:
        raise ValueError(f"Could not parse JSON from model response: {e}\nRaw: {raw[:300]}")


# ── Pydantic model for structured validation ──────────────────────────────────

class QuestionOutput(BaseModel):
    """Structured output for question generation with flexible validation."""

    question: str = Field(min_length=50, description="The main question text")
    option_a: str = Field(min_length=10, description="First option - should be descriptive")
    option_b: str = Field(min_length=10, description="Second option - should be descriptive")
    option_c: str = Field(min_length=10, description="Third option - should be descriptive")
    option_d: str = Field(min_length=10, description="Fourth option - should be descriptive")
    correct_answer: str = Field(pattern="^[ABCD]$", description="Must be A, B, C, or D")
    explanation: str = Field(min_length=100, description="Detailed explanation")


# ── LangGraph state ───────────────────────────────────────────────────────────

class QuestionState(TypedDict):
    """State for the question generation graph."""

    user_id: str
    level: str
    previous_questions: list[str]
    attempt: int
    max_attempts: int
    generated_question: GeneratedQuestion | None
    error_message: str
    is_valid: bool
    messages: Annotated[list, add_messages]


# ── System prompt shared by generate and fix nodes ────────────────────────────

_SYSTEM_PROMPT = (
    "You are an expert educational content creator for children aged 7-14. "
    "Always respond with pure JSON only — no markdown, no explanation, no code fences."
)


class SmartQuestionGenerator:
    """Generates thought-provoking questions for children aged 7-14."""

    def __init__(self, api_key: str | None = None):
        """
        api_key is accepted but ignored — Ollama is configured via
        OLLAMA_HOST, OLLAMA_MODEL, and OLLAMA_API_KEY environment variables.
        """
        try:
            self.workflow = self._build_workflow()
            self.app = self.workflow.compile()
            logger.info(
                f"SmartQuestionGenerator initialised — model: {OLLAMA_MODEL}, url: {OLLAMA_URL}"
            )
        except Exception as e:
            logger.error(f"Failed to initialise SmartQuestionGenerator: {e}")
            raise RuntimeError(f"Generator initialisation failed: {e}")

    # ── Workflow construction ─────────────────────────────────────────────────

    def _build_workflow(self) -> StateGraph:
        workflow = StateGraph(QuestionState)

        workflow.add_node("generate",  self._generate_node)
        workflow.add_node("validate",  self._validate_node)
        workflow.add_node("fix",       self._fix_node)
        workflow.add_node("fallback",  self._fallback_node)

        workflow.add_edge(START, "generate")
        workflow.add_edge("generate", "validate")

        workflow.add_conditional_edges(
            "validate",
            self._should_retry,
            {"success": END, "retry": "fix", "fallback": "fallback"},
        )

        workflow.add_edge("fix", "generate")
        workflow.add_edge("fallback", END)

        return workflow

    # ── Topic helpers ─────────────────────────────────────────────────────────

    def _get_diverse_topics(self) -> str:
        topics = [
            "nature and animals", "space and planets", "weather and climate",
            "human body and health", "plants and trees", "oceans and marine life",
            "technology and inventions", "mathematics and patterns",
            "energy and forces", "light and colors", "sound and music",
            "food and nutrition", "geography and earth", "history and discoveries",
            "psychology and behavior", "chemistry and materials",
            "physics and motion", "biology and life",
            "ecosystems and environment", "transportation and movement",
        ]
        return random.choice(topics)

    # ── Node: generate ────────────────────────────────────────────────────────

    def _generate_node(self, state: QuestionState) -> QuestionState:
        """Call Ollama Cloud API to generate a question."""
        updated = state.copy()
        topic = self._get_diverse_topics()

        level_context = {
            "beginner": "children aged 7-9. Use simple words, basic cause-and-effect, everyday objects.",
            "medium":   "children aged 10-12. Include scientific concepts explained simply.",
            "advanced": "children aged 13-14. Include deeper scientific or mathematical reasoning.",
        }.get(state["level"], "children aged 10-12.")

        previous_note = ""
        if state["previous_questions"]:
            samples = state["previous_questions"][-5:]
            previous_note = (
                f"\n\nAvoid questions similar to these recent ones:\n"
                + "\n".join(f"- {q}" for q in samples)
            )

        user_prompt = f"""Generate a unique, thought-provoking multiple-choice question about "{topic}" for {level_context}
{previous_note}

Return ONLY a JSON object with exactly these keys:
{{
  "question": "A detailed, curiosity-sparking question (at least 50 characters)",
  "option_a": "First option (at least 10 characters)",
  "option_b": "Second option (at least 10 characters)",
  "option_c": "Third option (at least 10 characters)",
  "option_d": "Fourth option (at least 10 characters)",
  "correct_answer": "A or B or C or D",
  "explanation": "A rich, educational explanation of at least 100 characters"
}}"""

        try:
            raw = _call_ollama(_SYSTEM_PROMPT, user_prompt, temperature=0.8)
            data = _parse_json(raw)
            q = QuestionOutput(**data)           # validates field lengths / correct_answer format
            updated["generated_question"] = GeneratedQuestion(
                question=q.question,
                option_a=q.option_a,
                option_b=q.option_b,
                option_c=q.option_c,
                option_d=q.option_d,
                correct_answer=q.correct_answer,
                explanation=q.explanation,
            )
            updated["is_valid"] = True
            updated["error_message"] = ""
        except Exception as e:
            logger.warning(f"_generate_node failed (attempt {state['attempt']}): {e}")
            updated["generated_question"] = None
            updated["is_valid"] = False
            updated["error_message"] = str(e)
            updated["attempt"] = state["attempt"] + 1

        return updated

    # ── Node: validate ────────────────────────────────────────────────────────

    def _validate_node(self, state: QuestionState) -> QuestionState:
        """Validate the generated question."""
        updated = state.copy()
        q = state.get("generated_question")
        if q and self.validate_question(q):
            updated["is_valid"] = True
        else:
            updated["is_valid"] = False
            updated["attempt"] = state["attempt"] + 1
        return updated

    # ── Node: fix ─────────────────────────────────────────────────────────────

    def _fix_node(self, state: QuestionState) -> QuestionState:
        """Ask the model to fix the previous broken output."""
        updated = state.copy()

        fix_prompt = (
            f"The previous question generation failed with: {state['error_message']}\n\n"
            "Please generate a completely new question. "
            "Return ONLY valid JSON with keys: question, option_a, option_b, option_c, "
            "option_d, correct_answer, explanation."
        )

        try:
            raw = _call_ollama(_SYSTEM_PROMPT, fix_prompt, temperature=0.5)
            data = _parse_json(raw)
            q = QuestionOutput(**data)
            updated["generated_question"] = GeneratedQuestion(
                question=q.question,
                option_a=q.option_a,
                option_b=q.option_b,
                option_c=q.option_c,
                option_d=q.option_d,
                correct_answer=q.correct_answer,
                explanation=q.explanation,
            )
            updated["is_valid"] = True
            updated["error_message"] = ""
        except Exception as e:
            logger.warning(f"_fix_node failed: {e}")
            updated["is_valid"] = False
            updated["error_message"] = str(e)
            updated["attempt"] = state["attempt"] + 1

        return updated

    # ── Node: fallback ────────────────────────────────────────────────────────

    def _fallback_node(self, state: QuestionState) -> QuestionState:
        """Return a hardcoded fallback question when all AI attempts fail."""
        updated = state.copy()

        fallback_pool = {
            "beginner": [
                {
                    "question": "Why do leaves change color in autumn? What is happening inside the leaf?",
                    "option_a": "Leaves get painted by the cold weather turning them orange and red",
                    "option_b": "The green chlorophyll breaks down, revealing hidden yellow and red colors",
                    "option_c": "Trees pour colored water into their leaves before dropping them",
                    "option_d": "Leaves change color to attract birds to eat them and spread seeds",
                    "correct_answer": "B",
                    "explanation": "Leaves contain green chlorophyll that hides other colors during summer. In autumn, trees stop making chlorophyll, so it breaks down and the hidden yellows, oranges, and reds are revealed. It's like the green was a curtain hiding a colorful painting underneath!",
                },
            ],
            "medium": [
                {
                    "question": "Scientists recently discovered that some trees can 'talk' to each other through underground networks. How do you think they communicate?",
                    "option_a": "Trees make very quiet sounds through their roots",
                    "option_b": "Trees send chemical signals through fungal networks connecting their roots",
                    "option_c": "Trees use electrical signals like our nervous system",
                    "option_d": "Trees communicate by releasing specific smells into the air",
                    "correct_answer": "B",
                    "explanation": "Trees connect through fungal networks called mycorrhizae. Through these threads, trees share nutrients and warn each other about insect attacks. A mother tree can even recognise her own seedlings and send them extra nutrients — a forest-wide family chat happening underground!",
                },
            ],
            "advanced": [
                {
                    "question": "If you traveled at 99.9% the speed of light to a star 10 light-years away and back, how much time would pass on Earth while you experienced only 2 years?",
                    "option_a": "About 20 years would pass on Earth",
                    "option_b": "About 45 years would pass on Earth",
                    "option_c": "About 140 years would pass on Earth",
                    "option_d": "Time would pass the same for both you and Earth",
                    "correct_answer": "C",
                    "explanation": "This is time dilation from Einstein's relativity. At 99.9% light speed, time moves ~22× slower for you. The round trip takes ~20 light-years but relativistic effects stretch the Earth clock to roughly 140 years. You'd return to find everyone you knew had aged far more than you!",
                },
            ],
        }

        level_fallbacks = fallback_pool.get(state["level"], fallback_pool["medium"])
        fallback = random.choice(level_fallbacks)

        try:
            updated["generated_question"] = GeneratedQuestion(**fallback)
            updated["is_valid"] = True
        except Exception as e:
            logger.error(f"_fallback_node failed: {e}")

        return updated

    # ── Routing helper ────────────────────────────────────────────────────────

    def _should_retry(self, state: QuestionState) -> str:
        if state["is_valid"]:
            return "success"
        elif state["attempt"] >= state["max_attempts"]:
            return "fallback"
        return "retry"

    # ── Public API ────────────────────────────────────────────────────────────

    def generate_question(
        self, user_id: str, level: str, previous_questions: list[str]
    ) -> GeneratedQuestion:
        """Generate a unique, age-appropriate question using the LangGraph workflow."""
        if not user_id or not isinstance(user_id, str):
            raise ValueError("user_id must be a non-empty string")
        if level not in ["beginner", "medium", "advanced"]:
            logger.warning(f"Unknown level '{level}', defaulting to 'medium'")
            level = "medium"
        if previous_questions is None:
            previous_questions = []

        initial_state = QuestionState(
            user_id=user_id,
            level=level,
            previous_questions=previous_questions,
            attempt=1,
            max_attempts=4,
            generated_question=None,
            error_message="",
            is_valid=False,
            messages=[],
        )

        try:
            final_state = self.app.invoke(initial_state)
            if final_state.get("generated_question"):
                logger.info(
                    f"Question generated for user {user_id} "
                    f"after {final_state.get('attempt', '?')} attempt(s)"
                )
                return final_state["generated_question"]
            raise RuntimeError("Workflow completed but no question produced")

        except Exception as e:
            logger.error(f"LangGraph workflow error for user {user_id}: {e}")
            # Emergency hardcoded fallback
            emergency = {
                "question": "What would happen if Earth suddenly stopped spinning for just one second?",
                "option_a": "Nothing would change because one second is too short",
                "option_b": "Everything would fly eastward at incredible speeds",
                "option_c": "All the water in oceans would immediately freeze",
                "option_d": "Gravity would become twice as strong everywhere",
                "correct_answer": "B",
                "explanation": "If Earth stopped spinning, everything on the surface would keep moving eastward at ~1,000 mph (Earth's rotational speed at the equator). It's like being in a car that suddenly stops — you keep moving forward. This is why our planet spinning so fast is both amazing and something we never notice!",
            }
            try:
                q = GeneratedQuestion(**emergency)
                logger.info(f"Used emergency fallback for user {user_id}")
                return q
            except Exception as fe:
                raise RuntimeError(f"Complete failure to generate question: {e}") from fe

    def validate_question(self, question: GeneratedQuestion) -> bool:
        """Validate a question for educational quality."""
        try:
            return (
                question is not None
                and len(question.question.strip()) >= 50
                and question.correct_answer in ["A", "B", "C", "D"]
                and len(question.explanation.strip()) >= 100
                and all(
                    len(opt.strip()) >= 10
                    for opt in [
                        question.option_a,
                        question.option_b,
                        question.option_c,
                        question.option_d,
                    ]
                )
            )
        except Exception as e:
            logger.error(f"Error validating question: {e}")
            return False