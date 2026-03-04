#!/usr/bin/env bash
set -euo pipefail

# Adds/updates a cron entry to generate LinkedIn job links daily at 8:00 PM America/New_York.
# Output lands in daily CSV files under ./output

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRON_LINE='0 20 * * * cd '"$SCRIPT_DIR"' && /usr/bin/env TZ=America/New_York python3 generate_linkedin_links.py --config job-search-config.json --out output/job-links-$(date +\%F).csv >> output/job-links.log 2>&1'

mkdir -p "$SCRIPT_DIR/output"

( crontab -l 2>/dev/null | rg -v "generate_linkedin_links.py"; echo "$CRON_LINE" ) | crontab -

echo "Scheduled: daily 8:00 PM America/New_York"
echo "Run 'crontab -l' to confirm."
