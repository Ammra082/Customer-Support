"""Memory persistence node — saves messages to SQLite after each turn."""

from app.db import queries as q
from app.utils.logging import get_logger

logger = get_logger("agent.memory")


def run_memory_persistence(state: dict) -> dict:
    """Persist the current turn (user + assistant messages) to the DB."""
    db = state.get("db")
    if not db:
        logger.warning("No DB session — messages not persisted")
        return state

    conversation_id = state.get("conversation_id", "")
    user_id = state.get("user_id", "anonymous")
    user_message = state.get("user_message", "")
    final_response = state.get("final_response", "")
    intent = state.get("intent")
    confidence = state.get("confidence")

    try:
        # Ensure conversation record exists
        q.get_or_create_conversation(db, conversation_id, user_id)

        # Save user message
        if user_message:
            q.add_message(
                db=db,
                conversation_id=conversation_id,
                role="user",
                content=user_message,
                intent=intent,
                confidence=confidence,
            )

        # Save assistant response
        if final_response:
            q.add_message(
                db=db,
                conversation_id=conversation_id,
                role="assistant",
                content=final_response,
                intent=intent,
                confidence=confidence,
            )

        logger.debug("Messages persisted", conversation_id=conversation_id)
    except Exception as e:
        logger.error("Memory persistence failed", error=str(e))

    return state
