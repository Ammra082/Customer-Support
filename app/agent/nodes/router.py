"""Router node — maps intent to the next graph node."""

from app.utils.logging import get_logger

logger = get_logger("agent.router")


def route(state: dict) -> str:
    """Return the name of the next node based on classified intent."""
    intent = state.get("intent", "faq")
    confidence = state.get("confidence", 1.0)

    if intent == "escalate" or confidence < 0.45:
        logger.debug("Routing to escalation", intent=intent, confidence=confidence)
        return "escalation_decider"

    if intent == "action":
        logger.debug("Routing to action_executor")
        return "action_executor"

    # Default: faq
    logger.debug("Routing to faq_retriever")
    return "faq_retriever"
