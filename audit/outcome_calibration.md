# Outcome-calibration monitor

Generated: 2026-06-02T23:50:26Z

Is the agent/critic's stated confidence calibrated against realized outcomes — and does it improve as decision-outcome experience accumulates? Confidence-ECE over the (decision, outcome) ledger, split early vs late by arrival order.

## Windows

| Window | n | ECE | mean conf | accuracy | gap |
|---|---|---|---|---|---|
| overall | 24 | 0.276 | 0.80 | 0.58 | +0.21 |
| early | 12 | 0.411 | 0.91 | 0.50 | +0.41 |
| late | 12 | 0.200 | 0.68 | 0.67 | +0.02 |

**ECE delta (late − early): -0.211 → calibration improving with experience.**

## Reliability (overall)

| confidence bin | n | mean conf | accuracy |
|---|---|---|---|
| 0.4-0.5 | 2 | 0.50 | 0.00 |
| 0.5-0.6 | 4 | 0.57 | 0.50 |
| 0.6-0.7 | 1 | 0.70 | 1.00 |
| 0.7-0.8 | 2 | 0.78 | 1.00 |
| 0.8-0.9 | 9 | 0.88 | 0.67 |
| 0.9-1.0 | 6 | 0.94 | 0.50 |

## What this does not establish

Synthetic decision-outcome ledger (clean-room); pure-Python confidence-ECE. The early-vs-late split is a single, small temporal comparison — shows the monitor works, not a statistically powered claim. On a live substrate this consumes real (decision, outcome) pairs from the chained ledger; the realized outcome must be verified ground truth, never the agent's own later judgment (feedback-loop guard).

## Reproduce

```bash
python scripts/run_outcome_calibration.py
```
