"""Evaluation runner — runs the JSONL dataset through the agent and reports metrics."""

import sys
import json
import time
import argparse
from pathlib import Path

# Ensure project root is on path
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from tqdm import tqdm
from app.db.init_db import init_db
from app.db.seed import seed
from app.db.session import SessionLocal
from app.agent.graph import run_agent
from app.eval.metrics import EvalResult, compute_metrics, format_report
from app.utils.config import get_settings
from app.utils.logging import configure_logging, get_logger

logger = get_logger("eval.runner")


def load_dataset(path: str) -> list[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def run_evaluation(
    max_samples: int | None = None,
    output_file: str | None = None,
    deduplicate: bool = True,
) -> None:
    configure_logging()
    settings = get_settings()
    settings.validate_api_key()

    print("\n[*] Initializing database...")
    init_db()
    seed()

    dataset_path = settings.faq_dataset_path
    print(f"[*] Loading dataset: {dataset_path}")
    records = load_dataset(dataset_path)

    # Deduplicate by user_query to reduce API calls
    if deduplicate:
        seen_queries: set[str] = set()
        deduped = []
        for r in records:
            q = r["user_query"].lower().strip()
            if q not in seen_queries:
                seen_queries.add(q)
                deduped.append(r)
        records = deduped
        print(f"[*] Deduplicated to {len(records)} unique queries")

    if max_samples:
        records = records[:max_samples]
        print(f"[*] Evaluating {len(records)} samples (--max-samples={max_samples})")
    else:
        print(f"[*] Evaluating all {len(records)} samples")

    results: list[EvalResult] = []
    db = SessionLocal()
    conv_id = "eval_run_001"

    try:
        for i, record in enumerate(tqdm(records, desc="Evaluating")):
            start = time.perf_counter()
            try:
                state = run_agent(
                    user_message=record["user_query"],
                    user_id="eval_user",
                    conversation_id=f"{conv_id}_{i}",
                    db=db,
                    history=[],
                )
                latency_ms = (time.perf_counter() - start) * 1000

                predicted_intent = state.get("intent", "unknown")
                predicted_escalate = state.get("escalated", False)

                results.append(EvalResult(
                    id=record["id"],
                    expected_intent=record["intent"],
                    predicted_intent=predicted_intent,
                    expected_escalate=record.get("should_escalate", False),
                    predicted_escalate=predicted_escalate,
                    latency_ms=latency_ms,
                ))

            except Exception as e:
                latency_ms = (time.perf_counter() - start) * 1000
                logger.error("Eval sample failed", id=record["id"], error=str(e))
                results.append(EvalResult(
                    id=record["id"],
                    expected_intent=record["intent"],
                    predicted_intent="error",
                    expected_escalate=record.get("should_escalate", False),
                    predicted_escalate=False,
                    latency_ms=latency_ms,
                ))

    finally:
        db.close()

    metrics = compute_metrics(results)
    report = format_report(metrics, results)

    print("\n" + report)

    if output_file:
        out_path = Path(output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(report)
        print(f"\n[OK] Report saved to: {out_path}")

    # Also save JSON metrics
    json_path = Path(output_file).with_suffix(".json") if output_file else Path("eval_results.json")
    json_path.write_text(json.dumps(metrics.to_dict(), indent=2))
    print(f"[*] JSON metrics: {json_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate the TaskFlow support agent")
    parser.add_argument("--max-samples", type=int, default=None,
                        help="Maximum number of samples to evaluate")
    parser.add_argument("--output", type=str, default="eval_report.txt",
                        help="Output file path for the text report")
    parser.add_argument("--no-dedup", action="store_true",
                        help="Disable deduplication of queries")
    args = parser.parse_args()

    run_evaluation(
        max_samples=args.max_samples,
        output_file=args.output,
        deduplicate=not args.no_dedup,
    )
