"""Pydantic request/response schemas for the FastAPI layer."""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ── Chat ──────────────────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=2000, description="User message")
    user_id: str = Field(default="demo_user", description="User identifier")
    conversation_id: Optional[str] = Field(
        default=None, description="Conversation ID (auto-generated if omitted)"
    )

    model_config = {"json_schema_extra": {
        "example": {
            "message": "Can you check my current subscription plan?",
            "user_id": "user_001",
            "conversation_id": None,
        }
    }}


class ChatResponse(BaseModel):
    conversation_id: str
    user_id: str
    message: str
    response: str
    intent: str
    sub_intent: Optional[str] = None
    confidence: float
    escalated: bool
    ticket_number: Optional[str] = None
    action_result: Optional[dict] = None


# ── Tickets ───────────────────────────────────────────────────────────────────

class TicketOut(BaseModel):
    ticket_number: str
    user_id: str
    intent: Optional[str]
    escalation_reason: Optional[str]
    conversation_snippet: Optional[str]
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TicketsResponse(BaseModel):
    tickets: list[TicketOut]
    total: int


# ── Health ────────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    version: str
    database: str
    faiss_index: str
    groq_configured: bool


# ── Reset ─────────────────────────────────────────────────────────────────────

class ResetResponse(BaseModel):
    message: str
    conversations_deleted: int
