from typing import Literal

from langgraph.graph import END, StateGraph

from .nodes import answer_node, rag_node, router_node, web_node
from .shared import AgentState


# ── Enhanced routing helpers ─────────────────────────────────────────────────
def from_router(st: AgentState) -> Literal["rag", "web", "answer", "end"]:
    """Route from router node - now includes direct web search option"""
    return st["route"]


def after_rag(st: AgentState) -> Literal["answer", "web"]:
    """After RAG: either sufficient to answer or needs web search"""
    return st["route"]


def after_web(_) -> Literal["answer"]:
    """After web search: always go to answer"""
    return "answer"


# ── Build enhanced graph ─────────────────────────────────────────────────────
g = StateGraph(AgentState)

# Add all nodes
g.add_node("router", router_node)
g.add_node("rag_lookup", rag_node)
g.add_node("web_search", web_node)
g.add_node("answer", answer_node)

# Set entry point
g.set_entry_point("router")

# Enhanced routing from router - now includes direct web search
g.add_conditional_edges(
    "router",
    from_router,
    {
        "rag": "rag_lookup",  # For disaster safety comic content
        "web": "web_search",  # Direct web search for current/location info
        "answer": "answer",  # Direct answer for general knowledge
        "end": END,  # Simple greetings/small talk
    },
)

# From RAG: either answer or fallback to web search
g.add_conditional_edges(
    "rag_lookup",
    after_rag,
    {
        "answer": "answer",  # RAG content is sufficient
        "web": "web_search",  # Need additional web info
    },
)

# Web search always goes to answer
g.add_edge("web_search", "answer")

# Answer always ends
g.add_edge("answer", END)

# Compile the agent
agent = g.compile()