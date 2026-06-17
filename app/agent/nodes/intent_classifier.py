"""Intent classification node — calls Groq to classify user intent."""

import json
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from app.utils.config import get_settings
from app.utils.text import is_frustrated, wants_human
from app.utils.logging import get_logger

logger = get_logger("agent.intent_classifier")

INTENT_SYSTEM_PROMPT = """You are an intent classifier for TaskFlow customer support.

Classify the user message into exactly ONE of these intents:
- faq: The user is asking a general question about TaskFlow features, policies, or how-to guidance. If the user asks HOW to do something, classify it as 'faq'.
- action: The user wants to perform a specific account/subscription/workspace operation. Only classify as 'action' if the user explicitly asks YOU to do it for them right now.
- escalate: The user is frustrated, requests a human, or the request is outside support scope

Also extract the sub_intent (a short snake_case label like "check_subscription", "password_reset") and the tool_name if intent is "action".

Respond ONLY with valid JSON in this exact format:
{
  "intent": "faq" | "action" | "escalate",
  "sub_intent": "string",
  "tool_name": "string or null",
  "confidence": 0.0-1.0,
  "escalation_reason": "string or null"
}

Known action tool names: check_subscription, upgrade_plan, cancel_subscription, update_billing_email,
view_invoice, check_workspace_usage, invite_member, reset_access, check_payment_status,
update_workspace_name, assign_role, create_ticket, check_integration_status, restore_project, export_workspace.

Be conservative: if in doubt between action and faq, choose faq. If confidence < 0.5, choose escalate."""


def run_intent_classifier(state: dict) -> dict:
    """Classify the latest user message and update state."""
    settings = get_settings()
    user_message = state.get("user_message", "")

    # Fast-path: explicit human request or frustration
    if wants_human(user_message):
        logger.info("Fast-path: human requested")
        return {
            **state,
            "intent": "escalate",
            "sub_intent": "human_request",
            "tool_name": None,
            "confidence": 1.0,
            "escalation_reason": "User explicitly requested a human agent.",
        }

    if is_frustrated(user_message):
        logger.info("Fast-path: frustration detected")
        return {
            **state,
            "intent": "escalate",
            "sub_intent": "frustration",
            "tool_name": None,
            "confidence": 0.95,
            "escalation_reason": "Frustration signals detected in user message.",
        }

    try:
        llm = ChatGroq(
            api_key=settings.groq_api_key,
            model=settings.groq_model,
            temperature=0,
            max_tokens=256,
        )
        messages = [
            SystemMessage(content=INTENT_SYSTEM_PROMPT),
            HumanMessage(content=user_message),
        ]
        response = llm.invoke(messages)
        raw = response.content.strip()

        # Strip markdown fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        parsed = json.loads(raw)
        intent = parsed.get("intent", "faq")
        confidence = float(parsed.get("confidence", 0.7))

        # Safety: low confidence → escalate
        if confidence < 0.45:
            intent = "escalate"
            parsed["escalation_reason"] = f"Low classification confidence ({confidence:.2f})."

        return {
            **state,
            "intent": intent,
            "sub_intent": parsed.get("sub_intent", ""),
            "tool_name": parsed.get("tool_name"),
            "confidence": confidence,
            "escalation_reason": parsed.get("escalation_reason"),
        }

    except Exception as e:
        logger.error("Intent classification failed", error=str(e))
        return {
            **state,
            "intent": "escalate",
            "sub_intent": "classifier_error",
            "tool_name": None,
            "confidence": 0.0,
            "escalation_reason": f"Intent classifier error: {str(e)[:120]}",
        }
