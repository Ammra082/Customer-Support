"""SQLAlchemy ORM models for TaskFlow Support Bot."""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
    Enum,
)
from sqlalchemy.orm import DeclarativeBase, relationship
import enum


class Base(DeclarativeBase):
    pass


# ── Enums ─────────────────────────────────────────────────────────────────────

class PlanType(str, enum.Enum):
    free = "free"
    starter = "starter"
    pro = "pro"
    enterprise = "enterprise"


class TicketStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    closed = "closed"


class IntentType(str, enum.Enum):
    faq = "faq"
    action = "action"
    escalate = "escalate"
    unknown = "unknown"


class MessageRole(str, enum.Enum):
    user = "user"
    assistant = "assistant"
    system = "system"


# ── Tables ────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), unique=True, index=True, nullable=False)
    name = Column(String(128), nullable=False)
    email = Column(String(256), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    subscription = relationship("Subscription", back_populates="user", uselist=False)
    workspace = relationship("Workspace", back_populates="user", uselist=False)
    conversations = relationship("Conversation", back_populates="user")
    tickets = relationship("Ticket", back_populates="user")


class Subscription(Base):
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False)
    plan = Column(Enum(PlanType), default=PlanType.free)
    status = Column(String(32), default="active")   # active | past_due | cancelled
    billing_email = Column(String(256))
    next_billing_date = Column(String(32))
    amount_usd = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="subscription")
    invoices = relationship("Invoice", back_populates="subscription")


class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(64), unique=True, nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=False)
    amount_usd = Column(Float, nullable=False)
    status = Column(String(32), default="paid")   # paid | pending | failed
    issued_date = Column(String(32))
    due_date = Column(String(32))
    pdf_url = Column(String(512), default="")

    subscription = relationship("Subscription", back_populates="invoices")


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True, index=True)
    workspace_id = Column(String(64), unique=True, nullable=False)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False)
    name = Column(String(256), nullable=False)
    member_count = Column(Integer, default=1)
    storage_used_gb = Column(Float, default=0.0)
    storage_limit_gb = Column(Float, default=5.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="workspace")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(64), unique=True, index=True, nullable=False)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_escalated = Column(Boolean, default=False)

    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", order_by="Message.created_at")
    ticket = relationship("Ticket", back_populates="conversation", uselist=False)


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(64), ForeignKey("conversations.conversation_id"), nullable=False)
    role = Column(Enum(MessageRole), nullable=False)
    content = Column(Text, nullable=False)
    intent = Column(Enum(IntentType), nullable=True)
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(32), unique=True, nullable=False)
    conversation_id = Column(String(64), ForeignKey("conversations.conversation_id"), nullable=True)
    user_id = Column(String(64), ForeignKey("users.user_id"), nullable=False)
    intent = Column(Enum(IntentType), nullable=True)
    escalation_reason = Column(Text, nullable=True)
    conversation_snippet = Column(Text, nullable=True)
    status = Column(Enum(TicketStatus), default=TicketStatus.open)
    priority = Column(String(16), default="medium")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="tickets")
    conversation = relationship("Conversation", back_populates="ticket")


class ActionLog(Base):
    __tablename__ = "action_logs"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(String(64), nullable=True)
    user_id = Column(String(64), nullable=True)
    action_name = Column(String(128), nullable=False)
    parameters = Column(Text, nullable=True)   # JSON string
    result = Column(Text, nullable=True)        # JSON string
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
