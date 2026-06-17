"""Response generator node — synthesizes the final reply using Groq."""

import json
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from app.utils.config import get_settings
from app.utils.logging import get_logger

logger = get_logger("agent.response_generator")

RESPONSE_SYSTEM_PROMPT = """You are a professional customer support agent for TaskFlow, a project management SaaS.

Guidelines:
- Be concise, professional, and empathetic.
- Never fabricate account details, billing confirmations, or security information.
- If an action was performed, confirm it clearly and state the outcome.
- If the answer came from the knowledge base, present it naturally.
- If the case was escalated, express empathy and give the ticket number.
- Keep responses under 150 words unless the user needs detailed steps.
- Do not use excessive emojis or overly casual language.
- Always end with an offer to help further if appropriate."""


def _build_context(state: dict) -> str:
    """Summarize state into a structured context block for the LLM."""
    parts = []
    intent = state.get("intent", "faq")
    parts.append(f"Intent: {intent}")

    if state.get("retrieved_answer"):
        parts.append(f"Knowledge Base Answer: {state['retrieved_answer']}")
        parts.append(f"Retrieval Confidence: {state.get('retrieval_confidence', 0):.2f}")

    if state.get("action_result"):
        result = state["action_result"]
        parts.append(f"Action Tool: {state.get('tool_name', '')}")
        parts.append(f"Action Result: {json.dumps(result)}")
        parts.append(f"Action Success: {state.get('action_success', False)}")

    if state.get("escalated"):
        parts.append(f"Escalated: Yes")
        parts.append(f"Ticket Number: {state.get('ticket_number', 'N/A')}")
        parts.append(f"Escalation Reason: {state.get('escalation_reason', '')}")

    # Include recent conversation turns for context
    history = state.get("history", [])
    if history:
        recent = history[-4:]  # last 2 exchanges
        history_text = "\n".join(
            f"{m['role'].upper()}: {m['content'][:120]}" for m in recent
        )
        parts.append(f"Recent Conversation:\n{history_text}")

    return "\n".join(parts)


def run_response_generator(state: dict) -> dict:
    """Generate the final assistant response."""
    settings = get_settings()
    user_message = state.get("user_message", "")
    context = _build_context(state)

    prompt = f"""Context about this support interaction:
{context}

User's current message: {user_message}

Generate a professional, helpful response."""

    try:
        llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=0.3,
            max_tokens=512,
        )
        messages = [
            SystemMessage(content=RESPONSE_SYSTEM_PROMPT),
            HumanMessage(content=prompt),
        ]
        response = llm.invoke(messages)
        final_response = response.content.strip()
        logger.debug("Response generated", length=len(final_response))

    except Exception as e:
        logger.error("Response generation failed", error=str(e))
        if state.get("escalated"):
            ticket = state.get("ticket_number", "N/A")
            final_response = (
                f"I've escalated your case to our support team. "
                f"Your ticket number is **{ticket}**. "
                "A specialist will follow up with you shortly."
            )
        elif state.get("retrieved_answer"):
            final_response = state["retrieved_answer"]
        else:
            final_response = (
                "I'm sorry, I encountered an issue processing your request. "
                "Please try again or contact support directly."
            )

    return {**state, "final_response": final_response}
