"""LangGraph state machine for the TaskFlow support agent."""

from typing import TypedDict, Optional, Any
from langgraph.graph import StateGraph, END

from app.agent.nodes.intent_classifier import run_intent_classifier
from app.agent.nodes.router import route
from app.agent.nodes.faq_retriever import run_faq_retriever
from app.agent.nodes.action_executor import run_action_executor
from app.agent.nodes.escalation import run_escalation_decider
from app.agent.nodes.response_generator import run_response_generator
from app.agent.nodes.memory import run_memory_persistence
from app.utils.logging import get_logger

logger = get_logger("agent.graph")


# ── Typed State ────────────────────────────────────────────────────────────────

class AgentState(TypedDict, total=False):
    # Input
    user_message: str
    user_id: str
    conversation_id: str
    db: Any                        # SQLAlchemy Session (not serialized)
    history: list[dict]

    # Classification
    intent: str
    sub_intent: str
    tool_name: Optional[str]
    confidence: float
    escalation_reason: Optional[str]

    # Retrieval
    retrieved_answer: Optional[str]
    retrieval_confidence: float
    retrieval_source: Optional[str]
    above_threshold: bool

    # Action
    action_result: Optional[dict]
    action_success: bool

    # Escalation
    escalated: bool
    ticket_number: Optional[str]

    # Output
    final_response: str


# ── Conditional routing helper ─────────────────────────────────────────────────

def _route_after_classification(state: AgentState) -> str:
    return route(state)


def _route_after_faq(state: AgentState) -> str:
    """After retrieval, check if we need to escalate due to low confidence."""
    if not state.get("above_threshold", True):
        return "escalation_decider"
    return "response_generator"


def _route_after_action(state: AgentState) -> str:
    """After action execution, check if we need to escalate on failure."""
    if not state.get("action_success", True):
        return "escalation_decider"
    return "response_generator"


# ── Build the graph ────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    # Register nodes
    graph.add_node("intent_classifier", run_intent_classifier)
    graph.add_node("faq_retriever", run_faq_retriever)
    graph.add_node("action_executor", run_action_executor)
    graph.add_node("escalation_decider", run_escalation_decider)
    graph.add_node("response_generator", run_response_generator)
    graph.add_node("memory_persistence", run_memory_persistence)

    # Entry point
    graph.set_entry_point("intent_classifier")

    # Classification → router
    graph.add_conditional_edges(
        "intent_classifier",
        _route_after_classification,
        {
            "faq_retriever": "faq_retriever",
            "action_executor": "action_executor",
            "escalation_decider": "escalation_decider",
        },
    )

    # FAQ → conditional on retrieval confidence
    graph.add_conditional_edges(
        "faq_retriever",
        _route_after_faq,
        {
            "response_generator": "response_generator",
            "escalation_decider": "escalation_decider",
        },
    )

    # Action → conditional on success
    graph.add_conditional_edges(
        "action_executor",
        _route_after_action,
        {
            "response_generator": "response_generator",
            "escalation_decider": "escalation_decider",
        },
    )

    # Escalation → response
    graph.add_edge("escalation_decider", "response_generator")

    # Response → memory → END
    graph.add_edge("response_generator", "memory_persistence")
    graph.add_edge("memory_persistence", END)

    return graph


# Module-level compiled graph singleton
_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph().compile()
        logger.info("LangGraph compiled successfully")
    return _compiled_graph


def run_agent(
    user_message: str,
    user_id: str,
    conversation_id: str,
    db,
    history: list[dict] | None = None,
) -> AgentState:
    """Run the agent for one turn and return the final state."""
    graph = get_graph()
    initial_state: AgentState = {
        "user_message": user_message,
        "user_id": user_id,
        "conversation_id": conversation_id,
        "db": db,
        "history": history or [],
        "escalated": False,
        "action_success": True,
        "above_threshold": True,
    }
    result = graph.invoke(initial_state)
    return result
