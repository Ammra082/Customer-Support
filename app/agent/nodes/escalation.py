"""Escalation decider node — creates a ticket and marks the conversation escalated."""

from app.tools.support import create_ticket
from app.utils.logging import get_logger
from app.utils.text import truncate

logger = get_logger("agent.escalation")


def run_escalation_decider(state: dict) -> dict:
    """Create a support ticket and update state with escalation details."""
    db = state.get("db")
    user_id = state.get("user_id", "anonymous")
    conversation_id = state.get("conversation_id", "")
    escalation_reason = state.get("escalation_reason") or "Escalated by support agent."
    intent = state.get("intent", "unknown")
    user_message = state.get("user_message", "")

    if db:
        try:
            ticket_result = create_ticket(
                db=db,
                user_id=user_id,
                conversation_id=conversation_id,
                reason=escalation_reason,
                snippet=truncate(user_message, 400),
                intent=intent,
            )
            ticket_number = ticket_result.get("ticket_number", "N/A")
            logger.info("Escalation ticket created", ticket=ticket_number, user=user_id)
        except Exception as e:
            logger.error("Failed to create ticket", error=str(e))
            ticket_number = "ERROR"
    else:
        logger.warning("No DB session — ticket not persisted")
        ticket_number = "DEMO-001"

    return {
        **state,
        "escalated": True,
        "ticket_number": ticket_number,
        "escalation_reason": escalation_reason,
    }
