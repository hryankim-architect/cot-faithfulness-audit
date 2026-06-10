"""v0.2 tests: bootstrap CIs, per-type detection, counterfactual flip-rate."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from cotfaith import metrics  # noqa: E402
from cotfaith.bootstrap import bootstrap_runs, clopper_pearson_ci, percentile_ci  # noqa: E402
from cotfaith.counterfactual import INJECTIONS, counterfactual_flip  # noqa: E402
from cotfaith.ledger import load_runs  # noqa: E402

RUNS = REPO / "data" / "runs.yaml"


def test_percentile_ci_orders():
    lo, hi = percentile_ci([i / 100 for i in range(100)], alpha=0.10)
    assert lo <= hi and lo <= 0.10 and hi >= 0.89


def test_percentile_ci_empty_nan():
    lo, hi = percentile_ci([])
    assert lo != lo and hi != hi


def test_bootstrap_recall_degenerates_on_all_caught():
    # The percentile bootstrap collapses to [1.00, 1.00] on an all-caught control
    # set — which is exactly why the *report* uses Clopper-Pearson for recall (see
    # test_clopper_pearson_* below). This test pins that degeneracy so the reason
    # for switching is documented, not hidden.
    runs = load_runs(RUNS)
    a = bootstrap_runs(runs, metrics.planted_detection_recall, n_boot=300, seed=0)
    b = bootstrap_runs(runs, metrics.planted_detection_recall, n_boot=300, seed=0)
    assert a == b                                   # deterministic
    assert a["point"] == 1.0
    assert a["ci_low"] == 1.0 and a["ci_high"] == 1.0  # degenerate — uninformative
    assert a["n_boot"] > 0


def test_clopper_pearson_informative_at_boundaries():
    # 4/4 must NOT read as certainty: the exact interval reaches down to ~0.40.
    lo, hi = clopper_pearson_ci(4, 4)
    assert hi == 1.0
    assert 0.36 < lo < 0.42                         # ~0.398, not 1.0
    # 0/4 is the mirror image.
    lo0, hi0 = clopper_pearson_ci(0, 4)
    assert lo0 == 0.0
    assert 0.55 < hi0 < 0.65                         # ~0.602


def test_clopper_pearson_brackets_point_and_narrows_with_n():
    # The interval brackets the point estimate and tightens as n grows.
    lo, hi = clopper_pearson_ci(3, 4)               # 0.75
    assert lo < 0.75 < hi
    lo_small, hi_small = clopper_pearson_ci(4, 4)
    lo_big, hi_big = clopper_pearson_ci(40, 40)
    assert lo_big > lo_small                         # 40/40 far tighter than 4/4
    import pytest
    with pytest.raises(ValueError):
        clopper_pearson_ci(5, 4)                     # k > n is invalid


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
