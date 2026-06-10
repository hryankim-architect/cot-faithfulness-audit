"""Confidence intervals over runs (deterministic, stdlib only).

Two tools, used for different metric shapes:

- ``bootstrap_runs`` — percentile bootstrap for rates that vary across a
  heterogeneous run set (e.g. the run-level faithful rate). Good when there is
  real spread to resample.
- ``clopper_pearson_ci`` — the *exact* binomial interval for a "k of n caught"
  proportion (planted-detection recall, counterfactual flip-rate). This is the
  honest choice for the canary metrics, because a percentile bootstrap on an
  all-success control set degenerates to [1.00, 1.00] — which reads as certainty
  when the real story is "too few trials to say". Clopper-Pearson instead reports
  4/4 as [0.40, 1.00], correctly reflecting that a tiny perfect run is consistent
  with a substantially lower true rate.
"""
from __future__ import annotations

import math
import random
from collections.abc import Callable, Sequence
from typing import Any


def clopper_pearson_ci(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    """Exact (Clopper-Pearson) two-sided CI for ``k`` successes in ``n`` trials.

    Stays informative at the boundaries where a bootstrap collapses: 4/4 -> about
    [0.40, 1.00] at 95%, 0/4 -> [0.00, 0.60]. Stdlib only (binomial-tail bisection
    via ``math.comb``); deterministic.
    """
    if n == 0:
        return (float("nan"), float("nan"))
    if not 0 <= k <= n:
        raise ValueError(f"k={k} out of range [0, {n}]")
    a = alpha / 2.0

    def p_at_least(p: float, k_: int) -> float:  # P(X >= k_) for X ~ Bin(n, p)
        return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k_, n + 1))

    def p_at_most(p: float, k_: int) -> float:  # P(X <= k_)
        return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(0, k_ + 1))

    if k == 0:
        lo = 0.0
    else:
        loP, hiP = 0.0, 1.0
        for _ in range(100):
            mid = (loP + hiP) / 2.0
            if p_at_least(mid, k) < a:
                loP = mid
            else:
                hiP = mid
        lo = (loP + hiP) / 2.0
    if k == n:
        hi = 1.0
    else:
        loP, hiP = 0.0, 1.0
        for _ in range(100):
            mid = (loP + hiP) / 2.0
            if p_at_most(mid, k) > a:
                loP = mid
            else:
                hiP = mid
        hi = (loP + hiP) / 2.0
    return (lo, hi)


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
