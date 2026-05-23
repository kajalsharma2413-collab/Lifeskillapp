# app/api/dependencies/ai/rag_chatbot/tools.py
"""
FIXED: Replaced OllamaEmbeddings (which hardcodes localhost:11434) with a
direct `requests` call to the Ollama Cloud embeddings endpoint — same pattern
as shared.py, diary_summarizer.py, and ollama_agent.py.

Public interface is UNCHANGED:
    rag_search_tool  — @tool, takes {"query": str} -> str
    web_search_tool  — @tool, takes {"query": str} -> str
"""

import logging
import os

import requests
from dotenv import load_dotenv
from langchain_core.tools import tool
from langchain_pinecone import PineconeVectorStore
from langchain_tavily import TavilySearch
from pinecone import Pinecone

load_dotenv()
logger = logging.getLogger(__name__)

# ── Ollama Cloud config ───────────────────────────────────────────────────────
OLLAMA_API_KEY       = os.getenv("OLLAMA_API_KEY", "").strip()
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "nomic-embed-text")
OLLAMA_HOST          = os.getenv("OLLAMA_HOST", "").strip().rstrip("/")
OLLAMA_EMBED_URL     = (
    f"{OLLAMA_HOST}/api/embed" if OLLAMA_HOST else "https://ollama.com/api/embed"
)

# ── Tavily (unchanged) ────────────────────────────────────────────────────────
tavily = TavilySearch(
    max_results=3,
    topic="general",
    exclude_domains=["reddit.com", "4chan.org"],
)

# ── Pinecone client (unchanged) ───────────────────────────────────────────────
pinecone_api_key = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=pinecone_api_key)


# ── Direct Ollama embeddings (replaces OllamaEmbeddings) ─────────────────────

class _OllamaEmbedder:
    """
    Drop-in for OllamaEmbeddings — implements embed_query() and embed_documents()
    using the Ollama Cloud /api/embed endpoint directly via `requests`.
    Compatible with langchain_pinecone.PineconeVectorStore.
    """

    def embed_query(self, text: str) -> list[float]:
        return self._embed([text])[0]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return self._embed(texts)

    def _embed(self, texts: list[str]) -> list[list[float]]:
        headers = {"Content-Type": "application/json"}
        if OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

        body = {
            "model": OLLAMA_EMBEDDING_MODEL,
            "input": texts,
        }

        try:
            resp = requests.post(OLLAMA_EMBED_URL, json=body, headers=headers, timeout=30)
        except requests.Timeout:
            raise RuntimeError("Ollama embed API timed out")
        except requests.ConnectionError as e:
            raise RuntimeError(f"Ollama embed API connection failed: {e}")

        if resp.status_code == 401:
            raise RuntimeError("Ollama embed 401: check OLLAMA_API_KEY")
        if resp.status_code != 200:
            raise RuntimeError(f"Ollama embed HTTP {resp.status_code}: {resp.text[:300]}")

        data = resp.json()
        # Ollama /api/embed returns {"embeddings": [[...]]}
        embeddings = data.get("embeddings", [])
        if not embeddings:
            raise RuntimeError(f"Ollama embed returned no embeddings: {data}")
        return embeddings


# ── Global retriever (lazy-init, unchanged logic) ─────────────────────────────
_retriever = None


def get_retriever():
    global _retriever
    if _retriever is None:
        try:
            embedding = _OllamaEmbedder()
            docsearch = PineconeVectorStore.from_existing_index(
                index_name="rag-chatbot",
                embedding=embedding,
            )
            _retriever = docsearch.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 4},
            )
            logger.info("Pinecone retriever initialised with Ollama Cloud embeddings")
        except Exception as e:
            logger.error(f"Failed to initialise retriever: {e}")
            raise
    return _retriever


# ── Tools (UNCHANGED interface) ───────────────────────────────────────────────

@tool
def web_search_tool(query: str) -> str:
    """Search for up-to-date, child-appropriate information using Tavily"""
    try:
        logger.info(f"Web searching for: {query}")
        result = tavily.invoke({"query": f"child-friendly {query}"})

        if isinstance(result, dict) and "results" in result:
            formatted_results = []
            for item in result["results"][:3]:
                title   = item.get("title", "No title")
                content = item.get("content", "No content")[:500]
                url     = item.get("url", "")
                if not _contains_inappropriate_content(content):
                    formatted_results.append(
                        f"Title: {title}\nContent: {content}\nSource: {url}"
                    )

            if formatted_results:
                logger.info(f"Found {len(formatted_results)} appropriate web results")
                return "\n\n".join(formatted_results)
            return "No appropriate results found for children"
        return "No web results found"

    except Exception as e:
        logger.error(f"Web search error: {e}")
        return "Sorry, I couldn't search the web right now. Please try again later."


@tool
def rag_search_tool(query: str) -> str:
    """Search educational comics about natural disasters (Top-4 most relevant chunks)"""
    try:
        logger.info(f"RAG searching for: {query}")
        retriever = get_retriever()
        docs = retriever.invoke(query)

        if docs:
            combined_content = []
            for doc in docs:
                content = doc.page_content
                if hasattr(doc, "metadata") and doc.metadata:
                    source = doc.metadata.get("source", "")
                    if source:
                        content += f"\n(Source: {source})"
                combined_content.append(content)
            result = "\n\n---\n\n".join(combined_content)
            logger.info(f"Found {len(docs)} RAG results")
            return result

        logger.info("No RAG results found")
        return ""

    except Exception as e:
        logger.error(f"RAG search error: {e}")
        return f"RAG_ERROR: Could not access educational content - {str(e)}"


def _contains_inappropriate_content(content: str) -> bool:
    """Enhanced filter for child-inappropriate content"""
    inappropriate_keywords = [
        "violence", "blood", "death", "kill", "murder", "war", "weapon",
        "terrorist", "bomb", "attack", "shooting", "stabbing", "abuse",
        "adult content", "explicit", "sexual", "pornography", "nude",
        "graphic", "disturbing", "horrific", "gruesome", "traumatic",
        "nightmare", "scary images", "horror", "profanity", "curse",
        "swear", "offensive language", "body count", "casualties",
        "victims died", "massive destruction", "devastation", "apocalypse",
        "end of world",
    ]
    content_lower = content.lower()
    return any(keyword in content_lower for keyword in inappropriate_keywords)
