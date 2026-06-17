"""Parse the JSONL dataset, build documents, and index them into FAISS."""

import json
from pathlib import Path
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from app.rag.embeddings import get_embeddings
from app.rag.index import save_index
from app.utils.config import get_settings
from app.utils.logging import get_logger

logger = get_logger("rag.ingest")


def load_jsonl(path: str) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def build_documents(records: list[dict]) -> list[Document]:
    """Convert JSONL records into LangChain Documents for indexing."""
    docs = []
    seen = set()
    for r in records:
        # Index FAQ and escalation ideal answers; skip pure action stubs
        if r.get("intent") == "action" and not r.get("ideal_answer"):
            continue
        text = f"{r['user_query']}\n{r.get('ideal_answer', '')}"
        if text in seen:
            continue
        seen.add(text)
        docs.append(
            Document(
                page_content=text,
                metadata={
                    "id": r["id"],
                    "intent": r["intent"],
                    "sub_intent": r.get("sub_intent", ""),
                    "tags": ",".join(r.get("tags", [])),
                    "ideal_answer": r.get("ideal_answer", ""),
                    "tool_name": r.get("tool_name") or "",
                    "should_escalate": str(r.get("should_escalate", False)),
                    "confidence_threshold": str(r.get("confidence_threshold", 0.65)),
                },
            )
        )
    return docs


def ingest() -> int:
    """Full ingest pipeline — parse → build docs → FAISS → save."""
    settings = get_settings()
    dataset_path = settings.faq_dataset_path

    if not Path(dataset_path).exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    logger.info("Loading dataset", path=dataset_path)
    records = load_jsonl(dataset_path)
    docs = build_documents(records)
    logger.info("Building FAISS index", doc_count=len(docs))

    embeddings = get_embeddings()
    vectorstore = FAISS.from_documents(docs, embeddings)
    save_index(vectorstore)
    logger.info("Ingest complete", total_docs=len(docs))
    return len(docs)


if __name__ == "__main__":
    count = ingest()
    print(f"[OK] Indexed {count} documents into FAISS.")
