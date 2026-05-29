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