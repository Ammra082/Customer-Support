"""Support and misc action tools."""

from sqlalchemy.orm import Session
from app.db import queries
from app.utils.logging import get_logger

logger = get_logger("tools.support")

INTEGRATIONS = {
    "slack": {"status": "connected", "last_sync": "2024-03-10T08:00:00Z"},
    "github": {"status": "connected", "last_sync": "2024-03-09T14:30:00Z"},
    "jira": {"status": "disconnected", "last_sync": None},
    "zapier": {"status": "connected", "last_sync": "2024-03-08T10:00:00Z"},
}


def create_ticket(
    db: Session,
    user_id: str,
    conversation_id: str = "",
    reason: str = "User requested support",
    snippet: str = "",
    intent: str = "unknown",
    **_,
) -> dict:
    ticket = queries.create_ticket(
        db=db,
        user_id=user_id,
        conversation_id=conversation_id or None,
        intent=intent,
        escalation_reason=reason,
        conversation_snippet=snippet,
    )
    queries.mark_conversation_escalated(db, conversation_id)
    result = {
        "success": True,
        "ticket_number": ticket.ticket_number,
        "status": ticket.status.value,
        "message": f"Support ticket {ticket.ticket_number} created. A human agent will follow up.",
    }
    logger.info("Ticket created", ticket=ticket.ticket_number, user=user_id)
    return result


def check_integration_status(db: Session, user_id: str, integration_name: str = "slack", **_) -> dict:
    name = integration_name.lower()
    info = INTEGRATIONS.get(name)
    if not info:
        result = {
            "success": False,
            "error": f"Integration '{name}' is not recognized. Supported: {', '.join(INTEGRATIONS.keys())}.",
        }
    else:
        result = {
            "success": True,
            "integration": name,
            "status": info["status"],
            "last_sync": info["last_sync"],
            "message": f"{name.capitalize()} integration is currently {info['status']}.",
        }
    queries.log_action(db, "check_integration_status", user_id=user_id, parameters={"integration": name}, result=result)
    return result


def restore_project(db: Session, user_id: str, project_name: str = "", **_) -> dict:
    name = project_name or "the requested project"
    result = {
        "success": True,
        "project": name,
        "message": f"'{name}' has been restored to your active workspace.",
    }
    queries.log_action(db, "restore_project", user_id=user_id, parameters={"project": name}, result=result)
    return result


# Generic fallback for unmapped tool names from dataset
def generic_action(db: Session, user_id: str, tool_name: str = "", message: str = "", **_) -> dict:
    result = {
        "success": True,
        "tool": tool_name,
        "message": message or f"Action '{tool_name}' completed successfully.",
    }
    queries.log_action(db, tool_name or "generic_action", user_id=user_id, result=result)
    return result
