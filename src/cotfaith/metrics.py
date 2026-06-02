"""Aggregate faithfulness results across runs (the deliverable)."""
from __future__ import annotations

from cotfaith import CHECKS
from cotfaith.checks import run_checks
from cotfaith.ledger import Run


def audit_runs(runs: list[Run]) -> dict:
    n = len(runs)
    per_check_pass = dict.fromkeys(CHECKS, 0)
    run_faithful = 0
    taxonomy: dict[str, int] = {}       # failed-check -> count
    caught_planted = 0
    n_planted = 0
    details = []

    for run in runs:
        res = run_checks(run)
        passed = {k: v[0] for k, v in res.items()}
        for c in CHECKS:
            per_check_pass[c] += int(passed[c])
        all_pass = all(passed.values())
        run_faithful += int(all_pass)
        for c in CHECKS:
            if not passed[c]:
                taxonomy[c] = taxonomy.get(c, 0) + 1
        is_planted = run.label.startswith("unfaithful")
        if is_planted:
            n_planted += 1
            if not all_pass:
                caught_planted += 1
        details.append({
            "run_id": run.run_id, "label": run.label, "faithful": all_pass,
            "failed": [c for c in CHECKS if not passed[c]],
        })

    return {
        "n_runs": n,
        "per_check_pass_rate": {c: per_check_pass[c] / n for c in CHECKS},
        "run_level_faithful_rate": run_faithful / n,
        "unfaithfulness_taxonomy": taxonomy,
        "planted_detection_recall": (caught_planted / n_planted) if n_planted else float("nan"),
        "n_planted": n_planted,
        "details": details,
    }
