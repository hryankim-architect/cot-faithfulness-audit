#!/usr/bin/env python3
"""Outcome-calibration monitor over the (decision, realized-outcome) ledger.

Reports whether the agent/critic's stated confidence is calibrated against
realized outcomes (confidence-ECE + reliability), and whether calibration
improves as decision-outcome experience accumulates (early vs late window).

Reproduce:  python scripts/run_outcome_calibration.py
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from cotfaith import audit  # noqa: E402
from cotfaith.outcome_calibration import load_decisions, temporal_trend  # noqa: E402

AUDIT = REPO / "audit"
JOB_ID = "outcome-calibration-v0.3"


def main() -> int:
    decisions = load_decisions(REPO / "data" / "decisions.yaml")
    t = temporal_trend(decisions)
    o, e, late = t["overall"], t["early"], t["late"]
    delta = t["ece_delta_late_minus_early"]

    def fmt(label, m):
        return (f"  {label:8s} n={m['n']:2d}  ECE={m['ece']:.3f}  "
                f"conf={m['mean_conf']:.2f} vs acc={m['accuracy']:.2f} "
                f"(gap {m['gap']:+.2f})")

    print(f"=== outcome-calibration monitor (n={o['n']} decisions) ===")
    print(fmt("overall", o))
    print(fmt("early", e))
    print(fmt("late", late))
    trend = ("improving" if delta < -0.02 else "worsening" if delta > 0.02 else "flat")
    print(f"  ECE delta (late - early): {delta:+.3f}  -> calibration {trend} with experience")

    AUDIT.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: UP017
    rel = "\n".join(
        f"| {b['lo']:.1f}-{b['hi']:.1f} | {b['count']} | {b['mean_conf']:.2f} | {b['accuracy']:.2f} |"
        for b in o["bins"]
    )
    (AUDIT / "outcome_calibration.md").write_text(
        "# Outcome-calibration monitor\n\n"
        f"Generated: {ts}\n\n"
        "Is the agent/critic's stated confidence calibrated against realized "
        "outcomes — and does it improve as decision-outcome experience accumulates? "
        "Confidence-ECE over the (decision, outcome) ledger, split early vs late by "
        "arrival order.\n\n"
        "## Windows\n\n"
        "| Window | n | ECE | mean conf | accuracy | gap |\n|---|---|---|---|---|---|\n"
        f"| overall | {o['n']} | {o['ece']:.3f} | {o['mean_conf']:.2f} | {o['accuracy']:.2f} | {o['gap']:+.2f} |\n"
        f"| early | {e['n']} | {e['ece']:.3f} | {e['mean_conf']:.2f} | {e['accuracy']:.2f} | {e['gap']:+.2f} |\n"
        f"| late | {late['n']} | {late['ece']:.3f} | {late['mean_conf']:.2f} | {late['accuracy']:.2f} | {late['gap']:+.2f} |\n\n"
        f"**ECE delta (late − early): {delta:+.3f} → calibration {trend} with experience.**\n\n"
        "## Reliability (overall)\n\n"
        "| confidence bin | n | mean conf | accuracy |\n|---|---|---|---|\n" + rel + "\n\n"
        "## Honest scope\n\n"
        "Synthetic decision-outcome ledger (clean-room); pure-Python confidence-ECE. "
        "The early-vs-late split is a single, small temporal comparison — illustrative "
        "of the monitor, not a powered claim. On the live substrate this consumes real "
        "(decision, outcome) pairs from the hash-chained ledger; the realized outcome "
        "must be a verified ground truth, never the agent's own later judgment "
        "(feedback-loop guard).\n\n"
        "## Reproduce\n\n```bash\npython scripts/run_outcome_calibration.py\n```\n"
    )
    print(f"\nWrote {AUDIT / 'outcome_calibration.md'}")
    audit.emit("outcome_calibration", JOB_ID, fields={
        "n": o["n"], "ece_overall": o["ece"], "ece_early": e["ece"],
        "ece_late": late["ece"], "ece_delta_late_minus_early": delta,
    }, ledger_path=AUDIT / "local-demo.ndjson")
    ok, n = audit.verify(AUDIT / "local-demo.ndjson")
    print(f"  audit chain: {'OK' if ok else 'BROKEN'} ({n} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
