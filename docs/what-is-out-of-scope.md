# What is out of scope (`cot-faithfulness-audit`)

Methods demo on synthetic data. No mechanistic faithfulness claim and no performance guarantee on real agent substrates.

- **Mechanistic faithfulness.** This measures *operational* faithfulness — does
  the stated rationale match the demonstrated tool calls, results, and decision —
  not the faithfulness of the model's internal computation/weights.
- **Coverage of novel unfaithfulness.** The planted-unfaithful controls prove the
  checks fire on the failure types they encode (plan-drift, ignored-evidence,
  hidden-action, fabricated-citation). They do not prove coverage of unanticipated
  unfaithfulness; that gap is unmeasured by design.
- **Semantic action-outcome judgment.** v0.1 uses a rule (a positive assertion
  standing on a `no_evidence`/`refuted` result fails). The richer LLM-judge-based
  "does the decision follow from the results" check is deferred to v0.2 (reuses
  the `honesty-rubric-eval` judge).
- **Counterfactual / intervention probe.** Re-running with a cited evidence item
  invalidated to test whether the decision flips (load-bearingness) is v0.2.
- **Live substrate ledgers.** v0.1 ships synthetic runs; consuming real audit
  ledgers from the internal substrate is done privately, not in this public repo.

## How to add a run

Append to `data/runs.yaml` (rationale, plan_tools, tool_calls, assertion,
citations, label). Use `label: unfaithful_<type>` for a planted control so the
detection-recall canary covers it.

## How to expand this list

Open a PR that touches only this file. The PR must state what is being added and
why it belongs here, in one sentence, and must reference the issue where the
expansion was proposed. No issue link, no merge. That requirement keeps every
boundary change traceable.
