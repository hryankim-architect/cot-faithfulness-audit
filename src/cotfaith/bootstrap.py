"""Percentile bootstrap CIs over runs (deterministic, stdlib only).

The headline rates (planted-detection recall, run-level faithful rate) are point
estimates on a small set of runs. Resampling the runs with replacement and
recomputing gives a percentile CI — so a single demo rate is reported as an
estimate with uncertainty. On a tiny control set a perfect recall yields a CI of
[1.00, 1.00]: that reflects *zero observed misses*, not a guarantee — the small N
is the real limitation, not the interval width.
"""
from __future__ import annotations

import random
from collections.abc import Callable, Sequence
from typing import Any


def percentile_ci(samples: list[float], alpha: float = 0.05) -> tuple[float, float]:
    """Two-sided (1-alpha) percentile interval from bootstrap replicates."""
    s = sorted(samples)
    n = len(s)
    if n == 0:
        return (float("nan"), float("nan"))
    lo_i = max(0, int((alpha / 2.0) * n))
    hi_i = min(n - 1, int((1.0 - alpha / 2.0) * n))
    return (s[lo_i], s[hi_i])


def bootstrap_runs(
    runs: Sequence[Any],
    metric_fn: Callable[[Sequence[Any]], float | None],
    *,
    n_boot: int = 2000,
    seed: int = 0,
    alpha: float = 0.05,
) -> dict[str, Any]:
    """Bootstrap a scalar metric over ``runs``.

    ``metric_fn`` maps a (resampled) run list to a scalar, or None when undefined
    (e.g. a resample with no planted controls); None replicates are dropped.
    Deterministic given ``seed``.
    """
    n = len(runs)
    point = metric_fn(runs) if n else None
    if n == 0:
        return {"point": point, "ci_low": None, "ci_high": None, "n_boot": 0, "alpha": alpha}
    rng = random.Random(seed)
    reps: list[float] = []
    for _ in range(n_boot):
        sample = [runs[rng.randrange(n)] for _ in range(n)]
        v = metric_fn(sample)
        if v is not None and v == v:  # drop None and NaN
            reps.append(v)
    lo, hi = percentile_ci(reps, alpha) if reps else (None, None)
    return {"point": point, "ci_low": lo, "ci_high": hi, "n_boot": len(reps), "alpha": alpha}
