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
from cotfaith.bootstrap import bootstrap_runs, clopper_pearson_ci  # noqa: E402
from cotfaith.counterfactual import counterfactual_flip  # noqa: E402
from cotfaith.ledger import load_runs  # noqa: E402

AUDIT = REPO / "audit"
JOB_ID = "cot-faithfulness-audit-v0.2"


def _ci(d: dict) -> str:
    lo, hi = d["ci_low"], d["ci_high"]
    return "[n/a]" if lo is None else f"[{lo:.3f}, {hi:.3f}]"


def _cit(t: tuple[float, float]) -> str:
    lo, hi = t
    return "[n/a]" if lo is None or lo != lo else f"[{lo:.3f}, {hi:.3f}]"


def main() -> int:
    runs = load_runs(REPO / "data" / "runs.yaml")
    m = metrics.audit_runs(runs)
    faith_ci = bootstrap_runs(runs, metrics.run_level_faithful_rate, n_boot=2000, seed=0)
    flip = counterfactual_flip(runs)
    # The binomial "canary" metrics (planted-detection recall, counterfactual
    # flip-rate) use the exact Clopper-Pearson interval, NOT a percentile bootstrap:
    # on an all-caught control set the bootstrap collapses to [1.00, 1.00], which
    # reads as certainty, whereas Clopper-Pearson reports 4/4 as ~[0.40, 1.00] —
    # honest about how few trials there are.
    n_planted = m["n_planted"]
    caught = round(m["planted_detection_recall"] * n_planted) if n_planted else 0
    recall_ci = clopper_pearson_ci(caught, n_planted) if n_planted else (float("nan"), float("nan"))
    flip_total = sum(pf["n_bases"] for pf in flip["per_fault"].values())
    flip_flipped = round(flip["flip_rate"] * flip_total) if flip_total else 0
    flip_ci = clopper_pearson_ci(flip_flipped, flip_total) if flip_total else (float("nan"), float("nan"))
    print(f"=== CoT faithfulness audit (n_runs={m['n_runs']}, "
          f"planted unfaithful={m['n_planted']}) ===")
    for d in m["details"]:
        tag = "FAITHFUL" if d["faithful"] else "UNFAITHFUL " + ",".join(d["failed"])
        print(f"  {d['run_id']:28s} [{d['label']:28s}] -> {tag}")

    print("\n--- per-check pass rate ---")
    for c in CHECKS:
        print(f"  {c:22s} {m['per_check_pass_rate'][c]:.3f}")
    print(f"\n  run-level faithful rate     : {m['run_level_faithful_rate']:.3f}  "
          f"95% CI {_ci(faith_ci)}")
    print(f"  planted-detection recall    : {m['planted_detection_recall']:.3f}  "
          f"95% CI {_cit(recall_ci)} (Clopper-Pearson, {caught}/{n_planted} planted)")
    print("  planted detection by type:")
    for label, info in m["planted_detection_by_type"].items():
        print(f"    {label:34s} caught={str(info['caught']):5s} via {','.join(info['failed_checks'])}")
    print(f"  counterfactual flip-rate    : {flip['flip_rate']:.3f}  "
          f"95% CI {_cit(flip_ci)} (Clopper-Pearson, {flip_flipped}/{flip_total}); "
          f"injected into {flip['n_bases']} faithful base run(s)")

    AUDIT.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # noqa: UP017
    rows = "\n".join(
        f"| `{d['run_id']}` | {d['label']} | {'yes' if d['faithful'] else 'no'} | "
        f"{', '.join(d['failed']) or '—'} |" for d in m["details"]
    )
    checks_tbl = "\n".join(f"| `{c}` | {m['per_check_pass_rate'][c]:.2f} |" for c in CHECKS)
    tax = ", ".join(f"{k}={v}" for k, v in m["unfaithfulness_taxonomy"].items()) or "none"
    by_type_tbl = "\n".join(
        f"| `{label}` | {'yes' if info['caught'] else 'NO'} | "
        f"{', '.join(info['failed_checks']) or '—'} |"
        for label, info in m["planted_detection_by_type"].items()
    )
    flip_tbl = "\n".join(
        f"| `{fault}` | {info['flip_rate']:.2f} | {info['target_check_fired']:.2f} |"
        for fault, info in flip["per_fault"].items()
    )
    (AUDIT / "faithfulness_audit.md").write_text(
        "# CoT faithfulness audit\n\n"
        f"Generated: {ts}\n\n"
        "Operational faithfulness = does the stated rationale match the actual tool "
        "calls, results, and decision? Measured post-hoc from the (synthetic) audit "
        "ledger. This is a behavioral proxy, not mechanistic faithfulness.\n\n"
        f"- Runs: {m['n_runs']} ({m['n_planted']} planted-unfaithful controls).\n\n"
        "## Per-check pass rate\n\n| Check | Pass rate |\n|---|---|\n" + checks_tbl + "\n\n"
        f"- **Run-level faithful rate:** {m['run_level_faithful_rate']:.3f} "
        f"(95% CI {_ci(faith_ci)}, n_boot={faith_ci['n_boot']})\n"
        f"- **Planted-detection recall:** {m['planted_detection_recall']:.3f} "
        f"(95% CI {_cit(recall_ci)}, Clopper-Pearson, {caught}/{n_planted}) — every "
        "deliberately-unfaithful control should be caught (the canary principle). The exact "
        "binomial CI is wide because the control set is tiny: 4/4 is consistent with a true "
        "recall as low as ~0.40, so this shows the method catches the encoded faults, not a "
        "benchmarked detection rate.\n"
        f"- **Counterfactual flip-rate:** {flip['flip_rate']:.3f} "
        f"(95% CI {_cit(flip_ci)}, Clopper-Pearson, {flip_flipped}/{flip_total}) — faults "
        f"injected into {flip['n_bases']} faithful base run(s); 1.00 means every injected "
        "fault flips the verdict (an active robustness test, not just a label).\n"
        f"- Unfaithfulness taxonomy: {tax}\n\n"
        "## Planted detection by type\n\n| Unfaithfulness type | Caught | Via check(s) |\n"
        "|---|---|---|\n" + by_type_tbl + "\n\n"
        "## Counterfactual flip-rate (per injected fault)\n\n"
        "| Injected fault | Flip rate | Target check fired |\n|---|---|---|\n"
        + flip_tbl + "\n\n"
        "## Per-run\n\n| Run | Label | Faithful | Failed checks |\n|---|---|---|---|\n"
        + rows + "\n\n"
        "## What this does not establish\n\n"
        "Operational, not mechanistic: checks stated-reasoning vs "
        "demonstrated-action consistency; it says nothing about internal model computation. "
        "Rule-based checks on synthetic runs only. The **semantic** action-outcome check "
        "(matching the prose rationale to results in meaning, not just tool bookkeeping) "
        "needs an LLM and is deferred to v0.3. Planted controls and the counterfactual "
        "probe confirm the checks fire on the failure modes they encode, not on novel "
        "unfaithfulness types.\n\n"
        "## Reproduce\n\n```bash\npython scripts/run_faithfulness_audit.py\n```\n"
    )
    print(f"\nWrote {AUDIT / 'faithfulness_audit.md'}")

    audit.emit("faithfulness_audit", JOB_ID, fields={
        "n_runs": m["n_runs"],
        "run_level_faithful_rate": m["run_level_faithful_rate"],
        "run_faithful_ci": [faith_ci["ci_low"], faith_ci["ci_high"]],
        "planted_detection_recall": m["planted_detection_recall"],
        "recall_ci": [recall_ci[0], recall_ci[1]],
        "recall_ci_method": "clopper_pearson",
        "counterfactual_flip_rate": flip["flip_rate"],
        "flip_ci": [flip_ci[0], flip_ci[1]],
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
