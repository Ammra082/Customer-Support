"""HuggingFace embedding wrapper used across the RAG pipeline."""

from functools import lru_cache
from langchain_huggingface import HuggingFaceEmbeddings
from app.utils.config import get_settings


@lru_cache(maxsize=1)
def get_embeddings() -> HuggingFaceEmbeddings:
    """Return a cached HuggingFace embedding model."""
    settings = get_settings()
    return HuggingFaceEmbeddings(
        model_name=settings.embedding_model,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )
