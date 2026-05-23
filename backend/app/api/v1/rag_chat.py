import logging

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import AIMessage, HumanMessage

from app.api.dependencies.ai.rag_chatbot.db_utils import (
    get_chat_history,
    insert_chat_history,
)
from app.api.dependencies.ai.rag_chatbot.langchain_utils import contextualise_chain
from app.api.dependencies.ai.rag_chatbot.langgraph_agent import agent
from app.api.dependencies.ai.rag_chatbot.pydantic_models import (
    QueryInput,
    QueryResponse,
)
from app.api.dependencies.ai.rag_chatbot.utils import (
    append_message,
    get_or_create_session_id,
    history_to_lc_messages,
)
from app.api.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/rag_chat", tags=["rag_chat"])
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=QueryResponse)
async def chat(
    query_input: QueryInput,
    current_user: User = Depends(get_current_user),
):
    """
    Improved chat endpoint with better contextualization flow
    """
    session_id = get_or_create_session_id(query_input.session_id)

    try:
        # Get chat history and convert to LangChain messages
        chat_history = get_chat_history(session_id)
        messages = history_to_lc_messages(chat_history)

        # IMPROVED APPROACH: Pass both original and contextualized questions to LangGraph
        if messages:
            logger.info("Contextualizing question with chat history")
            contextualized_question = contextualise_chain.invoke(
                {
                    "chat_history": messages,
                    "input": query_input.question,
                }
            )
            logger.info(f"Original: {query_input.question}")
            logger.info(f"Contextualized: {contextualized_question}")

            # Add the original question to messages (for proper chat history)
            messages = append_message(
                messages, HumanMessage(content=query_input.question)
            )

            # Pass both questions to the agent state
            agent_input = {
                "messages": messages,
                "original_question": query_input.question,
                "contextualized_question": contextualized_question,
            }
        else:
            # No history, use original question
            logger.info("No chat history, using original question")
            messages = append_message(
                messages, HumanMessage(content=query_input.question)
            )
            agent_input = {
                "messages": messages,
                "original_question": query_input.question,
                "contextualized_question": query_input.question,
            }

        # Invoke the LangGraph agent with improved state
        result = agent.invoke(agent_input)

        # Get the last AI message
        last_message = next(
            (m for m in reversed(result["messages"]) if isinstance(m, AIMessage)), None
        )

        if last_message:
            answer = last_message.content
        else:
            answer = "I apologize, but I couldn't generate a response at this time."

        # Store the original question and answer
        insert_chat_history(session_id, query_input.question, answer)
        # logger.info(f"Session ID: {session_id}, AI Response: {answer[:100]}...")

        return QueryResponse(answer=answer, session_id=session_id)

    except Exception as e:
        logger.error(f"Error in chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")