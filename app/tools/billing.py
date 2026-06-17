"""Billing-related business action tools."""

from sqlalchemy.orm import Session
from app.db.queries import get_subscription, get_invoices, log_action
from datetime import datetime


def update_billing_email(db: Session, user_id: str, new_email: str = "", **_) -> dict:
    sub = get_subscription(db, user_id)
    if not sub:
        return {"success": False, "error": "No subscription found."}
    if not new_email or "@" not in new_email:
        return {"success": False, "error": "A valid email address is required."}
    old_email = sub.billing_email
    sub.billing_email = new_email
    sub.updated_at = datetime.utcnow()
    db.commit()
    result = {
        "success": True,
        "old_email": old_email,
        "new_email": new_email,
        "message": f"Billing email updated to {new_email}.",
    }
    log_action(
        db, "update_billing_email",
        user_id=user_id,
        parameters={"new_email": new_email},
        result=result,
    )
    return result


def view_invoice(db: Session, user_id: str, invoice_number: str = "", **_) -> dict:
    invoices = get_invoices(db, user_id)
    if not invoices:
        return {"success": False, "error": "No invoices found for this account."}
    if invoice_number:
        inv = next((i for i in invoices if i.invoice_number == invoice_number), None)
        if not inv:
            return {"success": False, "error": f"Invoice {invoice_number} not found."}
    else:
        # Return the most recent invoice
        inv = sorted(invoices, key=lambda i: i.issued_date or "", reverse=True)[0]
    result = {
        "success": True,
        "invoice_number": inv.invoice_number,
        "amount_usd": inv.amount_usd,
        "status": inv.status,
        "issued_date": inv.issued_date,
        "due_date": inv.due_date,
        "pdf_url": inv.pdf_url,
    }
    log_action(db, "view_invoice", user_id=user_id, result=result)
    return result


def check_payment_status(db: Session, user_id: str, **_) -> dict:
    invoices = get_invoices(db, user_id)
    if not invoices:
        return {"success": False, "error": "No payment records found."}
    latest = sorted(invoices, key=lambda i: i.issued_date or "", reverse=True)[0]
    result = {
        "success": True,
        "invoice_number": latest.invoice_number,
        "amount_usd": latest.amount_usd,
        "status": latest.status,
        "issued_date": latest.issued_date,
        "message": f"Latest payment ({latest.invoice_number}) is {latest.status}.",
    }
    log_action(db, "check_payment_status", user_id=user_id, result=result)
    return result
