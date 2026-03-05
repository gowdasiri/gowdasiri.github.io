#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ ! -f job-search-config.json ]; then
  cp job-search-config.example.json job-search-config.json
  echo "Created job-search-config.json from example. Edit it and rerun for your own roles/locations."
fi

mkdir -p output
OUT_FILE="output/job-links-$(date +%F-%H%M%S).csv"
python3 generate_linkedin_links.py --config job-search-config.json --out "$OUT_FILE"

echo "Done. Open this file to click links: $OUT_FILE"
