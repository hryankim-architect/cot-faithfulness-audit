"""Load synthetic agent runs (stand-in for the substrate audit ledger)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass(frozen=True)
class ToolCall:
    name: str
    status: str  # evidence | no_evidence | refuted | ok


@dataclass(frozen=True)
class Run:
    run_id: str
    rationale: str
    plan_tools: list[str]
    tool_calls: list[ToolCall]
    assertion: str            # "positive" | "declined"
    citations: list[str]
    label: str                # "faithful" | "unfaithful_*"
    extra: dict = field(default_factory=dict)

    @property
    def called_tools(self) -> list[str]:
        return [c.name for c in self.tool_calls]


def load_runs(path: Path) -> list[Run]:
    raw = yaml.safe_load(Path(path).read_text())
    out: list[Run] = []
    for r in raw["runs"]:
        calls = [ToolCall(name=c["name"], status=c["result"]["status"]) for c in r["tool_calls"]]
        out.append(Run(
            run_id=r["run_id"], rationale=r["rationale"].strip(),
            plan_tools=list(r.get("plan_tools", [])), tool_calls=calls,
            assertion=r.get("assertion", "positive"),
            citations=list(r.get("citations", [])), label=r.get("label", "faithful"),
        ))
    return out
