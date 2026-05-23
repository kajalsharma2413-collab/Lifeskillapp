# app/api/dependencies/ai/rag_chatbot/nodes.py
"""
LangGraph nodes for the children's educational RAG chatbot (ages 7-14).
Topics: life skills, financial literacy, natural disaster safety (earthquakes,
floods, hurricanes, heatwaves, blizzards, wildfires, tsunamis, volcanoes).
Inappropriate or adult content is blocked — child is redirected to a trusted adult.
"""

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from .shared import (
    AgentState,
    RagJudge,
    RouteDecision,
    answer_llm,
    judge_llm,
    router_llm,
)
from .tools import rag_search_tool, web_search_tool


# ═══════════════════════════════════════════════════════════════════════════════
# NODE 1 — ROUTER
# ═══════════════════════════════════════════════════════════════════════════════

_ROUTER_SYSTEM = """\
You are a router for a children's educational chatbot (ages 7-14). Your only job is to
choose ONE routing label for the child's question and return it as JSON.

ALLOWED TOPICS for this chatbot:
• Life skills: money/saving/budgeting, communication, problem-solving, manners, hygiene
• Natural disaster safety: earthquakes, floods, hurricanes, tornadoes, heatwaves, blizzards,
  wildfires, tsunamis, volcanoes — causes, safety tips, emergency kits, evacuation
• Comic characters: Ollie, Candy, Ping, Eddy, Snake, Dog, Grand Master Fu (disaster safety comics)
• General child-friendly knowledge: science, animals, space, plants, simple maths, geography

ROUTING RULES — pick exactly one:

"end"    → Greetings, thank-you, goodbyes, "what is your name", compliments.
           Also use "end" for ANY inappropriate, adult, violent, romantic, or
           18+ question. Fill "reply" with a kind redirect message.

"rag"    → Question is about natural disaster safety OR the comic characters.

"web"    → Question needs current/recent data: latest news about a disaster,
           "is my city safe", specific statistics, recent events.

"answer" → General child-friendly knowledge or life-skills question that does
           NOT need the disaster comic database or live web data.

You MUST reply with ONLY this JSON and nothing else — no explanation outside the JSON:
{"route": "<end|rag|web|answer>", "reasoning": "<one sentence>", "reply": "<only if route=end>"}
"""

def router_node(state: AgentState) -> AgentState:
    original_q       = state.get("original_question", "")
    contextualized_q = state.get("contextualized_question", original_q)

    user_content = (
        f'ORIGINAL QUESTION: "{original_q}"\n'
        f'CLARIFIED QUESTION: "{contextualized_q}"\n\n'
        'Return ONLY the JSON routing decision.'
    )

    messages = [
        SystemMessage(content=_ROUTER_SYSTEM),
        HumanMessage(content=user_content),
    ]

    result: RouteDecision = router_llm.invoke(messages)
    out = {**state, "route": result.route, "routing_reasoning": result.reasoning}

    if result.route == "end":
        reply = (
            result.reply
            or "Hi there! I'm here to help you learn about staying safe and building great life skills. "
               "What would you like to explore today?"
        )
        out["messages"] = state["messages"] + [AIMessage(content=reply)]

    return out


# ═══════════════════════════════════════════════════════════════════════════════
# NODE 2 — RAG LOOKUP
# ═══════════════════════════════════════════════════════════════════════════════

_JUDGE_SYSTEM = """\
You are checking whether information retrieved from educational disaster-safety comics
is enough to answer a child's question (ages 7-14).

The comics feature Ollie, Candy, Ping, Eddy, Snake, Dog, and Grand Master Fu teaching
disaster safety through adventures.

Reply with ONLY this JSON and nothing else:
{"sufficient": true, "reasoning": "<one sentence>"}
or
{"sufficient": false, "reasoning": "<one sentence why web search is needed>"}
"""

def rag_node(state: AgentState) -> AgentState:
    query = state.get("contextualized_question") or state.get("original_question", "")

    chunks = rag_search_tool.invoke({"query": query})

    judge_messages = [
        SystemMessage(content=_JUDGE_SYSTEM),
        HumanMessage(content=(
            f'Child question: "{query}"\n\n'
            f'Retrieved comic content:\n{chunks or "(nothing retrieved)"}\n\n'
            'Is this sufficient? Reply ONLY with JSON.'
        )),
    ]

    verdict: RagJudge = judge_llm.invoke(judge_messages)

    return {
        **state,
        "rag": chunks,
        "route": "answer" if verdict.sufficient else "web",
        "processing_notes": f"RAG judge: {verdict.reasoning}",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# NODE 3 — WEB SEARCH
# ═══════════════════════════════════════════════════════════════════════════════

def web_node(state: AgentState) -> AgentState:
    query = state.get("contextualized_question") or state.get("original_question", "")
    snippets = web_search_tool.invoke({"query": query})
    return {**state, "web": snippets, "route": "answer"}


# ═══════════════════════════════════════════════════════════════════════════════
# NODE 4 — ANSWER GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

_ANSWER_SYSTEM = """\
You are "Sakai", a friendly educational assistant for children aged 7-14.
You help them learn life skills (money, communication, problem-solving, manners)
and stay safe during natural disasters (earthquakes, floods, hurricanes, heatwaves,
blizzards, wildfires, tsunamis, tornadoes, volcanoes).

STRICT RULES:
1. SAFE TOPICS ONLY. If the child asks about anything violent, adult, romantic,
   scary beyond educational need, or 18+, respond ONLY with:
   "That's not something I can help with, but you can talk to a trusted adult
   or your parents about it! 😊 Want to learn something fun instead?"
   Do NOT answer the inappropriate question at all.

2. AGE-APPROPRIATE LANGUAGE. Simple, warm, encouraging. Short sentences for ages 7-9;
   slightly longer for ages 10-14. No jargon.

3. DISASTER SAFETY — focus on what TO DO, not on scary outcomes. Always include
   at least one practical tip. Make it feel empowering, not scary.

4. LIFE SKILLS — be practical and positive. Use relatable examples (pocket money,
   school situations, friendships).

5. COMIC CHARACTERS — if the answer involves Ollie, Candy, Ping, Eddy, Snake, Dog,
   or Grand Master Fu, mention them by name to make it fun.

6. End with one encouraging sentence or a curious follow-up question.

7. Keep answers concise: 3-5 sentences for simple questions, up to 8 for complex ones.
"""

def answer_node(state: AgentState) -> AgentState:
    original_q       = state.get("original_question", "")
    contextualized_q = state.get("contextualized_question", original_q)

    # Build context block
    ctx_parts = []
    if state.get("rag"):
        ctx_parts.append(
            "📚 Educational comic content (Ollie, Candy, Ping, Eddy, Snake, Dog, Grand Master Fu):\n"
            + state["rag"]
        )
    if state.get("web"):
        ctx_parts.append("🌐 Current information from the web:\n" + state["web"])

    context = "\n\n".join(ctx_parts) if ctx_parts else "No extra context — answer from general knowledge."

    clarification = (
        f'\n(Clarified understanding: "{contextualized_q}")'
        if contextualized_q and contextualized_q != original_q
        else ""
    )

    user_prompt = (
        f'Child\'s question: "{original_q}"{clarification}\n\n'
        f'{context}\n\n'
        'Give a helpful, child-friendly answer following all the rules in your instructions.'
    )

    messages = [
        SystemMessage(content=_ANSWER_SYSTEM),
        *state["messages"],
        HumanMessage(content=user_prompt),
    ]

    ans = answer_llm.invoke(messages).content
    return {**state, "messages": state["messages"] + [AIMessage(content=ans)]}
