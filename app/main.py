"""FastAPI application entry point."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.db.init_db import init_db
from app.db.seed import seed
from app.utils.config import get_settings
from app.utils.logging import configure_logging, get_logger

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic."""
    configure_logging()
    settings = get_settings()

    logger.info("TaskFlow Support Bot starting up", env=settings.app_env)

    # Initialize database tables
    init_db()

    # Seed demo data
    seed()

    # Validate Groq key early
    try:
        settings.validate_api_key()
        logger.info("Groq API key validated")
    except EnvironmentError as e:
        logger.warning("Groq API key missing", hint=str(e))

    yield

    logger.info("TaskFlow Support Bot shutting down")


app = FastAPI(
    title="TaskFlow Support Bot API",
    description=(
        "Production-grade AI customer support agent for TaskFlow. "
        "Handles FAQ retrieval, account actions, and escalation."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS — allow Streamlit frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="")

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.app_env == "development",
        log_level=settings.log_level.lower(),
    )
