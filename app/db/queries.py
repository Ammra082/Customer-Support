"""Database query helpers — all DB interactions go through here."""

import json
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.db.models import (
    User, Subscription, Invoice, Workspace,
    Conversation, Message, Ticket, ActionLog,
    TicketStatus, IntentType, MessageRole, PlanType,
)


# ── Ticket helpers ─────────────────────────────────────────────────────────────

def _next_ticket_number(db: Session) -> str:
    count = db.query(Ticket).count()
    return f"TKT-{datetime.utcnow().strftime('%Y%m%d')}-{count + 1:04d}"


def create_ticket(
    db: Session,
    user_id: str,
    conversation_id: Optional[str],
    intent: Optional[str],
    escalation_reason: str,
    conversation_snippet: str,
    priority: str = "medium",
) -> Ticket:
    ticket = Ticket(
        ticket_number=_next_ticket_number(db),
        conversation_id=conversation_id,
        user_id=user_id,
        intent=IntentType(intent) if intent in IntentType.__members__ else IntentType.unknown,
        escalation_reason=escalation_reason,
        conversation_snippet=conversation_snippet,
        status=TicketStatus.open,
        priority=priority,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    return ticket


def get_all_tickets(db: Session) -> list[Ticket]:
    return db.query(Ticket).order_by(Ticket.created_at.desc()).all()


def update_ticket_status(db: Session, ticket_number: str, status: str) -> Optional[Ticket]:
    ticket = db.query(Ticket).filter(Ticket.ticket_number == ticket_number).first()
    if ticket:
        ticket.status = TicketStatus(status)
        ticket.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(ticket)
    return ticket


# ── Conversation helpers ───────────────────────────────────────────────────────

def get_or_create_conversation(db: Session, conversation_id: str, user_id: str) -> Conversation:
    conv = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id
    ).first()
    if not conv:
        conv = Conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )
        db.add(conv)
        db.commit()
        db.refresh(conv)
    return conv


def add_message(
    db: Session,
    conversation_id: str,
    role: str,
    content: str,
    intent: Optional[str] = None,
    confidence: Optional[float] = None,
) -> Message:
    msg = Message(
        conversation_id=conversation_id,
        role=MessageRole(role),
        content=content,
        intent=IntentType(intent) if intent in IntentType.__members__ else None,
        confidence=confidence,
    )
    db.add(msg)
    # Update conversation last_updated
    conv = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id
    ).first()
    if conv:
        conv.last_updated = datetime.utcnow()
    db.commit()
    db.refresh(msg)
    return msg


def get_conversation_history(db: Session, conversation_id: str) -> list[dict]:
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
        .all()
    )
    return [
        {
            "role": m.role.value,
            "content": m.content,
            "intent": m.intent.value if m.intent else None,
            "confidence": m.confidence,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]


def mark_conversation_escalated(db: Session, conversation_id: str) -> None:
    conv = db.query(Conversation).filter(
        Conversation.conversation_id == conversation_id
    ).first()
    if conv:
        conv.is_escalated = True
        db.commit()


# ── Action log helpers ─────────────────────────────────────────────────────────

def log_action(
    db: Session,
    action_name: str,
    user_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
    parameters: Optional[dict] = None,
    result: Optional[dict] = None,
    success: bool = True,
    error_message: Optional[str] = None,
) -> ActionLog:
    log = ActionLog(
        conversation_id=conversation_id,
        user_id=user_id,
        action_name=action_name,
        parameters=json.dumps(parameters or {}),
        result=json.dumps(result or {}),
        success=success,
        error_message=error_message,
    )
    db.add(log)
    db.commit()
    db.refresh(log)
    return log


# ── User helpers ───────────────────────────────────────────────────────────────

def get_user(db: Session, user_id: str) -> Optional[User]:
    return db.query(User).filter(User.user_id == user_id).first()


def get_subscription(db: Session, user_id: str) -> Optional[Subscription]:
    return db.query(Subscription).filter(Subscription.user_id == user_id).first()


def get_workspace(db: Session, user_id: str) -> Optional[Workspace]:
    return db.query(Workspace).filter(Workspace.user_id == user_id).first()


def get_invoices(db: Session, user_id: str) -> list[Invoice]:
    sub = get_subscription(db, user_id)
    if not sub:
        return []
    return db.query(Invoice).filter(Invoice.subscription_id == sub.id).all()


def reset_all_conversations(db: Session) -> None:
    """Delete all conversation data — for demo/testing only."""
    db.query(ActionLog).delete()
    db.query(Ticket).delete()
    db.query(Message).delete()
    db.query(Conversation).delete()
    db.commit()
