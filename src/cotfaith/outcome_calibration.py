"""Outcome-calibration monitor: is the agent/critic's stated confidence
calibrated against realized outcomes — and does calibration improve as
decision-outcome experience accumulates?

Pure-Python (no numpy) confidence-ECE + reliability bins + an early-vs-late
temporal trend over the (decision, outcome) ledger. This extends the portfolio's
"judge from experience" idea to the decision-outcome axis: accumulate real
outcomes and check whether the system's self-assessed confidence earns trust.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass(frozen=True)
class Decision:
    order: int
    confidence: float
    correct: int  # 1 if the decision turned out correct, else 0


def load_decisions(path: Path) -> list[Decision]:
    raw = yaml.safe_load(Path(path).read_text())
    out = [
        Decision(order=int(d["order"]), confidence=float(d["confidence"]),
                 correct=int(d["correct"]))
        for d in raw["decisions"]
    ]
    return sorted(out, key=lambda d: d.order)


def ece(decisions: list[Decision], n_bins: int = 10) -> dict:
    """Confidence-ECE + over/under-confidence gap + reliability bins."""
    if not decisions:
        return {"ece": float("nan"), "mean_conf": float("nan"),
                "accuracy": float("nan"), "gap": float("nan"), "n": 0, "bins": []}
    n = len(decisions)
    edges = [i / n_bins for i in range(n_bins + 1)]
    bins = []
    ece_val = 0.0
    for b in range(n_bins):
        lo, hi = edges[b], edges[b + 1]
        sel = [d for d in decisions
               if (lo < d.confidence <= hi) or (b == 0 and d.confidence <= hi)]
        if not sel:
            continue
        cnt = len(sel)
        mc = sum(d.confidence for d in sel) / cnt
        acc = sum(d.correct for d in sel) / cnt
        ece_val += (cnt / n) * abs(mc - acc)
        bins.append({"lo": lo, "hi": hi, "count": cnt, "mean_conf": mc, "accuracy": acc})
    mean_conf = sum(d.confidence for d in decisions) / n
    accuracy = sum(d.correct for d in decisions) / n
    return {"ece": ece_val, "mean_conf": mean_conf, "accuracy": accuracy,
            "gap": mean_conf - accuracy, "n": n, "bins": bins}


def temporal_trend(decisions: list[Decision], n_bins: int = 10) -> dict:
    """Split by arrival order into early vs late halves; ECE of each + overall.

    A lower late-window ECE means confidence got better calibrated as
    decision-outcome experience accumulated.
    """
    ordered = sorted(decisions, key=lambda d: d.order)
    mid = len(ordered) // 2
    early, late = ordered[:mid], ordered[mid:]
    e_early, e_late = ece(early, n_bins), ece(late, n_bins)
    return {
        "overall": ece(ordered, n_bins),
        "early": e_early,
        "late": e_late,
        "ece_delta_late_minus_early": e_late["ece"] - e_early["ece"],
    }
