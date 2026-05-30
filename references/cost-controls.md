# Cost Controls

Default behavior:
- Dry-run paid actors first.
- Cap first paid validation at 25 results per source unless the user explicitly approves more.
- Print estimated payload, actor ID, and max results before running.
- Store raw paid outputs under `data/` or `.tmp/` and keep normalized reports separate.

Lessons from prior runs:
- 10times produced high-value Lainie event data cheaply.
- Eventbrite can produce useful local networking results when scoped tightly.
- Meetup was noisy for broad networking scans.
- AllEvents cost more than expected and was noisy; avoid broad scans.
- LinkedIn participant scraping requires cookies/account side effects and must be approval-gated.
## May 30, 2026 Cape Coral validation
- Scoped Apify Google Search actor run used `apify/google-search-scraper` with 5 focused local-event queries and `maxPagesPerQuery: 1`.
- Actual latest run metadata: status `SUCCEEDED`, usageTotalUsd `$0.0235`, 5 SERP dataset items.
- On Windows, run repo scripts as modules when imports reference `scripts.*`: `python -m scripts.run_apify_event_actor ...`.
- PowerShell 5 `Set-Content -Encoding UTF8` can write a UTF-8 BOM; JSON payloads should be written without BOM or `read_json` should be updated to support `utf-8-sig`.
