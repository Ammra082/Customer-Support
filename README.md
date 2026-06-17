# TaskFlow Support Bot

> **Production-style AI customer support agent for TaskFlow SaaS — powered by LangGraph, Groq (Llama 3.3 70B), FAISS, FastAPI, and Streamlit.**

---

## Overview

TaskFlow Support Bot is a complete, business-ready AI support system that goes beyond simple Q&A:

| Capability | Implementation |
|---|---|
| Intent classification | Groq Llama 3.3 70B via LangGraph node |
| FAQ answering with RAG | FAISS + HuggingFace MiniLM embeddings |
| Account/subscription actions | 15+ SQLite-backed business tools |
| Human escalation | Automatic on frustration, low confidence, or user request |
| Chat history & tickets | SQLite via SQLAlchemy |
| REST API | FastAPI with Pydantic schemas |
| Frontend | Streamlit with customer chat + admin tickets tabs |
| Evaluation | Batch runner with accuracy, resolution, and latency metrics |

---

## Architecture

```
User → Streamlit UI → FastAPI → LangGraph Agent
                                    ├── intent_classifier  (Groq LLM, fast-path heuristics)
                                    ├── router             (conditional edges)
                                    ├── faq_retriever      (FAISS cosine similarity)
                                    ├── action_executor    (15 SQLite-backed tools)
                                    ├── escalation_decider (ticket creation)
                                    ├── response_generator (Groq LLM)
                                    └── memory_persistence (SQLite)
```

**Agent State Flow:**
```
intent_classifier → [faq | action | escalate]
  faq_retriever   → [response_generator | escalation_decider]
  action_executor → [response_generator | escalation_decider]
  escalation_decider → response_generator → memory_persistence → END
```

---

## Folder Structure

```
taskflow-support-bot/
  app/
    main.py                 # FastAPI app entry point
    api/
      routes.py             # /chat, /tickets, /health, /reset
      schemas.py            # Pydantic request/response models
    agent/
      graph.py              # LangGraph StateGraph
      nodes/
        intent_classifier.py
        router.py
        faq_retriever.py
        action_executor.py
        escalation.py
        response_generator.py
        memory.py
    db/
      models.py             # SQLAlchemy ORM (8 tables)
      session.py
      init_db.py
      seed.py               # 5 demo users with subscriptions & invoices
      queries.py            # All DB operations
    rag/
      embeddings.py         # HuggingFace all-MiniLM-L6-v2
      ingest.py             # JSONL → FAISS index
      retriever.py          # Semantic search + confidence scoring
      index.py              # FAISS save/load
    tools/
      subscription.py       # check, upgrade, cancel
      billing.py            # email, invoices, payment status
      workspace.py          # usage, members, roles, export
      support.py            # tickets, integrations, project restore
    ui/
      streamlit_app.py      # 2-tab Streamlit frontend
      components.py         # Reusable UI components
    eval/
      run_eval.py           # CLI evaluation runner
      metrics.py            # KPI computation
    utils/
      config.py             # Pydantic settings
      logging.py            # Structlog setup
      text.py               # Frustration/escalation detection
  data/
    taskflow_support_dataset_150.jsonl
    faiss_index/            # Auto-generated after ingest
  tests/
    test_agent.py
  .env.example
  requirements.txt
  Dockerfile
  docker-compose.yml
  README.md
```

---

## Setup Instructions

