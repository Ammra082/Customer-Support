"""Subscription-related business action tools."""

from sqlalchemy.orm import Session
from app.db.queries import get_subscription, log_action
from app.db.models import PlanType
from datetime import datetime, timedelta

PLAN_PRICES = {
    "free": 0.0,
    "starter": 19.0,
    "pro": 49.0,
    "enterprise": 299.0,
}


def check_subscription(db: Session, user_id: str, **_) -> dict:
    sub = get_subscription(db, user_id)
    if not sub:
        return {"success": False, "error": "No subscription found for this account."}
    result = {
        "success": True,
        "plan": sub.plan.value,
        "status": sub.status,
        "billing_email": sub.billing_email,
        "next_billing_date": sub.next_billing_date,
        "amount_usd": sub.amount_usd,
    }
    log_action(db, "check_subscription", user_id=user_id, result=result)
    return result


def upgrade_plan(db: Session, user_id: str, new_plan: str = "pro", **_) -> dict:
    sub = get_subscription(db, user_id)
    if not sub:
        return {"success": False, "error": "No subscription found."}
    new_plan = new_plan.lower()
    if new_plan not in PLAN_PRICES:
        return {"success": False, "error": f"Unknown plan '{new_plan}'."}
    old_plan = sub.plan.value
    sub.plan = PlanType(new_plan)
    sub.amount_usd = PLAN_PRICES[new_plan]
    sub.updated_at = datetime.utcnow()
    db.commit()
    result = {
        "success": True,
        "old_plan": old_plan,
        "new_plan": new_plan,
        "new_amount_usd": PLAN_PRICES[new_plan],
        "message": f"Plan upgraded from {old_plan} to {new_plan} successfully.",
    }
    log_action(db, "upgrade_plan", user_id=user_id, parameters={"new_plan": new_plan}, result=result)
    return result


def cancel_subscription(db: Session, user_id: str, **_) -> dict:
    sub = get_subscription(db, user_id)
    if not sub:
        return {"success": False, "error": "No subscription found."}
    if sub.status == "cancelled":
        return {"success": False, "error": "Subscription is already cancelled."}
    sub.status = "cancelled"
    sub.updated_at = datetime.utcnow()
    db.commit()
    result = {
        "success": True,
        "plan": sub.plan.value,
        "active_until": sub.next_billing_date,
        "message": "Subscription cancellation scheduled. Access continues until billing period ends.",
    }
    log_action(db, "cancel_subscription", user_id=user_id, result=result)
    return result
