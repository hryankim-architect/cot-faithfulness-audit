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

## Planned

- [ ] **Semantic (LLM-judge) action-outcome check** — beyond rule-based string grounding; composes with `honesty-rubric-eval`'s judge
- [ ] **Counterfactual flip-rate probe** — does perturbing the stated rationale change the action? (a stronger faithfulness signal than consistency alone)

---

## Honest scope

This is **operational** faithfulness (stated reasoning vs demonstrated action), a
tractable proxy — **not** mechanistic faithfulness of the model's weights. Runs are
synthetic; the planted controls only prove the checks fire on the failure types they
encode. Part of the portfolio AI-safety extension (robustness / CoT-faithfulness pillar).
