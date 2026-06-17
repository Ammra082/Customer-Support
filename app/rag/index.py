"""FAISS index creation, saving, and loading."""

import os
from pathlib import Path
from langchain_community.vectorstores import FAISS
from app.rag.embeddings import get_embeddings
from app.utils.config import get_settings
from app.utils.logging import get_logger

logger = get_logger("rag.index")


def get_index_path() -> Path:
    settings = get_settings()
    return Path(settings.faiss_index_path)


def save_index(vectorstore: FAISS) -> None:
    """Persist FAISS index to disk."""
    path = get_index_path()
    path.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(path))
    logger.info("FAISS index saved", path=str(path))


def load_index() -> FAISS | None:
    """Load FAISS index from disk; returns None if not found."""
    path = get_index_path()
    if not path.exists() or not any(path.iterdir()):
        logger.warning("FAISS index not found — run ingest.py first", path=str(path))
        return None
    embeddings = get_embeddings()
    store = FAISS.load_local(
        str(path), embeddings, allow_dangerous_deserialization=True
    )
    logger.info("FAISS index loaded", path=str(path))
    return store


def index_exists() -> bool:
    path = get_index_path()
    return path.exists() and any(path.iterdir())
