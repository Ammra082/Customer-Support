"""Action executor node — dispatches to business tool functions."""

from app.utils.logging import get_logger
from app.utils.text import extract_email

logger = get_logger("agent.action_executor")


# Registry mapping tool_name → callable
def _get_tool_registry():
    from app.tools.subscription import check_subscription, upgrade_plan, cancel_subscription
    from app.tools.billing import update_billing_email, view_invoice, check_payment_status
    from app.tools.workspace import (
        check_workspace_usage, invite_member, reset_access,
        update_workspace_name, assign_role, export_workspace,
    )
    from app.tools.support import (
        create_ticket, check_integration_status, restore_project, generic_action,
    )
    return {
        "check_subscription": check_subscription,
        "upgrade_plan": upgrade_plan,
        "cancel_subscription": cancel_subscription,
        "update_billing_email": update_billing_email,
        "view_invoice": view_invoice,
        "check_payment_status": check_payment_status,
        "check_workspace_usage": check_workspace_usage,
        "invite_member": invite_member,
        "reset_access": reset_access,
        "update_workspace_name": update_workspace_name,
        "assign_role": assign_role,
        "create_ticket": create_ticket,
        "check_integration_status": check_integration_status,
        "restore_project": restore_project,
        "export_workspace": export_workspace,
        # Dataset extras — map to generic
        "resend_invite": generic_action,
        "change_timezone": generic_action,
        "manage_webhook": generic_action,
        "download_audit": generic_action,
        "change_owner": generic_action,
        "update_language": generic_action,
        "set_digest": generic_action,
        "add_label": generic_action,
        "attach_file_limit": generic_action,
        "verify_sso": generic_action,
    }


def _extract_params(state: dict) -> dict:
    """Pull dynamic parameters from user message and state."""
    msg = state.get("user_message", "")
    params = {
        "user_id": state.get("user_id", "demo_user"),
        "conversation_id": state.get("conversation_id", ""),
        "intent": state.get("intent", "action"),
        "reason": state.get("escalation_reason", ""),
        "snippet": msg[:300],
        "tool_name": state.get("tool_name", ""),
        "message": f"Action '{state.get('tool_name', '')}' completed.",
    }

    # Dynamically extract common parameter patterns from message
    email = extract_email(msg)
    if email:
        params["new_email"] = email
        params["member_email"] = email

    lower = msg.lower()

    # Plan name extraction
    for plan in ["enterprise", "business", "pro", "starter", "free"]:
        if plan in lower:
            params["new_plan"] = plan
            break

    # Target user extraction (simplistic: look for "for <Name>")
    import re
    m = re.search(r"\bfor\s+([A-Z][a-z]+)\b", msg)
    if m:
        params["target_user"] = m.group(1)
        params["member_name"] = m.group(1)

    # Make <name> to <name> extraction
    m2 = re.search(r"\b(?:make|set)\s+([A-Z][a-z]+)\b", msg)
    if m2:
        params["target_user"] = m2.group(1)

    # New workspace name
    m3 = re.search(r"\bto\s+([A-Z][A-Za-z0-9 ]+?)(?:\s*\.|$)", msg)
    if m3:
        params["new_name"] = m3.group(1).strip()
        params["project_name"] = m3.group(1).strip()

    # Integration name
    for svc in ["slack", "github", "jira", "zapier", "google"]:
        if svc in lower:
            params["integration_name"] = svc
            break

    return params


def run_action_executor(state: dict) -> dict:
    """Dispatch to the appropriate tool and attach the result to state."""
    tool_name = state.get("tool_name")
    db = state.get("db")

    if not db:
        logger.error("No DB session in state")
        return {
            **state,
            "action_result": {"success": False, "error": "Database session unavailable."},
            "action_success": False,
        }

    registry = _get_tool_registry()
    tool_fn = registry.get(tool_name)

    if not tool_fn:
        logger.warning("Unknown tool", tool_name=tool_name)
        return {
            **state,
            "action_result": {
                "success": False,
                "error": f"Action '{tool_name}' is not supported.",
            },
            "action_success": False,
            "intent": "escalate",
            "escalation_reason": f"Unsupported action: {tool_name}",
        }

    params = _extract_params(state)

    try:
        result = tool_fn(db=db, **params)
        success = result.get("success", True)
        logger.info("Action executed", tool=tool_name, success=success)

        if not success:
            return {
                **state,
                "action_result": result,
                "action_success": False,
                "intent": "escalate",
                "escalation_reason": result.get("error", "Action failed."),
            }

        return {**state, "action_result": result, "action_success": True}

    except Exception as e:
        logger.error("Action execution error", tool=tool_name, error=str(e))
        return {
            **state,
            "action_result": {"success": False, "error": str(e)},
            "action_success": False,
            "intent": "escalate",
            "escalation_reason": f"Action '{tool_name}' failed: {str(e)[:120]}",
        }
