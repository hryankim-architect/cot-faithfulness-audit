"""v0.2 tests: bootstrap CIs, per-type detection, counterfactual flip-rate."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from cotfaith import metrics  # noqa: E402
from cotfaith.bootstrap import bootstrap_runs, percentile_ci  # noqa: E402
from cotfaith.counterfactual import INJECTIONS, counterfactual_flip  # noqa: E402
from cotfaith.ledger import load_runs  # noqa: E402

RUNS = REPO / "data" / "runs.yaml"


def test_percentile_ci_orders():
    lo, hi = percentile_ci([i / 100 for i in range(100)], alpha=0.10)
    assert lo <= hi and lo <= 0.10 and hi >= 0.89


def test_percentile_ci_empty_nan():
    lo, hi = percentile_ci([])
    assert lo != lo and hi != hi


def test_bootstrap_recall_deterministic_and_perfect():
    runs = load_runs(RUNS)
    a = bootstrap_runs(runs, metrics.planted_detection_recall, n_boot=300, seed=0)
    b = bootstrap_runs(runs, metrics.planted_detection_recall, n_boot=300, seed=0)
    assert a == b                                   # deterministic
    assert a["point"] == 1.0
    assert a["ci_low"] == 1.0 and a["ci_high"] == 1.0  # zero observed misses
    assert a["n_boot"] > 0


def test_bootstrap_faithful_rate_has_spread():
    runs = load_runs(RUNS)
    out = bootstrap_runs(runs, metrics.run_level_faithful_rate, n_boot=500, seed=0)
    assert 0.0 <= out["ci_low"] <= out["point"] <= out["ci_high"] <= 1.0
    assert out["ci_low"] < out["ci_high"]           # 2/6 faithful -> real spread


def test_per_type_detection_all_caught():
    by_type = metrics.planted_detection_by_type(load_runs(RUNS))
    assert len(by_type) == 4
    for info in by_type.values():
        assert info["caught"] is True
        assert info["failed_checks"]                # at least one check fired


def test_counterfactual_flip_rate_perfect():
    flip = counterfactual_flip(load_runs(RUNS))
    assert flip["n_bases"] >= 1
    assert flip["flip_rate"] == 1.0                 # every injected fault flips the verdict
    for fault in INJECTIONS:
        f = flip["per_fault"][fault]
        assert f["flip_rate"] == 1.0
        assert f["target_check_fired"] == 1.0       # the intended check actually fires


def test_counterfactual_only_uses_faithful_bases():
    # A run that is already unfaithful must not be used as a clean base.
    flip = counterfactual_flip(load_runs(RUNS))
    # dataset has exactly one faithful + positive-assertion run (r1)
    assert flip["n_bases"] == 1
