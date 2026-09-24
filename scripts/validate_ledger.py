#!/usr/bin/env python3
"""Check the research ledger for missing sources, empty quotes, and duplicate IDs.

This does not prove a quote is accurate. It proves the ledger is internally complete
so a later pass can re-read each URL instead of inventing a citation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

REQUIRED_IDS = {
    "F01", "F17", "F18", "F20", "F21", "F22", "F28", "F29", "F30", "F31", "F34", "F36"
}
ALLOWED_STATUS = {"settled", "open", "flag", "rejected", "supported"}


def load(name: str) -> dict:
    path = DATA / name
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    errors: list[str] = []
    sources = load("sources.json")
    findings = load("findings.json")
    panel = load("panel.json")
    feed = load("feed.json")
    calculator = load("calculator.json")

    source_ids = [s.get("id") for s in sources.get("sources", [])]
    if len(source_ids) != len(set(source_ids)):
        errors.append("duplicate source id")
    by_id = {s["id"]: s for s in sources["sources"]}
    for source in sources["sources"]:
        for key in ("id", "title", "publisher", "url", "retrieved"):
            if not source.get(key):
                errors.append(f"source {source.get('id')} missing {key}")
        if not str(source.get("url", "")).startswith("https://"):
            errors.append(f"source {source.get('id')} url is not https")

    seen = set()
    for finding in findings.get("findings", []):
        fid = finding.get("id")
        if fid in seen:
            errors.append(f"duplicate finding {fid}")
        seen.add(fid)
        if finding.get("status") not in ALLOWED_STATUS:
            errors.append(f"{fid} has bad status {finding.get('status')}")
        quote = (finding.get("quote") or "").strip()
        if len(quote) < 20:
            errors.append(f"{fid} quote is missing or too short")
        sid = finding.get("source_id")
        if sid not in by_id:
            errors.append(f"{fid} cites unknown source {sid}")
        if not finding.get("claim") or not finding.get("why_it_matters"):
            errors.append(f"{fid} missing claim or why_it_matters")

    missing = REQUIRED_IDS - seen
    if missing:
        errors.append("missing required findings: " + ", ".join(sorted(missing)))

    filled = [
        seat for seat in panel.get("seats", [])
        if seat.get("kind") == "license-required" and seat.get("status") != "empty"
    ]
    for seat in filled:
        if not seat.get("license_board_url") or not seat.get("license_record_date"):
            errors.append(f"filled CPA seat {seat.get('id')} has no board-lookup record")

    if not feed.get("items"):
        errors.append("feed is empty")

    # The calculator is deliberately data-driven. These checks catch a stale or
    # malformed rate table before it can make the public page look authoritative.
    if calculator.get("step") != 10000 or calculator.get("maximum") != 200000:
        errors.append("calculator must cover $10,000 steps through $200,000")
    for key in ("federal_rates", "california_rates", "income_inclusion", "california_year_note"):
        source_id = calculator.get("sources", {}).get(key)
        if source_id not in by_id:
            errors.append(f"calculator cites unknown source {source_id}")
    for label in ("federal_bands", "california_bands"):
        bands = calculator.get(label, [])
        if not bands:
            errors.append(f"calculator {label} is empty")
            continue
        previous = -1
        for index, band in enumerate(bands):
            if not all(key in band for key in ("from", "up_to", "base", "rate")):
                errors.append(f"calculator {label} is missing band fields at {index}")
                continue
            if not isinstance(band.get("from"), (int, float)) or band["from"] <= previous:
                if index == 0 and band.get("from") == 0:
                    pass
                else:
                    errors.append(f"calculator {label} has invalid band start at {index}")
            previous = band.get("from", previous)
            if band.get("up_to") is not None and band["up_to"] <= band["from"]:
                errors.append(f"calculator {label} has invalid band end at {index}")
            if not isinstance(band.get("base"), (int, float)) or band["base"] < 0:
                errors.append(f"calculator {label} has invalid base at {index}")
            if not isinstance(band.get("rate"), (int, float)) or not 0 < band["rate"] <= 1:
                errors.append(f"calculator {label} has invalid rate at {index}")
        if bands[-1].get("up_to") is not None:
            errors.append(f"calculator {label} must end with an open band")

    def tax_at(amount: float, bands: list[dict]) -> float:
        for band in bands:
            if band.get("up_to") is None or amount <= band["up_to"]:
                return band["base"] + (amount - band["from"]) * band["rate"]
        return 0.0

    # These are the user-visible anchor rows. They make a bracket edit fail loudly
    # instead of silently changing the requested $10k, $50k, or $200k answers.
    for amount, expected in {
        10000: (1000.00, 100.00, 1100.00),
        50000: (5752.00, 1534.89, 7286.89),
        200000: (40598.00, 15038.64, 55636.64),
    }.items():
        try:
            actual = (
                tax_at(amount, calculator.get("federal_bands", [])),
                tax_at(amount, calculator.get("california_bands", [])),
            )
        except (KeyError, TypeError):
            errors.append(f"calculator anchor row ${amount:,} could not be calculated")
            continue
        if any(round(value, 2) != expected[index] for index, value in enumerate(actual)):
            errors.append(f"calculator anchor row ${amount:,} changed: got {actual}")
        if round(sum(actual), 2) != expected[2]:
            errors.append(f"calculator combined anchor row ${amount:,} changed")

    if errors:
        print("LEDGER FAILED")
        for error in errors:
            print("- " + error)
        return 1

    print(f"LEDGER OK: {len(seen)} findings, {len(by_id)} sources, {len(feed['items'])} feed items")
    print("CPA license seats filled:", len(filled))
    return 0


if __name__ == "__main__":
    sys.exit(main())
