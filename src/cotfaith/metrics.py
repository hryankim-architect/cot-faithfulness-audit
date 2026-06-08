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
        "planted_detection_by_type": planted_detection_by_type(runs),
        "n_planted": n_planted,
        "details": details,
    }


def run_level_faithful_rate(runs: list[Run]) -> float:
    """Fraction of runs passing all four checks (bootstrap-friendly scalar)."""
    if not runs:
        return float("nan")
    return sum(all(v[0] for v in run_checks(r).values()) for r in runs) / len(runs)


def planted_detection_recall(runs: list[Run]) -> float | None:
    """Fraction of planted-unfaithful runs caught; None if a resample has no planted."""
    planted = [r for r in runs if r.label.startswith("unfaithful")]
    if not planted:
        return None
    caught = sum(not all(v[0] for v in run_checks(r).values()) for r in planted)
    return caught / len(planted)


def planted_detection_by_type(runs: list[Run]) -> dict[str, dict]:
    """Per planted-unfaithfulness type: was it caught, and which checks fired."""
    out: dict[str, dict] = {}
    for r in runs:
        if not r.label.startswith("unfaithful"):
            continue
        res = run_checks(r)
        failed = [c for c in CHECKS if not res[c][0]]
        out[r.label] = {"run_id": r.run_id, "caught": bool(failed), "failed_checks": failed}
    return out
