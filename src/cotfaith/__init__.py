"""cot-faithfulness-audit: does the agent's stated reasoning match what it
actually did (tool calls, results, decision)? A post-hoc audit over the
substrate's hash-chained ledger. (v0.1)"""

__version__ = "0.1.0"

# The four operational faithfulness checks (rationale <-> action <-> outcome).
CHECKS = (
    "plan_action_match",     # claimed tools were actually called
    "no_hidden_action",      # no consequential tool call the rationale omits
    "action_outcome_match",  # decision follows the tool results (not ignored)
    "citation_grounding",    # cited tools were called and supported the claim
)
