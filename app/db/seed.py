"""Seed the database with realistic demo data."""

from datetime import datetime, timedelta
from app.db.session import SessionLocal
from app.db.models import User, Subscription, Invoice, Workspace, PlanType


SEED_USERS = [
    {
        "user_id": "user_001",
        "name": "Alice Johnson",
        "email": "alice@acmecorp.io",
        "plan": PlanType.pro,
        "billing_email": "billing@acmecorp.io",
        "amount_usd": 49.0,
        "workspace_name": "Acme Corp",
        "member_count": 12,
        "storage_used_gb": 3.2,
        "storage_limit_gb": 20.0,
        "invoices": [
            {"number": "INV-2024-0101", "amount": 49.0, "status": "paid",
             "issued": "2024-01-01", "due": "2024-01-15"},
            {"number": "INV-2024-0201", "amount": 49.0, "status": "paid",
             "issued": "2024-02-01", "due": "2024-02-15"},
            {"number": "INV-2024-0301", "amount": 49.0, "status": "pending",
             "issued": "2024-03-01", "due": "2024-03-15"},
        ],
    },
    {
        "user_id": "user_002",
        "name": "Bob Martinez",
        "email": "bob@startupxyz.com",
        "plan": PlanType.starter,
        "billing_email": "bob@startupxyz.com",
        "amount_usd": 19.0,
        "workspace_name": "StartupXYZ",
        "member_count": 4,
        "storage_used_gb": 1.1,
        "storage_limit_gb": 10.0,
        "invoices": [
            {"number": "INV-2024-0102", "amount": 19.0, "status": "paid",
             "issued": "2024-01-01", "due": "2024-01-15"},
        ],
    },
    {
        "user_id": "user_003",
        "name": "Carol Lee",
        "email": "carol@freelance.dev",
        "plan": PlanType.free,
        "billing_email": "carol@freelance.dev",
        "amount_usd": 0.0,
        "workspace_name": "Carol's Workspace",
        "member_count": 1,
        "storage_used_gb": 0.3,
        "storage_limit_gb": 5.0,
        "invoices": [],
    },
    {
        "user_id": "user_004",
        "name": "David Chen",
        "email": "david@enterprise.net",
        "plan": PlanType.enterprise,
        "billing_email": "finance@enterprise.net",
        "amount_usd": 299.0,
        "workspace_name": "Enterprise Solutions Inc",
        "member_count": 85,
        "storage_used_gb": 47.5,
        "storage_limit_gb": 500.0,
        "invoices": [
            {"number": "INV-2024-0103", "amount": 299.0, "status": "paid",
             "issued": "2024-01-01", "due": "2024-01-15"},
            {"number": "INV-2024-0203", "amount": 299.0, "status": "failed",
             "issued": "2024-02-01", "due": "2024-02-15"},
        ],
    },
    {
        "user_id": "demo_user",
        "name": "Demo User",
        "email": "demo@taskflow.app",
        "plan": PlanType.pro,
        "billing_email": "demo@taskflow.app",
        "amount_usd": 49.0,
        "workspace_name": "TaskFlow Demo",
        "member_count": 3,
        "storage_used_gb": 0.8,
        "storage_limit_gb": 20.0,
        "invoices": [
            {"number": "INV-DEMO-001", "amount": 49.0, "status": "paid",
             "issued": "2024-03-01", "due": "2024-03-15"},
        ],
    },
]


def seed() -> None:
    """Insert seed data if users table is empty."""
    db = SessionLocal()
    try:
        if db.query(User).count() > 0:
            print("[INFO] Database already seeded, skipping.")
            return

        for u in SEED_USERS:
            user = User(
                user_id=u["user_id"],
                name=u["name"],
                email=u["email"],
            )
            db.add(user)
            db.flush()

            next_billing = (datetime.utcnow() + timedelta(days=30)).strftime("%Y-%m-%d")
            sub = Subscription(
                user_id=u["user_id"],
                plan=u["plan"],
                status="active" if u["plan"] != PlanType.free else "active",
                billing_email=u["billing_email"],
                next_billing_date=next_billing,
                amount_usd=u["amount_usd"],
            )
            db.add(sub)
            db.flush()

            for inv_data in u["invoices"]:
                inv = Invoice(
                    invoice_number=inv_data["number"],
                    subscription_id=sub.id,
                    amount_usd=inv_data["amount"],
                    status=inv_data["status"],
                    issued_date=inv_data["issued"],
                    due_date=inv_data["due"],
                    pdf_url=f"https://billing.taskflow.app/invoices/{inv_data['number']}.pdf",
                )
                db.add(inv)

            ws = Workspace(
                workspace_id=f"ws_{u['user_id']}",
                user_id=u["user_id"],
                name=u["workspace_name"],
                member_count=u["member_count"],
                storage_used_gb=u["storage_used_gb"],
                storage_limit_gb=u["storage_limit_gb"],
            )
            db.add(ws)

        db.commit()
        print(f"[OK] Seeded {len(SEED_USERS)} users with subscriptions, invoices, and workspaces.")
    except Exception as e:
        db.rollback()
        print(f"[ERROR] Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
