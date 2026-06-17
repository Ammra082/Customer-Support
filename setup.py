"""Quick startup helper — initialises DB, seeds data, and builds FAISS index."""

import sys
from pathlib import Path

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))


def main():
    print("=" * 55)
    print("  TaskFlow Support Bot — Quick Start")
    print("=" * 55)

    # 1. Check .env
    env_file = ROOT / ".env"
    if not env_file.exists():
        print("❌  .env file not found. Copy .env.example to .env and add your GROQ_API_KEY.")
        sys.exit(1)

    from app.utils.config import get_settings
    settings = get_settings()

    if not settings.groq_api_key:
        print("❌  GROQ_API_KEY is not set in .env.")
        print("    Get a free key at https://console.groq.com")
        sys.exit(1)
    else:
        print("✅  Groq API key found.")

    # 2. Init DB
    print("\n🔧  Initializing database...")
    from app.db.init_db import init_db
    init_db()

    # 3. Seed
    print("🌱  Seeding demo data...")
    from app.db.seed import seed
    seed()

    # 4. Build FAISS index
    faiss_path = Path(settings.faiss_index_path)
    if faiss_path.exists() and any(faiss_path.iterdir()):
        print("✅  FAISS index already exists — skipping ingest.")
    else:
        print("📚  Building FAISS index (this may take ~30s on first run)...")
        from app.rag.ingest import ingest
        count = ingest()
        print(f"✅  Indexed {count} documents.")

    print("\n" + "=" * 55)
    print("  All done! Start the application:")
    print()
    print("  Terminal 1 (API):")
    print("    uvicorn app.main:app --reload")
    print()
    print("  Terminal 2 (Frontend):")
    print("    streamlit run app/ui/streamlit_app.py")
    print()
    print("  API docs: http://localhost:8000/docs")
    print("  Chat UI:  http://localhost:8501")
    print("=" * 55)


if __name__ == "__main__":
    main()
