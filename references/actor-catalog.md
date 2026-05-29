# Actor Catalog

Primary low-cost sources:
- `scraperlink/google-search-results-serp-scraper`: Google SERP lookup for profiles, Facebook, websites, and event pages.
- `apify/google-search-scraper`: Google search results for focused event/contact queries.
- `zen-studio/10times-events-scraper`: conferences, trade shows, expos, exhibitions. Strong signal in Lainie run.
- `santamaria-automations/eventbrite-scraper`: tightly scoped Eventbrite events.
- `powerai/eventbrite-events-scraper`: alternate Eventbrite search URL actor.

Secondary sources:
- `easyapi/meetup-events-scraper`: use only with specific professional groups or strong niche queries.
- `easyapi/ticketmaster-events-scraper`: ticketed expos, conventions, and venue-based events.
- `apify/facebook-events-scraper`: Facebook event search when local/community pages matter.
- `crawlerbros/facebook-events-scraper`: known Facebook event URLs or page event listings.

Avoid by default:
- `techforce.global/all-events-scraper`: Lainie test cost $4 for 10 noisy results due actor-start/memory billing.

Approval required:
- LinkedIn participant scraping actors.
- Authenticated LinkedIn automation.
- Full Instagram follower scrapes.
- Any paid actor run above the configured cap.