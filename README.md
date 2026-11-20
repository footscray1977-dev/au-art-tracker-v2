# Australian Art Sleeper Tracker (`au-art-tracker` v2)

House-direct-first overseas auction & estate-sale sleeper hunter for Australian and New Zealand art, built on the November 2026 architecture.

## Quick Start (Mac / Linux)

1. **Install Python dependencies** (Python 3.10+):
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Initialize the SQLite FTS5 database** from the cleaned master datasets (`946` artists, `339` overseas houses):
   ```bash
   python3 tracker.py --init-db
   ```

3. **Run a polite sweep** (Class B own-site houses, French provincial priority first):
   ```bash
   python3 tracker.py --sweep --limit 25
   ```

4. **Manual on-demand commands**:
   - Re-match local lots against one artist (instant, zero HTTP):
     `python3 tracker.py --artist "John Peter Russell"`
   - Fetch one specific house immediately:
     `python3 tracker.py --house "Drouot"`
   - Run the high-value misattribution + Australian subject bundle locally:
     `python3 tracker.py --bundle misattributed_aus`
   - Generate the Top-30 HTML Sleeper Digest (`reports/latest.html`, works via `file://`):
     `python3 tracker.py --report-only`

## Daily 3:00 AM Brisbane (17:00 UTC) Automation

- **GitHub Actions**: `.github/workflows/daily_sweep.yml` runs at `0 17 * * *` UTC (3:00 AM AEST, year-round) and includes a `workflow_dispatch` manual button.
- **macOS `launchd` / `cron`**:
  `0 3 * * * cd /path/to/au-art-tracker && .venv/bin/python tracker.py --sweep >> logs/sweep.log 2>&1`

## Scope Rules (Nov 2026)

- **Included media**: Oil, acrylic, tempera, watercolour, gouache, pastel, drawing, sculpture (bronze/wood/stone/metal), ceramics/pottery, photographs, and **prints** (etchings, lithographs, screenprints, woodblocks).
- **Excluded**: Bark paintings, Aboriginal/Torres Strait Islander art, coins, books, stamps, memorabilia, non-art `NEG_PHRASE_RX` false positives.
- **Polite HTTP**: Respects `robots.txt`, uses `ETag` / `If-None-Match` 304 caching, randomised 2.0–5.0s per-domain delays, and never bypasses CAPTCHAs or login gates.
