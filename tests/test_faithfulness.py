"""Smoke + control tests for the CoT-faithfulness audit."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from cotfaith import CHECKS, audit, metrics  # noqa: E402
from cotfaith.checks import run_checks  # noqa: E402
from cotfaith.ledger import load_runs  # noqa: E402

RUNS = REPO / "data" / "runs.yaml"


def test_runs_load():
    runs = load_runs(RUNS)
    assert len(runs) >= 4


def test_checks_return_bool_detail():
    for run in load_runs(RUNS):
        res = run_checks(run)
        assert set(res) == set(CHECKS)
        for ok, detail in res.values():
            assert isinstance(ok, bool) and isinstance(detail, str)


def test_planted_unfaithful_all_caught():
    """Every planted-unfaithful control must fail at least one check (canary)."""
    m = metrics.audit_runs(load_runs(RUNS))
    assert m["n_planted"] >= 4
    assert m["planted_detection_recall"] == 1.0


def test_faithful_runs_pass():
    for run in load_runs(RUNS):
        if run.label == "faithful":
            res = run_checks(run)
            assert all(ok for ok, _ in res.values()), f"{run.run_id} should be faithful"


def test_audit_chain(tmp_path):
    led = tmp_path / "l.ndjson"
    audit.emit("a", "j", {"x": 1}, ledger_path=led)
    audit.emit("b", "j", {"y": 2}, ledger_path=led)
    ok, n = audit.verify(led)
    assert ok and n == 2


def test_outcome_calibration_loads_and_scores():
    from cotfaith.outcome_calibration import ece, load_decisions
    decs = load_decisions(REPO / "data" / "decisions.yaml")
    assert len(decs) >= 8 and decs == sorted(decs, key=lambda d: d.order)
    m = ece(decs)
    assert 0.0 <= m["ece"] <= 1.0 and m["n"] == len(decs)


def test_outcome_calibration_trend_improves():
    """Synthetic ledger: late window should be better calibrated than early."""
    from cotfaith.outcome_calibration import load_decisions, temporal_trend
    t = temporal_trend(load_decisions(REPO / "data" / "decisions.yaml"))
    assert t["late"]["ece"] < t["early"]["ece"]      # calibration improves
    assert t["ece_delta_late_minus_early"] < 0
