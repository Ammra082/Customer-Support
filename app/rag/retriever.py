"""Semantic retriever with confidence scoring."""

from dataclasses import dataclass
from langchain_community.vectorstores import FAISS
from app.rag.index import load_index
from app.utils.config import get_settings
from app.utils.logging import get_logger

logger = get_logger("rag.retriever")


@dataclass
class RetrievalResult:
    answer: str
    source_id: str
    sub_intent: str
    confidence: float       # cosine similarity score (0–1)
    above_threshold: bool
    raw_docs: list


class FAQRetriever:
    def __init__(self) -> None:
        self._store: FAISS | None = None
        self._threshold = get_settings().retrieval_confidence_threshold

    def _get_store(self) -> FAISS | None:
        if self._store is None:
            self._store = load_index()
        return self._store

    def retrieve(self, query: str, k: int = 3) -> RetrievalResult | None:
        """Search FAISS and return the best match with a confidence score."""
        store = self._get_store()
        if store is None:
            logger.warning("FAISS store not available")
            return None

        results = store.similarity_search_with_score(query, k=k)
        if not results:
            return None

        # FAISS returns L2 distance by default; because we normalized embeddings
        # during ingest we convert distance → cosine similarity via: sim = 1 - dist/2
        best_doc, best_dist = results[0]
        confidence = float(max(0.0, min(1.0, 1.0 - best_dist / 2.0)))

        meta = best_doc.metadata
        ideal_answer = meta.get("ideal_answer", best_doc.page_content)

        logger.debug(
            "Retrieval result",
            confidence=confidence,
            threshold=self._threshold,
            sub_intent=meta.get("sub_intent"),
        )

        return RetrievalResult(
            answer=ideal_answer,
            source_id=meta.get("id", ""),
            sub_intent=meta.get("sub_intent", ""),
            confidence=confidence,
            above_threshold=confidence >= self._threshold,
            raw_docs=results,
        )


# Module-level singleton
_retriever: FAQRetriever | None = None


def get_retriever() -> FAQRetriever:
    global _retriever
    if _retriever is None:
        _retriever = FAQRetriever()
    return _retriever
