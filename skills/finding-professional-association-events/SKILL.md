---
name: finding-professional-association-events
description: Find professional associations, trade groups, societies, chambers, BNI-style groups, event calendars, member directories, board members, event staff, and association-hosted conferences for local or niche prospecting. Use for Vincent-style association/event ecosystem research.
---

# Finding Professional Association Events

## Workflow

1. Start with niche, geography, profession, and target buyer segment.
2. Generate association queries from `references/query-patterns.md`.
3. Run `scripts/discover_associations.py` for SERP discovery when API keys are available.
4. Capture association pages, event calendars, member directories, board/staff pages, and sponsor/exhibitor pages.
5. Extract contacts with `scripts/extract_event_contacts.py` and enrich carefully.

## Commands

```powershell
python scripts/discover_associations.py --niche "HVAC contractors" --city "Houston" --state TX --year 2026 --output reports/houston-hvac-associations.csv
```

## Guardrails

- Treat associations as relationship maps, not just event pages.
- Prioritize event managers, executive directors, board presidents, sponsors, and recurring committee leads.
- Keep member directories and event calendars as separate fields.
## 2026 Outcome-First Update

For association research, capture publication/distribution channels in addition to event pages: magazines, newsletters, flipbook directories, member directories, ad/sponsor pages, and official publication contacts.

Treat associations as relationship maps. Prioritize executive directors, event managers, board presidents, chapter chairs, recurring committee leads, sponsor contacts, newsletter editors, and publication/ad contacts.

Rank association opportunities with:

```powershell
python scripts/rank_opportunities.py --input reports/associations.csv --output reports/associations-ranked.csv
```
