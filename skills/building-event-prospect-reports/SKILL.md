---
name: building-event-prospect-reports
description: Build client-facing live-event intelligence reports, prospect sheets, event priority rankings, association watchlists, LinkedIn contact maps, and outreach-ready CSV/Markdown deliverables from normalized events and contacts.
---

# Building Event Prospect Reports

## Workflow

1. Normalize and dedupe events before reporting.
2. Merge contacts and LinkedIn matches only after confidence labels are present.
3. Put top attendance targets first, then watchlist/backfill events, then association hubs, then source limitations.
4. Generate Markdown with `scripts/generate_event_report.py`; create HTML only when requested.

## Commands

```powershell
python scripts/generate_event_report.py --events reports/events-deduped.csv --contacts reports/event-contacts-enriched.csv --output reports/live-event-report.md --title "Client Live Event Intelligence"
```

## Guardrails

- Separate current-year confirmed events from historical/reference events.
- Mention private app or LinkedIn access limits plainly.
- Keep reports concise enough to support action: event, why it matters, who to contact, next action.