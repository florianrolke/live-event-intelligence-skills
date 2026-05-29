from scripts.generate_event_queries import generate_queries


def test_mhi_query_generation_contains_core_patterns():
    rows = generate_queries(
        niche="manufactured housing",
        city="Las Vegas",
        state="NV",
        year=2026,
        event_name="MHI 2026 Congress & Expo",
        companies=["EXO Edge"],
        people=["Nikki Greenberg|Futurist"],
        official_domains=["manufacturedhousing.org"],
    )
    queries = {r["query"] for r in rows}
    assert "manufactured housing conference 2026" in queries
    assert "site:manufacturedhousing.org annual meeting 2026" in queries
    assert "MHI 2026 Congress & Expo exhibitors 2026" in queries
    assert 'site:linkedin.com/in "Nikki Greenberg" "Futurist"' in queries
    assert 'site:linkedin.com/company "EXO Edge" LinkedIn' in queries


def test_local_suburb_generation():
    rows = generate_queries(niche="dental", city="Tijuana", state="BC", year=2026, suburbs=["Zona Rio", "San Diego"])
    queries = {r["query"] for r in rows}
    assert '"dental" events "Zona Rio"' in queries
    assert 'site:.org "dental" "San Diego" "events"' in queries