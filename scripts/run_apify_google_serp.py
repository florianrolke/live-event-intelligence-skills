"""Run apify/google-search-scraper for a list of queries, extract organicResults, write CSV."""
from __future__ import annotations

import argparse
import requests
from scripts.common import env_keys, load_env, write_csv

EVENT_FIELDS = [
    "query", "stage", "title", "url", "snippet",
]


def run_query(token: str, query: str, results_per_page: int = 10) -> list[dict]:
    response = requests.post(
        "https://api.apify.com/v2/acts/apify~google-search-scraper/run-sync-get-dataset-items",
        params={"token": token},
        json={"queries": query, "maxPagesPerQuery": 1, "resultsPerPage": results_per_page},
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    results = []
    for page in data:
        for r in page.get("organicResults", []):
            results.append({
                "query": query,
                "stage": "apify_google_serp",
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "snippet": r.get("description", ""),
            })
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--queries", required=True, help="Newline-separated list of queries")
    parser.add_argument("--output", required=True)
    parser.add_argument("--results-per-page", type=int, default=10)
    args = parser.parse_args()

    load_env()
    tokens = env_keys("APIFY_API_TOKEN", preferred=["7", "6", "5", "4", "3", "2", ""])
    if not tokens:
        raise RuntimeError("No APIFY_API_TOKEN found")
    token = tokens[0]

    queries = [q.strip() for q in args.queries.strip().splitlines() if q.strip()]
    all_rows = []
    for query in queries:
        print(f"  querying: {query}")
        rows = run_query(token, query, args.results_per_page)
        print(f"    -> {len(rows)} results")
        all_rows.extend(rows)

    write_csv(args.output, all_rows, EVENT_FIELDS)
    print(f"Saved {len(all_rows)} rows to {args.output}")


if __name__ == "__main__":
    main()
