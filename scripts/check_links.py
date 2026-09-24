#!/usr/bin/env python3
"""Optional link check for the source registry.

Does not rewrite findings. A failure here means a URL did not answer, not that a
tax conclusion changed. Run by hand or with workflow_dispatch. Do not treat a
timeout as a change in the law.
"""

from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = json.loads((ROOT / "data" / "sources.json").read_text(encoding="utf-8"))


def main() -> int:
    failures = 0
    for source in SOURCES["sources"]:
        url = source["url"]
        if source.get("type") == "research-note":
            print(f"SKIP {source['id']} research note")
            continue
        request = urllib.request.Request(url, method="GET", headers={"User-Agent": "TAXKALSHI-link-check"})
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                print(f"OK {response.status} {source['id']}")
        except Exception as exc:  # noqa: BLE001 — report and continue
            failures += 1
            print(f"FAIL {source['id']} {url} {exc}")
    print(f"done, failures={failures}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
