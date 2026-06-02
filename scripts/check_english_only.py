#!/usr/bin/env python3
"""CI gate: fail if CJK characters appear in committed text artifacts."""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EXTS = {".md", ".py", ".yaml", ".yml", ".toml", ".txt"}


def _is_cjk(ch: str) -> bool:
    o = ord(ch)
    return (
        0x3040 <= o <= 0x30FF
        or 0x3400 <= o <= 0x4DBF
        or 0x4E00 <= o <= 0x9FFF
        or 0xAC00 <= o <= 0xD7A3
        or 0x1100 <= o <= 0x11FF
    )


def main() -> int:
    bad: list[str] = []
    for p in REPO.rglob("*"):
        if not p.is_file() or p.suffix.lower() not in EXTS:
            continue
        if any(part in {".git", ".venv", "__pycache__"} for part in p.parts):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        if any(_is_cjk(ch) for ch in text):
            bad.append(p.relative_to(REPO).as_posix())
    if bad:
        sys.stderr.write("::error::CJK characters found in: " + ", ".join(sorted(bad)) + "\n")
        return 1
    print("english-only: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
