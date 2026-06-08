# Roadmap — `cot-faithfulness-audit`

Audits **operational chain-of-thought faithfulness for tool-using agents**: the
stated rationale vs what the agent *actually did* (tool calls, results, decision),
read post-hoc from the hash-chained audit ledger. Short and dated so the repo's
state is legible. Operational, not mechanistic; synthetic runs — see
[`docs/what-is-out-of-scope.md`](docs/what-is-out-of-scope.md).

---

## v0.1 — operational faithfulness audit (shipped: tag `v0.1` + Release)

*Released as a single `v0.1` tag. The README uses phase labels (it calls the
outcome-calibration monitor "v0.3" and the semantic/counterfactual probes "v0.2");
this ROADMAP instead groups by what is actually shipped vs planned.*

**Goal**: catch — cheaply, from the ledger both sides already write to — when an
agent's stated reasoning diverges from its demonstrated actions.

- [x] Synthetic runs (`data/runs.yaml`): faithful runs + **planted-unfaithful controls** (plan-drift, ignored-evidence, hidden-action, fabricated-citation)
- [x] Four rule-based checks (`src/cotfaith/checks.py`): `plan_action_match`, `no_hidden_action`, `action_outcome_match`, `citation_grounding`
- [x] Aggregation (`metrics.py`): per-check pass rate, run-level faithful rate, unfaithfulness taxonomy, and **planted-detection recall** (the canary — every planted control must be caught or the run exits non-zero)
- [x] Hash-chained NDJSON ledger (the audit's own verdict is auditable)
- [x] **Outcome-calibration monitor** (`run_outcome_calibration.py`): confidence-ECE + reliability over the (decision, outcome) ledger, early-vs-late trend; realized-outcome-as-ground-truth feedback-loop guard
- [x] Test coverage (the four checks, audit_runs, tamper-detection); tag `v0.1` + GitHub Release

---

## v0.2 — uncertainty + active robustness (shipped: tag `v0.2` + Release)

**Goal**: report the headline rates as estimates with uncertainty, show where
detection lands per failure type, and actively test that the checks *flip* on
injected faults — matching the v0.2 depth of the sibling eval repos.

- [x] **Bootstrap CIs** (`src/cotfaith/bootstrap.py`) on run-level faithful rate and
  planted-detection recall (percentile, deterministic, None/NaN resamples dropped)
- [x] **Per-unfaithfulness-type detection** (`metrics.planted_detection_by_type`):
  caught? + which check(s) fired, per planted type
- [x] **Counterfactual flip-rate probe** (`src/cotfaith/counterfactual.py`): inject
  each fault into a faithful run; confirm the verdict flips and the target check fires
- [x] Runner + audit md + ledger carry the CIs, per-type table, and flip-rate; tests
  for all three; ruff + CI green

---

## Planned (v0.3)

- [ ] **Semantic (LLM-judge) action-outcome check** — beyond rule-based string
  grounding; matches the prose rationale to results in meaning; composes with
  `honesty-rubric-eval`'s judge
- [ ] Larger / more varied run set, including novel unfaithfulness types beyond the
  four planted failure modes

---

## Honest scope

This is **operational** faithfulness (stated reasoning vs demonstrated action), a
tractable proxy — **not** mechanistic faithfulness of the model's weights. Runs are
synthetic; the planted controls only prove the checks fire on the failure types they
encode. Part of the portfolio AI-safety extension (robustness / CoT-faithfulness pillar).
