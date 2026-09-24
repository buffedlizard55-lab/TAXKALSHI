#!/usr/bin/env python3
"""Reference implementation of the calculator rate model.

This is the same arithmetic as ``assets/site.js``. The validator uses it to
recompute anchor rows and to check that the static fallback table in
``calculator.html`` matches ``data/calculator.json``. It applies rate tables
that were copied from the cited IRS and FTB documents; it does not decide the
character of a Kalshi event contract.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "data" / "calculator.json"


def load_model(path: Path = MODEL_PATH) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def tax_at(amount: float, bands: list[dict]) -> float:
    """Rate-schedule arithmetic: base plus rate on the excess over the band start."""
    for band in bands:
        if band.get("up_to") is None or amount <= band["up_to"]:
            return band["base"] + (amount - band["from"]) * band["rate"]
    return 0.0


def stacked_federal(model: dict, ordinary_part: float, long_term_part: float) -> float:
    """Section 1(h)(1) with the section 1(j)(5) dollar breakpoints.

    (A) ordinary tax on taxable income reduced by the net capital gain;
    (B) 0 percent on the gain that fits below the maximum zero rate amount;
    (C) 15 percent on the remainder up to the maximum 15-percent rate amount;
    (D) 20 percent above that.
    """
    breaks = model["long_term_breakpoints_2026"]
    zero_max = breaks["maximum_zero_rate_amount"]
    fifteen_max = breaks["maximum_15_percent_rate_amount"]
    top_rate = breaks["rate_above_15_percent_amount"]

    ordinary_tax = tax_at(ordinary_part, model["federal_bands"])
    zero_slice = max(0.0, min(long_term_part, zero_max - ordinary_part))
    remaining = long_term_part - zero_slice
    fifteen_slice = max(0.0, min(remaining, fifteen_max - (ordinary_part + zero_slice)))
    twenty_slice = remaining - fifteen_slice
    return ordinary_tax + 0.15 * fifteen_slice + top_rate * twenty_slice


def federal_for(model: dict, scenario: dict, amount: float) -> float:
    if scenario["federal_method"] == "ordinary":
        return tax_at(amount, model["federal_bands"])
    if scenario["federal_method"] == "stacked":
        share = float(scenario["long_term_share"])
        return stacked_federal(model, amount * (1 - share), amount * share)
    raise ValueError(f"unknown federal_method {scenario['federal_method']!r}")


def california_for(model: dict, amount: float) -> float:
    return tax_at(amount, model["california_bands"])


def compute(model: dict, scenario: dict, amount: float) -> dict:
    federal = federal_for(model, scenario, amount)
    california = california_for(model, amount)
    return {
        "amount": amount,
        "federal": federal,
        "california": california,
        "combined": federal + california,
    }


def amounts(model: dict) -> list[int]:
    step = int(model["step"])
    maximum = int(model["maximum"])
    return list(range(step, maximum + 1, step))


def baseline(model: dict) -> dict:
    for scenario in model["scenarios"]:
        if scenario.get("baseline"):
            return scenario
    return model["scenarios"][0]


def money(value: float) -> str:
    return "${:,.2f}".format(round(max(0.0, value) + 1e-9, 2))


def render_rows(model: dict, view: str = "combined") -> str:
    """HTML rows for the static fallback table: one row per amount, one cell per scenario."""
    rows = []
    for amount in amounts(model):
        cells = []
        for scenario in model["scenarios"]:
            result = compute(model, scenario, amount)
            cells.append(f"<td>{money(result[view])}</td>")
        rows.append(
            f'<tr data-amount-row data-amount="{amount}"><th scope="row">{money(amount)}</th>'
            + "".join(cells)
            + "</tr>"
        )
    return "\n".join(rows)


if __name__ == "__main__":
    import sys

    model = load_model()
    view = sys.argv[1] if len(sys.argv) > 1 else "combined"
    print(render_rows(model, view))
