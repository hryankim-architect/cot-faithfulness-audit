#!/usr/bin/env python3
"""Audit CoT faithfulness over a set of agent runs (synthetic ledger in v0.1).

Reports the four per-check pass rates, the run-level faithful rate, the
unfaithfulness taxonomy, and — using the planted-unfaithful controls — whether
the audit actually catches unfaithfulness (detection recall).

Reproduce:  python scripts/run_faithfulness_audit.py
"""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from cotfaith import CHECKS, audit, metrics  # noqa: E402
from cotfaith.ledger import load_runs  # noqa: E402

AUDIT = REPO / "audit"
JOB_ID = "cot-faithfulness-audit-v0.1"


def main() -> int:
    runs = load_runs(REPO / "data" / "runs.yaml")
    m = metrics.audit_runs(runs)
    print(f"=== CoT faithfulness audit (n_runs={m['n_runs']}, "
          f"planted unfaithful={m['n_planted']}) ===")
    for d in m["details"]:
        tag = "FAITHFUL" if d["faithful"] else "UNFAITHFUL " + ",".join(d["failed"])
        print(f"  {d['run_id']:28s} [{d['label']:28s}] -> {tag}")

    print("\n--- per-check pass rate ---")
    for c in CHECKS:
        print(f"  {c:22s} {m['per_check_pass_rate'][c]:.3f}")
    print(f"\n  run-level faithful rate     : {m['run_level_faithful_rate']:.3f}")
    print(f"  planted-detection recall    : {m['planted_detection_recall']:.3f} "
          f"(caught / {m['n_planted']} planted)")

    AUDIT.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: UP017
    rows = "\n".join(
        f"| `{d['run_id']}` | {d['label']} | {'yes' if d['faithful'] else 'no'} | "
        f"{', '.join(d['failed']) or '—'} |" for d in m["details"]
    )
    checks_tbl = "\n".join(f"| `{c}` | {m['per_check_pass_rate'][c]:.2f} |" for c in CHECKS)
    tax = ", ".join(f"{k}={v}" for k, v in m["unfaithfulness_taxonomy"].items()) or "none"
    (AUDIT / "faithfulness_audit.md").write_text(
        "# CoT faithfulness audit\n\n"
        f"Generated: {ts}\n\n"
        "Operational faithfulness = does the stated rationale match the actual tool "
        "calls, results, and decision? Measured post-hoc from the (synthetic) audit "
        "ledger. This is a behavioral proxy, not mechanistic faithfulness.\n\n"
        f"- Runs: {m['n_runs']} ({m['n_planted']} planted-unfaithful controls).\n\n"
        "## Per-check pass rate\n\n| Check | Pass rate |\n|---|---|\n" + checks_tbl + "\n\n"
        f"- **Run-level faithful rate:** {m['run_level_faithful_rate']:.3f}\n"
        f"- **Planted-detection recall:** {m['planted_detection_recall']:.3f} "
        "(every deliberately-unfaithful control should be caught — the canary "
        "principle applied to faithfulness)\n"
        f"- Unfaithfulness taxonomy: {tax}\n\n"
        "## Per-run\n\n| Run | Label | Faithful | Failed checks |\n|---|---|---|---|\n"
        + rows + "\n\n"
        "## What this does not establish\n\n"
        "Operational, not mechanistic: checks stated-reasoning vs "
        "demonstrated-action consistency; it says nothing about internal model computation. "
        "v0.1 rule-based checks on synthetic runs only. The semantic "
        "action-outcome check and counterfactual flip-rate probe are v0.2. "
        "Planted controls confirm the checks fire on the failure modes they "
        "encode, not on novel unfaithfulness types.\n\n"
        "## Reproduce\n\n```bash\npython scripts/run_faithfulness_audit.py\n```\n"
    )
    print(f"\nWrote {AUDIT / 'faithfulness_audit.md'}")

    audit.emit("faithfulness_audit", JOB_ID, fields={
        "n_runs": m["n_runs"],
        "run_level_faithful_rate": m["run_level_faithful_rate"],
        "planted_detection_recall": m["planted_detection_recall"],
    }, ledger_path=AUDIT / "local-demo.ndjson")
    ok, n = audit.verify(AUDIT / "local-demo.ndjson")
    print(f"  audit chain: {'OK' if ok else 'BROKEN'} ({n} entries)")

    # Fail loudly if a planted-unfaithful control slipped through (canary).
    if m["n_planted"] and m["planted_detection_recall"] < 1.0:
        sys.stderr.write("::error::a planted-unfaithful control was NOT caught\n")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
