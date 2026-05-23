# app/services/ai.py
import json
import os
from typing import List

from langchain_ollama import ChatOllama

from app.schemas.skill import DiaryEntryResponse, SupportiveTipsResponse

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_llm(temperature: float = 0.7) -> ChatOllama:
    """Return a configured ChatOllama instance.

    For cloud.ollama.com set OLLAMA_API_KEY and OLLAMA_MODEL in .env.
    For a local instance set OLLAMA_BASE_URL (default http://localhost:11434)
    and leave OLLAMA_API_KEY empty.
    """
    kwargs: dict = dict(
        model=os.getenv("OLLAMA_MODEL", "gemma3:4b"),
        temperature=temperature,
    )
    api_key = os.getenv("OLLAMA_API_KEY", "")
    base_url = os.getenv("OLLAMA_BASE_URL", "")
    if api_key:
        kwargs["api_key"] = api_key          # cloud.ollama.com
    if base_url:
        kwargs["base_url"] = base_url        # local / self-hosted override
    return ChatOllama(**kwargs)


# ---------------------------------------------------------------------------
# Public functions
# ---------------------------------------------------------------------------


async def get_supportive_tips(
    entries: List[DiaryEntryResponse],
) -> SupportiveTipsResponse:
    """Generate AI supportive tips based on diary entries."""

    llm = _make_llm(temperature=0.7)

    diary_context = ""
    for entry in entries:
        mood_text = f"(mood: {entry.mood}/5)" if entry.mood else ""
        diary_context += f"- {entry.date}: {entry.text} {mood_text}\n"

    prompt = f"""
    As a child development expert, analyze these diary entries from a child and provide supportive parenting tips:

    Recent diary entries:
    {diary_context}

    Please provide a single, concise paragraph (2-3 sentences) with practical parenting advice that:
    1. Acknowledges the child's emotional experiences
    2. Suggests specific supportive actions parents can take
    3. Focuses on building emotional intelligence and resilience

    Keep the advice positive, actionable, and focused on the parent-child relationship.
    """

    try:
        response = await llm.ainvoke(prompt)
        tip = response.content.strip()
        return SupportiveTipsResponse(tip=tip)

    except Exception:
        return SupportiveTipsResponse(
            tip="Encourage quality time, active listening, and emotional support. Create a safe space for your child to express their feelings and celebrate their daily achievements, both big and small."
        )


async def analyze_diary_entry(entry_text: str) -> tuple[str, str, str]:
    """Analyze a diary entry and return mood, emoji, and AI response."""

    llm = _make_llm(temperature=0.7)

    prompt = f"""
    Analyze this child's diary entry and respond with exactly three items separated by |:

    Diary entry: "{entry_text}"

    Provide:
    1. A mood word (one word like: Happy, Sad, Excited, Worried, Proud, Frustrated, Content, Anxious, etc.)
    2. A single emoji that matches the mood
    3. A supportive, encouraging response (1-2 sentences) that acknowledges their feelings and provides gentle guidance

    Format: mood|emoji|response

    Example: Happy|😊|You're doing great! Keep up the positive attitude.
    """

    try:
        response = await llm.ainvoke(prompt)
        content = response.content.strip()

        parts = content.split("|")
        if len(parts) >= 3:
            mood = parts[0].strip()
            emoji = parts[1].strip()
            ai_response = parts[2].strip()
        else:
            mood = "Content"
            emoji = "😊"
            ai_response = "Thank you for sharing your thoughts. Keep expressing yourself!"

        return mood, emoji, ai_response

    except Exception:
        return (
            "Content",
            "😊",
            "Thank you for sharing your thoughts. Keep expressing yourself!",
        )