### Prerequisites
- Python 3.11+
- A free [Groq API key](https://console.groq.com)

### 1. Clone / enter the project directory

```bash
cd taskflow-support-bot
```

### 2. Create a virtual environment

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Edit .env and set your GROQ_API_KEY
```

### 5. Build the FAISS index (one-time)

```bash
python app/rag/ingest.py
```

---

## Running the Application

### Start the FastAPI backend

```bash
uvicorn app.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Swagger docs**: http://localhost:8000/docs

### Start the Streamlit frontend

In a second terminal:

```bash
streamlit run app/ui/streamlit_app.py
```

The UI will be at: http://localhost:8501

---

## Running with Docker

```bash
# Build and start API + frontend
docker-compose up --build

# Run the FAISS ingest (one-time setup)
docker-compose --profile setup run ingest
```

- **API**: http://localhost:8000
- **Frontend**: http://localhost:8501

---

## Running Evaluation

```bash
# Full evaluation (75 deduplicated samples)
python app/eval/run_eval.py --output eval_report.txt

# Quick test (first 20 samples)
python app/eval/run_eval.py --max-samples 20

# No deduplication (all 150 samples)
python app/eval/run_eval.py --no-dedup --output full_eval.txt
```

Output includes:
- Intent classification accuracy
- Escalation accuracy
- Autonomous resolution rate
- Average latency per request
- Per-intent breakdown
- Sample misclassifications

---

## Running Tests

```bash
pytest tests/ -v
```

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `GROQ_API_KEY` | **required** | Your Groq API key |
| `GROQ_MODEL` | `llama-3.3-70b-versatile` | Groq model name |
| `DATABASE_URL` | `sqlite:///./data/taskflow.db` | SQLite database path |
| `EMBEDDING_MODEL` | `sentence-transformers/all-MiniLM-L6-v2` | HuggingFace embedding model |
| `FAISS_INDEX_PATH` | `./data/faiss_index` | FAISS index storage path |
| `FAQ_DATASET_PATH` | `./data/taskflow_support_dataset_150.jsonl` | JSONL knowledge base |
| `RETRIEVAL_CONFIDENCE_THRESHOLD` | `0.45` | Min cosine sim to avoid escalation |
| `BACKEND_URL` | `http://localhost:8000` | Streamlit → FastAPI URL |
| `API_PORT` | `8000` | FastAPI port |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

---

## API Reference

### `POST /chat`
Send a message and get an AI response.

```json
// Request
{
  "message": "Can you check my subscription status?",
  "user_id": "user_001",
  "conversation_id": "optional-uuid"
}

// Response
{
  "conversation_id": "uuid",
  "user_id": "user_001",
  "message": "Can you check my subscription status?",
  "response": "Your current plan is Pro, status: active...",
  "intent": "action",
  "sub_intent": "check_subscription",
  "confidence": 0.92,
  "escalated": false,
  "ticket_number": null,
  "action_result": { "plan": "pro", "status": "active", ... }
}
```

### `GET /tickets`
Returns all escalated support tickets.

### `GET /health`
System health check (DB, FAISS index, Groq key).

### `POST /reset`
Clears all conversation history (demo/testing only).

---

## Demo Users

These users are seeded into the database automatically:

| User ID | Name | Plan | Notes |
|---|---|---|---|
| `user_001` | Alice Johnson | Pro | 3 invoices (1 pending) |
| `user_002` | Bob Martinez | Starter | 1 invoice |
| `user_003` | Carol Lee | Free | No invoices |
| `user_004` | David Chen | Enterprise | 1 failed payment |
| `demo_user` | Demo User | Pro | Default for quick testing |

---

## Sample Conversations

**FAQ:**
> User: "How do I reset my password?"
> Bot: "Go to the login page, click Forgot Password, and follow the email link to create a new password."

**Action:**
> User: "Check my subscription"
> Bot: "Your current plan is **Pro** (active). Next billing date: 2024-04-15. Amount: $49.00/month."

**Escalation:**
> User: "I want to talk to a real person"
> Bot: "Of course. I've created ticket **TKT-20240315-0001** and a human agent will follow up shortly."

---

## Tech Stack

| Layer | Technology |
|---|---|
| LLM | Groq Llama 3.3 70B |
| Agent orchestration | LangGraph StateGraph |
| Embeddings | HuggingFace all-MiniLM-L6-v2 |
| Vector store | FAISS (CPU, local) |
| Database | SQLite via SQLAlchemy 2.x |
| API | FastAPI + Pydantic v2 |
| Frontend | Streamlit |
| Logging | Structlog |
| Container | Docker + Docker Compose |
