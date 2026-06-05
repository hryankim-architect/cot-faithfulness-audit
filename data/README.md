# Dataset — CoT-faithfulness audit

Clean-room, synthetic data. No real agent logs are included; these are
hand-built stand-ins for the substrate audit ledger, designed so each planted
failure mode trips exactly one faithfulness check.

## Files

- **`runs.yaml`** — 6 agent runs, **2 faithful + 4 planted-unfaithful**, one
  planted run per failure mode (`plan_drift`, `ignored_evidence`,
  `hidden_action`, `fabricated_citation`). Each run carries:
  - `run_id`, `rationale`, `plan_tools`,
  - `tool_calls` (`name` + `result.status` in
    `evidence` / `no_evidence` / `refuted` / `ok`),
  - `assertion` (`positive` / `declined`), `citations`, and a `label`.

  The four checks — plan↔action match, no hidden action, action↔outcome match,
  citation grounding — pass on the faithful runs, and each planted run trips the
  matching check. That is the canary property the metrics assert
  (planted-detection recall = 1.0).

- **`decisions.yaml`** — 24 `(order, confidence, correct)` records for the
  outcome-calibration monitor: confidence-ECE over realized outcomes, split
  early vs late by arrival `order`, to test whether calibration improves as
  decision-outcome experience accumulates.

## Scope / honesty

Synthetic and small by design — a **methodology seed, not a benchmark**.
"Operational faithfulness" (stated rationale vs demonstrated actions) is a
behavioral proxy, **not** mechanistic faithfulness of model weights. See
[`../docs/what-is-out-of-scope.md`](../docs/what-is-out-of-scope.md).
