"""Text utility helpers for the support agent."""

import re
import unicodedata


# Keywords that suggest user frustration
FRUSTRATION_SIGNALS = [
    "frustrated",
    "annoyed",
    "angry",
    "terrible",
    "horrible",
    "useless",
    "worst",
    "hate",
    "ridiculous",
    "unacceptable",
    "pathetic",
    "disgusting",
    "furious",
    "outrageous",
    "awful",
    "this is a joke",
    "waste of time",
    "do something",
    "fix this now",
    "fed up",
    "enough",
    "stop wasting",
]

# Explicit escalation requests
HUMAN_ESCALATION_SIGNALS = [
    "speak to a human",
    "talk to a person",
    "human agent",
    "real person",
    "live agent",
    "human support",
    "connect me to",
    "transfer me",
    "escalate",
    "supervisor",
    "manager",
    "speak to someone",
]


def normalize_text(text: str) -> str:
    """Lowercase, strip, remove extra whitespace."""
    text = unicodedata.normalize("NFKC", text)
    text = text.lower().strip()
    text = re.sub(r"\s+", " ", text)
    return text


def is_frustrated(text: str) -> bool:
    """Return True if the message contains frustration signals."""
    normalized = normalize_text(text)
    return any(signal in normalized for signal in FRUSTRATION_SIGNALS)


def wants_human(text: str) -> bool:
    """Return True if the user explicitly requests a human agent."""
    normalized = normalize_text(text)
    return any(signal in normalized for signal in HUMAN_ESCALATION_SIGNALS)


def truncate(text: str, max_chars: int = 200) -> str:
    """Truncate text to max_chars with an ellipsis."""
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "…"


def extract_email(text: str) -> str | None:
    """Extract the first email address from text, or None."""
    match = re.search(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", text)
    return match.group(0) if match else None
