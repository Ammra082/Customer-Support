"""Basic smoke tests for the agent and tools."""

import pytest
from unittest.mock import MagicMock, patch
from app.utils.text import is_frustrated, wants_human, extract_email, normalize_text


# ── Text utility tests ────────────────────────────────────────────────────────

def test_normalize_text():
    assert normalize_text("  Hello  World  ") == "hello world"


def test_is_frustrated_positive():
    assert is_frustrated("This is the worst service I've ever used")
    assert is_frustrated("I am really frustrated with this")


def test_is_frustrated_negative():
    assert not is_frustrated("How do I reset my password?")
    assert not is_frustrated("Can you check my subscription?")


def test_wants_human_positive():
    assert wants_human("I want to talk to a real person")
    assert wants_human("Please connect me to a human agent")
    assert wants_human("I need to speak to someone")


def test_wants_human_negative():
    assert not wants_human("How do I upgrade my plan?")
    assert not wants_human("What is the billing cycle?")


def test_extract_email():
    assert extract_email("Change billing to finance@company.com please") == "finance@company.com"
    assert extract_email("no email here") is None


# ── Tool tests ────────────────────────────────────────────────────────────────

def test_check_subscription_no_user():
    from app.tools.subscription import check_subscription
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    result = check_subscription(db=db, user_id="nonexistent")
    assert result["success"] is False
    assert "No subscription" in result["error"]


def test_check_workspace_usage_no_workspace():
    from app.tools.workspace import check_workspace_usage
    db = MagicMock()
    db.query.return_value.filter.return_value.first.return_value = None
    result = check_workspace_usage(db=db, user_id="nonexistent")
    assert result["success"] is False


def test_update_billing_email_invalid():
    from app.tools.billing import update_billing_email
    db = MagicMock()
    # Mock subscription
    mock_sub = MagicMock()
    mock_sub.billing_email = "old@example.com"
    db.query.return_value.filter.return_value.first.return_value = mock_sub
    result = update_billing_email(db=db, user_id="user_001", new_email="not-an-email")
    assert result["success"] is False


# ── Config tests ──────────────────────────────────────────────────────────────

def test_settings_loads():
    from app.utils.config import get_settings
    settings = get_settings()
    assert settings.groq_model == "llama-3.3-70b-versatile" or len(settings.groq_model) > 0
    assert settings.retrieval_confidence_threshold > 0


def test_missing_api_key_raises():
    from app.utils.config import Settings
    s = Settings(groq_api_key="")
    with pytest.raises(EnvironmentError, match="GROQ_API_KEY"):
        s.validate_api_key()
