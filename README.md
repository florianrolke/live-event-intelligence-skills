# Live Event Intelligence Skills

Reusable Codex skills and deterministic scripts for finding local or niche live events, mapping conference relationships, and producing outreach-ready event prospect reports.

The workflow is based on proven runs for Lainie, Drew, Vincent Sims, and MHI 2026 research: start with a client/niche/location, generate layered deep-research queries, identify conferences and association events, extract visible speakers/exhibitors/sponsors/attendees, find LinkedIn profiles/pages, and export clean CSV/Markdown deliverables.

## Quick Start

```powershell
python scripts/generate_event_queries.py --niche "manufactured housing" --city "Las Vegas" --year 2026 --event-name "MHI 2026 Congress & Expo" --companies "EXO Edge" "21st Mortgage Corporation" --people "Nikki Greenberg|Futurist" "Laura Eldredge|EXO Edge"
python scripts/find_linkedin_profiles.py --input tests/fixtures/mhi_contacts.csv --output reports/mhi-linkedin-matches.csv
python scripts/normalize_events.py --input tests/fixtures/mhi_events_raw.csv --output reports/mhi-events-normalized.csv
python scripts/generate_event_report.py --events reports/mhi-events-normalized.csv --contacts reports/mhi-linkedin-matches.csv --output reports/mhi-event-report.md
```

## Core Outputs

- Google Sheets-ready event CSVs
- Contact and LinkedIn match CSVs
- Association/event-calendar CSVs
- Concise Markdown reports with evidence and next actions

## Source Policy

Prefer official pages, Google SERP, professional association pages, 10times, and tightly scoped Eventbrite. Avoid broad AllEvents scans by default. Require explicit approval for authenticated LinkedIn automation, LinkedIn participant scraping, full Instagram follower scrapes, or paid runs above the configured cap.
## 2026 Outcome-First Layer

This repo now includes an outcome-first ranking layer for turning messy deep-research outputs into action maps. Treat Perplexity/Genspark reports as lead lists, not evidence. Verify important claims, rank opportunities, and produce action-ready outputs.

New references:
- `references/outcome-first-opportunity-mapping.md`
- `references/niche-playbooks.md`

New deterministic script:

```powershell
python scripts/rank_opportunities.py --input reports/events-normalized.csv --output reports/events-ranked.csv
```

The ranker supports manufactured housing, AI/VapiCon-style startup conferences, CPA/CPE, exit planning, HVAC/plumbing, and local business networking patterns by scoring ICP fit, access quality, timeliness, commercial intent, relationship leverage, and source confidence.
