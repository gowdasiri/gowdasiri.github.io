#!/usr/bin/env python3
"""Generate direct-click LinkedIn job search links from a simple config.

This script generates search URLs only. It does not and should not automate job
applications.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from urllib.parse import quote_plus


def build_url(keyword: str, location: str, hours: int | None) -> str:
    params = [f"keywords={quote_plus(keyword)}", f"location={quote_plus(location)}"]
    if hours is not None:
        params.append(f"f_TPR=r{hours * 3600}")
    return "https://www.linkedin.com/jobs/search/?" + "&".join(params)


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate LinkedIn job search links")
    parser.add_argument(
        "--config",
        default="job-search-config.json",
        help="Path to config JSON file (default: job-search-config.json)",
    )
    parser.add_argument(
        "--out",
        default="job-links.csv",
        help="Output CSV path (default: job-links.csv)",
    )
    args = parser.parse_args()

    config_path = Path(args.config)
    if not config_path.exists():
        raise SystemExit(
            f"Config file not found: {config_path}. Copy job-search-config.example.json and customize it."
        )

    data = json.loads(config_path.read_text(encoding="utf-8"))
    keywords = data.get("keywords", [])
    locations = data.get("locations", [])
    posted_within_hours = data.get("posted_within_hours")

    rows: list[dict[str, str]] = []
    for keyword in keywords:
        for location in locations:
            rows.append(
                {
                    "keyword": keyword,
                    "location": location,
                    "url": build_url(keyword, location, posted_within_hours),
                }
            )

    out_path = Path(args.out)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["keyword", "location", "url"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} links at {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
