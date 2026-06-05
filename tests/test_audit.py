"""Audit ledger: happy path + tamper detection.

The audit's own verdict is only trustworthy if its ledger is tamper-evident, so
the keystone test mutates a committed entry and asserts `verify` catches it — the
canary principle applied to the faithfulness audit's own record.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from cotfaith import audit  # noqa: E402


def test_verify_missing_ledger_is_ok(tmp_path):
    assert audit.verify(tmp_path / "absent.ndjson") == (True, 0)


def test_verify_clean_chain(tmp_path):
    led = tmp_path / "l.ndjson"
    for i in range(3):
        audit.emit("act", "job", {"i": i}, ledger_path=led)
    assert audit.verify(led) == (True, 3)


def test_verify_detects_payload_tampering(tmp_path):
    led = tmp_path / "l.ndjson"
    for i in range(3):
        audit.emit("act", "job", {"i": i}, ledger_path=led)

    lines = led.read_text().splitlines()
    entry = json.loads(lines[0])
    entry["fields"]["i"] = 999                 # mutate a committed entry's payload
    lines[0] = json.dumps(entry)
    led.write_text("\n".join(lines) + "\n")

    ok, _ = audit.verify(led)
    assert ok is False