async def generate_problem_solving_questions() -> List[dict]:
    """Generate 6 daily problem-solving questions for kids."""

    llm = _make_llm(temperature=0.8)

    prompt = """
    Generate 6 age-appropriate problem-solving questions for children aged 8-14. Each question should:
    1. Present a real-life scenario they might encounter
    2. Have 4 multiple choice options
    3. Test logical thinking, safety awareness, or ethical decision-making
    4. Be engaging and relatable

    Format each question as JSON:
    {
        "question": "What should you do if...",
        "options": [
            {"text": "Option A", "correct": false},
            {"text": "Option B", "correct": true},
            {"text": "Option C", "correct": false},
            {"text": "Option D", "correct": false}
        ]
    }

    Provide all 6 questions in a JSON array. Return only valid JSON with no extra text.
    """

    try:
        response = await llm.ainvoke(prompt)
        content = response.content.strip()

        # Strip markdown code fences if the model adds them
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
            content = content.strip()

        questions = json.loads(content)
        return questions if isinstance(questions, list) else []

    except Exception:
        return [
            {
                "question": "What should you do if you see someone being bullied at school?",
                "options": [
                    {"text": "Ignore it and walk away", "correct": False},
                    {"text": "Join in the bullying", "correct": False},
                    {"text": "Tell a teacher or trusted adult", "correct": True},
                    {"text": "Record it on your phone", "correct": False},
                ],
            },
            {
                "question": "If you're home alone and someone knocks on the door, you should:",
                "options": [
                    {"text": "Open the door immediately", "correct": False},
                    {"text": "Don't answer and call a parent", "correct": True},
                    {"text": "Hide under your bed", "correct": False},
                    {"text": "Shout at them to go away", "correct": False},
                ],
            },
        ]


class ChatbotService:
    """Service for AI chatbot interactions."""

    def __init__(self):
        self.llm = _make_llm(temperature=0.7)

    async def get_chat_response(
        self,
        message: str,
        context: str = None,
        user_age: int = None,
        user_name: str = None,
    ) -> str:
        """Get general AI chat response."""

        age_context = (
            f"The user is {user_age} years old" if user_age else "The user is a child"
        )
        name_context = f"The user's name is {user_name}" if user_name else ""
        context_info = f"Context: {context}" if context else ""

        prompt = f"""
        You are a helpful, encouraging AI assistant for a life skills learning app for children aged 8-14.
        {age_context}. {name_context}. {context_info}

        User message: "{message}"

        Please provide a helpful, age-appropriate response that:
        1. Is encouraging and positive
        2. Relates to life skills learning when appropriate
        3. Uses simple, clear language
        4. Is safe and appropriate for children
        5. Keeps responses concise (1-3 sentences)

        If the user asks about inappropriate topics, gently redirect them to life skills topics.
        """

        try:
            response = await self.llm.ainvoke(prompt)
            return response.content.strip()
        except Exception:
            return "I'm here to help you learn and grow! What would you like to know about safety, money, or problem-solving?"

    async def get_safety_comic_response(
        self, message: str, user_age: int = None, user_name: str = None
    ) -> str:
        """Get AI response specifically for safety comic discussions."""

        age_context = (
            f"The user is {user_age} years old" if user_age else "The user is a child"
        )
        name_context = f"The user's name is {user_name}" if user_name else ""

        prompt = f"""
        You are a safety education AI assistant helping children understand safety concepts from comics.
        {age_context}. {name_context}

        User message about safety comic: "{message}"

        Please provide a response that:
        1. Relates to safety education and comic content
        2. Explains safety concepts in simple terms
        3. Encourages safe behavior
        4. Is engaging and comic-themed
        5. Asks follow-up questions to keep learning active

        Keep responses concise (1-3 sentences) and always emphasize safety.
        """

        try:
            response = await self.llm.ainvoke(prompt)
            return response.content.strip()
        except Exception:
            return "Great question about safety! Remember, the most important thing is to stay safe and tell a trusted adult if you need help."

    async def get_encouragement(
        self,
        user_name: str = None,
        user_age: int = None,
        user_points: int = 0,
        user_badges_count: int = 0,
    ) -> str:
        """Get encouraging message for the user."""

        name_context = f"The user's name is {user_name}" if user_name else "You"
        age_context = f"who is {user_age} years old" if user_age else ""

        prompt = f"""
        Generate an encouraging message for a child learning life skills.
        {name_context} {age_context} has earned {user_points} points and {user_badges_count} badges in the app.

        Create a positive, motivating message that:
        1. Celebrates their progress
        2. Encourages continued learning
        3. Is age-appropriate and uplifting
        4. Mentions their achievements if they have any
        5. Is 1-2 sentences long

        Make it personal and encouraging!
        """

        try:
            response = await self.llm.ainvoke(prompt)
            return response.content.strip()
        except Exception:
            if user_badges_count > 0:
                return f"Great job earning {user_badges_count} badges! Keep up the amazing work learning new life skills!"
            else:
                return "You're doing great! Every step you take in learning life skills makes you stronger and smarter!"