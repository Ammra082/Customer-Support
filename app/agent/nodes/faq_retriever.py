"""FAQ retrieval node — queries FAISS and populates state with retrieved context."""

from app.rag.retriever import get_retriever
from app.utils.logging import get_logger

logger = get_logger("agent.faq_retriever")


def run_faq_retriever(state: dict) -> dict:
    """Run semantic search and attach the result to state."""
    user_message = state.get("user_message", "")
    retriever = get_retriever()

    result = retriever.retrieve(user_message)

    if result is None:
        logger.warning("No retrieval result — will escalate")
        return {
            **state,
            "retrieved_answer": None,
            "retrieval_confidence": 0.0,
            "retrieval_source": None,
            "above_threshold": False,
        }

    logger.debug(
        "FAQ retrieved",
        confidence=result.confidence,
        source=result.source_id,
        above_threshold=result.above_threshold,
    )

    # If below threshold, escalation_decider will handle it
    if not result.above_threshold:
        return {
            **state,
            "retrieved_answer": result.answer,
            "retrieval_confidence": result.confidence,
            "retrieval_source": result.source_id,
            "above_threshold": False,
            "intent": "escalate",
            "escalation_reason": (
                f"Retrieval confidence too low ({result.confidence:.2f}) "
                "to answer reliably."
            ),
        }

    return {
        **state,
        "retrieved_answer": result.answer,
        "retrieval_confidence": result.confidence,
        "retrieval_source": result.source_id,
        "above_threshold": True,
    }
