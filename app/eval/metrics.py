"""Evaluation metrics computation."""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class EvalResult:
    """Single evaluation result for one dataset entry."""
    id: str
    expected_intent: str
    predicted_intent: str
    expected_escalate: bool
    predicted_escalate: bool
    latency_ms: float
    correct_intent: bool = field(init=False)
    correct_escalation: bool = field(init=False)

    def __post_init__(self):
        self.correct_intent = (
            self.expected_intent.lower() == self.predicted_intent.lower()
        )
        self.correct_escalation = (
            self.expected_escalate == self.predicted_escalate
        )


@dataclass
class AggregateMetrics:
    total: int = 0
    intent_correct: int = 0
    escalation_correct: int = 0
    escalated_count: int = 0
    resolved_count: int = 0
    total_latency_ms: float = 0.0
    errors: int = 0

    @property
    def intent_accuracy(self) -> float:
        return self.intent_correct / self.total if self.total else 0.0

    @property
    def escalation_accuracy(self) -> float:
        return self.escalation_correct / self.total if self.total else 0.0

    @property
    def escalation_rate(self) -> float:
        return self.escalated_count / self.total if self.total else 0.0

    @property
    def autonomous_resolution_rate(self) -> float:
        return self.resolved_count / self.total if self.total else 0.0

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.total if self.total else 0.0

    @property
    def error_rate(self) -> float:
        return self.errors / self.total if self.total else 0.0

    def to_dict(self) -> dict:
        return {
            "total_samples": self.total,
            "intent_accuracy": round(self.intent_accuracy, 4),
            "escalation_accuracy": round(self.escalation_accuracy, 4),
            "escalation_rate": round(self.escalation_rate, 4),
            "autonomous_resolution_rate": round(self.autonomous_resolution_rate, 4),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "error_rate": round(self.error_rate, 4),
            "errors": self.errors,
        }


def compute_metrics(results: list[EvalResult]) -> AggregateMetrics:
    agg = AggregateMetrics(total=len(results))
    for r in results:
        if r.correct_intent:
            agg.intent_correct += 1
        if r.correct_escalation:
            agg.escalation_correct += 1
        if r.predicted_escalate:
            agg.escalated_count += 1
        else:
            agg.resolved_count += 1
        agg.total_latency_ms += r.latency_ms
    return agg


def format_report(metrics: AggregateMetrics, results: list[EvalResult]) -> str:
    lines = [
        "=" * 60,
        "  TaskFlow Support Bot — Evaluation Report",
        "=" * 60,
        f"  Total samples:              {metrics.total}",
        f"  Intent accuracy:            {metrics.intent_accuracy:.1%}",
        f"  Escalation accuracy:        {metrics.escalation_accuracy:.1%}",
        f"  Autonomous resolution rate: {metrics.autonomous_resolution_rate:.1%}",
        f"  Escalation rate:            {metrics.escalation_rate:.1%}",
        f"  Avg latency:                {metrics.avg_latency_ms:.0f} ms",
        f"  Errors:                     {metrics.errors} ({metrics.error_rate:.1%})",
        "=" * 60,
    ]

    # Per-intent breakdown
    intent_groups: dict[str, dict] = {}
    for r in results:
        g = intent_groups.setdefault(r.expected_intent, {"correct": 0, "total": 0})
        g["total"] += 1
        if r.correct_intent:
            g["correct"] += 1

    lines.append("  Per-intent accuracy:")
    for intent, g in sorted(intent_groups.items()):
        acc = g["correct"] / g["total"] if g["total"] else 0
        lines.append(f"    {intent:<12} {acc:.1%}  ({g['correct']}/{g['total']})")

    lines.append("=" * 60)

    # First 5 failures
    failures = [r for r in results if not r.correct_intent][:5]
    if failures:
        lines.append("  Sample misclassifications:")
        for f in failures:
            lines.append(
                f"    [{f.id}] expected={f.expected_intent} "
                f"got={f.predicted_intent} latency={f.latency_ms:.0f}ms"
            )
        lines.append("=" * 60)

    return "\n".join(lines)
