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
