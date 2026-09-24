#!/usr/bin/env python3
"""Check the research ledger, the calculator model, and the calculator page for internal consistency.

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

    # Shared reference arithmetic (scripts/taxmodel.py mirrors assets/site.js).
    sys.path.insert(0, str(ROOT / "scripts"))
    from taxmodel import compute, render_rows  # noqa: E402

    scenarios = calculator.get("scenarios", [])
    if not scenarios:
        errors.append("calculator has no scenarios; the character comparison is the point of the page")
    if sum(1 for s in scenarios if s.get("baseline")) != 1:
        errors.append("calculator must have exactly one baseline scenario")
    scenario_ids = [s.get("id") for s in scenarios]
    if len(scenario_ids) != len(set(scenario_ids)):
        errors.append("duplicate scenario id")
    for scenario in scenarios:
        sid = scenario.get("id")
        for key in ("label", "short", "federal_method", "long_term_share", "federal_note",
                    "california_note", "loss_rule", "forms", "evidence", "status", "findings"):
            if key not in scenario or scenario[key] in ("", None):
                errors.append(f"scenario {sid} missing {key}")
        if scenario.get("federal_method") not in ("ordinary", "stacked"):
            errors.append(f"scenario {sid} has unknown federal_method")
        share = scenario.get("long_term_share")
        if not isinstance(share, (int, float)) or not 0 <= share <= 1:
            errors.append(f"scenario {sid} long_term_share must be between 0 and 1")
        if scenario.get("status") == "settled":
            errors.append(f"scenario {sid} is marked settled; character is open by rule")
        for fid in scenario.get("findings", []):
            if fid not in seen:
                errors.append(f"scenario {sid} cites unknown finding {fid}")

    breaks = calculator.get("long_term_breakpoints_2026", {})
    for key in ("maximum_zero_rate_amount", "maximum_15_percent_rate_amount", "rate_above_15_percent_amount"):
        if not isinstance(breaks.get(key), (int, float)):
            errors.append(f"calculator long_term_breakpoints_2026 missing {key}")

    # User-visible anchor rows. They make a bracket or breakpoint edit fail loudly
    # instead of silently changing the requested $10k, $50k, or $200k answers.
    # Expected values were hand-checked against Rev. Proc. 2025-32 Table 3 and
    # section 4.03, 26 U.S.C. section 1(h), and FTB 2025 Schedule X.
    anchors = {
        ("ordinary", 10000): (1000.00, 100.00),
        ("ordinary", 50000): (5752.00, 1534.89),
        ("ordinary", 200000): (40598.00, 15038.64),
        ("short_term", 200000): (40598.00, 15038.64),
        ("wagering", 200000): (40598.00, 15038.64),
        ("section_1256", 10000): (400.00, 100.00),
        ("section_1256", 50000): (2234.50, 1534.89),
        ("section_1256", 130000): (17852.00, 8528.64),
        ("section_1256", 200000): (30312.00, 15038.64),
        ("long_term", 10000): (0.00, 100.00),
        ("long_term", 50000): (82.50, 1534.89),
        ("long_term", 200000): (22582.50, 15038.64),
    }
    by_scenario = {s.get("id"): s for s in scenarios}
    for (sid, amount), expected in anchors.items():
        scenario = by_scenario.get(sid)
        if not scenario:
            errors.append(f"calculator anchor scenario {sid} is missing")
            continue
        try:
            result = compute(calculator, scenario, amount)
        except (KeyError, TypeError, ValueError) as exc:
            errors.append(f"calculator anchor {sid} ${amount:,} could not be calculated: {exc}")
            continue
        actual = (round(result["federal"], 2), round(result["california"], 2))
        if actual != expected:
            errors.append(f"calculator anchor {sid} ${amount:,} changed: got {actual}, expected {expected}")

    # Headline dollars quoted in prose must still match the model. This cannot
    # find every stale sentence, but it makes the summary and README fail loudly
    # when a bracket edit changes the numbers they quote.
    headline = [("ordinary", 50000), ("section_1256", 50000), ("long_term", 50000),
                ("ordinary", 200000), ("section_1256", 200000), ("long_term", 200000)]
    prose_pages = {name: (ROOT / name).read_text(encoding="utf-8") for name in ("index.html", "README.md")}
    for sid, amount in headline:
        scenario = by_scenario.get(sid)
        if not scenario:
            continue
        result = compute(calculator, scenario, amount)
        for label, value in (("federal", result["federal"]), ("california", result["california"])):
            text = "${:,.2f}".format(round(value + 1e-9, 2))
            for name, body in prose_pages.items():
                if text not in body:
                    errors.append(f"{name} no longer quotes {sid} {label} at ${amount:,} = {text}")

    # The static fallback table in calculator.html must equal the JSON model.
    page = (ROOT / "calculator.html").read_text(encoding="utf-8")
    start, end = "<!-- calculator-rows:start -->", "<!-- calculator-rows:end -->"
    if start in page and end in page:
        static_rows = page.split(start, 1)[1].split(end, 1)[0].strip()
        if scenarios and static_rows != render_rows(calculator, "combined").strip():
            errors.append("calculator.html fallback rows differ from data/calculator.json; run scripts/render_calculator.py")
    else:
        errors.append("calculator.html is missing the fallback-row markers")

    if errors:
        print("LEDGER FAILED")
        for error in errors:
            print("- " + error)
        return 1

    print(f"LEDGER OK: {len(seen)} findings, {len(by_id)} sources, {len(feed['items'])} feed items, {len(scenarios)} calculator scenarios")
    print("CPA license seats filled:", len(filled))
    return 0


if __name__ == "__main__":
    sys.exit(main())
