#!/usr/bin/env python3
"""Write the static fallback rows of calculator.html from data/calculator.json.

The interactive page recomputes everything in the browser. The rows between the
markers below exist so a reader without JavaScript, or a search engine, sees the
same numbers. Run this after any change to the rate model, then run
``scripts/validate_ledger.py``, which fails if the file and the model disagree.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from taxmodel import load_model, render_rows  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PAGE = ROOT / "calculator.html"
START = "<!-- calculator-rows:start -->"
END = "<!-- calculator-rows:end -->"
HEAD_START = "<!-- calculator-head:start -->"
HEAD_END = "<!-- calculator-head:end -->"


def render_head(model: dict) -> str:
    cells = ['<th scope="col">Modeled taxable income</th>']
    for scenario in model["scenarios"]:
        cells.append(f'<th scope="col">{scenario["short"]}</th>')
    return "<tr>" + "".join(cells) + "</tr>"


def replace_between(text: str, start: str, end: str, body: str) -> str:
    pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
    if not pattern.search(text):
        raise SystemExit(f"markers {start} … {end} not found in {PAGE}")
    return pattern.sub(lambda _: f"{start}\n{body}\n{end}", text)


def main() -> int:
    model = load_model()
    text = PAGE.read_text(encoding="utf-8")
    text = replace_between(text, HEAD_START, HEAD_END, render_head(model))
    text = replace_between(text, START, END, render_rows(model, "combined"))
    PAGE.write_text(text, encoding="utf-8")
    print("calculator.html fallback table rewritten from data/calculator.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
