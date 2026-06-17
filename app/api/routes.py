"""FastAPI route handlers."""

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import (
    ChatRequest, ChatResponse,
    TicketsResponse, TicketOut,
    HealthResponse, ResetResponse,
)
from app.agent.graph import run_agent
from app.db.session import get_db
from app.db import queries as q
from app.db.models import Conversation
from app.rag.index import index_exists
from app.utils.config import get_settings
from app.utils.logging import get_logger

logger = get_logger("api.routes")
router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["System"])
def health_check(db: Session = Depends(get_db)):
    """Health check — verifies DB and FAISS index availability."""
    settings = get_settings()
    try:
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"

    return HealthResponse(
        status="ok",
        version="1.0.0",
        database=db_status,
        faiss_index="ready" if index_exists() else "not_built",
        groq_configured=bool(settings.groq_api_key),
    )


@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Process a user message through the LangGraph support agent.

    - Classifies intent (faq | action | escalate)
    - Routes to the appropriate node
    - Persists messages and tickets to SQLite
    - Returns a structured JSON response
    """
    settings = get_settings()
    settings.validate_api_key()

    conversation_id = request.conversation_id or str(uuid.uuid4())

    # Load conversation history for context
    history = q.get_conversation_history(db, conversation_id)

    logger.info(
        "Chat request received",
        user_id=request.user_id,
        conversation_id=conversation_id,
        message_preview=request.message[:60],
    )

    try:
        final_state = run_agent(
            user_message=request.message,
            user_id=request.user_id,
            conversation_id=conversation_id,
            db=db,
            history=history,
        )
    except Exception as e:
        logger.error("Agent run failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    return ChatResponse(
        conversation_id=conversation_id,
        user_id=request.user_id,
        message=request.message,
        response=final_state.get("final_response", "I'm sorry, something went wrong."),
        intent=final_state.get("intent", "unknown"),
        sub_intent=final_state.get("sub_intent"),
        confidence=final_state.get("confidence", 0.0),
        escalated=final_state.get("escalated", False),
        ticket_number=final_state.get("ticket_number"),
        action_result=final_state.get("action_result"),
    )


@router.get("/tickets", response_model=TicketsResponse, tags=["Admin"])
def list_tickets(db: Session = Depends(get_db)):
    """Return all escalated support tickets (admin view)."""
    tickets = q.get_all_tickets(db)
    return TicketsResponse(
        tickets=[TicketOut.model_validate(t) for t in tickets],
        total=len(tickets),
    )


@router.post("/reset", response_model=ResetResponse, tags=["System"])
def reset_conversations(db: Session = Depends(get_db)):
    """
    Delete all conversation history (for demo/testing).
    Does NOT delete users, subscriptions, or invoices.
    """
    count = db.query(Conversation).count()
    q.reset_all_conversations(db)
    logger.warning("All conversations reset", deleted=count)
    return ResetResponse(
        message="All conversation data has been cleared.",
        conversations_deleted=count,
    )
