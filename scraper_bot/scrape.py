import os
import json
import datetime as dt
from pathlib import Path

# --- Robust import handling (works in both layouts) --------------------------
# Tries package-style first (python -m scraper_bot.scrape), then fallback.
try:
    import scraper_bot.providers.kiwi as kiwi_mod
    import scraper_bot.providers.amadeus as ama_mod
    from scraper_bot.providers.google_deeplink import build_google_flights_url
except Exception:
    # Fallback when run as "python scraper_bot/scrape.py"
    import providers.kiwi as kiwi_mod            # noqa: F401
    import providers.amadeus as ama_mod          # noqa: F401
    from providers.google_deeplink import build_google_flights_url  # noqa: F401

# Resolve function names regardless of *_flights vs no suffix
search_kiwi = getattr(kiwi_mod, "search_kiwi", getattr(kiwi_mod, "search_kiwi_flights"))
search_amadeus = getattr(ama_mod, "search_amadeus", getattr(ama_mod, "search_amadeus_flights"))

# --- Helpers -----------------------------------------------------------------
def now_iso():
    return dt.datetime.utcnow().isoformat() + "Z"

# Starter routes (edit/extend as you like)
ROUTES = [
    {"from": "SYD", "to": "DPS", "date": "2025-08-19", "cabin": "economy", "nonstop": False, "passengers": 1},
    {"from": "MEL", "to": "NRT", "date": "2025-09-10", "cabin": "economy", "nonstop": True,  "passengers": 1},
    {"from": "SYD", "to": "LAX", "date": "2025-10-02", "cabin": "premium", "nonstop": False, "passengers": 1},
]

def cabin_to_codes(cabin):
    c = (cabin or "economy").lower()
    kiwi = {"economy": "M", "premium": "W", "business": "C", "first": "F"}.get(c, "M")
    ama  = {"economy": "ECONOMY", "premium": "PREMIUM_ECONOMY", "business": "BUSINESS", "first": "FIRST"}.get(c, "ECONOMY")
    return kiwi, ama

def normalize(o, d, cabin, date, pax, nonstop, src_items):
    rows = []
    for it in src_items:
        url = it.get("url") or build_google_flights_url(o, d, date, cabin=cabin, passengers=pax, nonstop=nonstop)
        rows.append({
            "from": o,
            "to": d,
            "cabin": cabin,
            "provider": it.get("provider"),
            "provider_code": it.get("provider_code"),
            "flight_number": it.get("flight_number", ""),
            "operated_by": it.get("operated_by", it.get("carrier", "")),
            "aud": it.get("aud"),
            "url": url,
            "ts": now_iso(),
        })
    return rows

def cheapest_by_provider(items):
    best = {}
    for it in items:
        key = (it.get("provider"), it.get("provider_code"))
        price = it.get("aud") if it.get("aud") is not None else 10**9
        if key not in best or (best[key].get("aud") if best[key].get("aud") is not None else 10**9) > price:
            best[key] = it
    return list(best.values())

# --- Main --------------------------------------------------------------------
def main():
    items = []
    for r in ROUTES:
        o, d, date = r["from"], r["to"], r["date"]
        cabin = r.get("cabin", "economy")
        pax = int(r.get("passengers", 1))
        nonstop = bool(r.get("nonstop", False))

        kiwi_code, ama_code = cabin_to_codes(cabin)

        # These gracefully return [] if API keys are missing
        try:
            k = search_kiwi(o, d, date, cabin=kiwi_code, currency="AUD", limit=5)
        except TypeError:
            # If provider has a slightly different signature, try minimal form
            k = search_kiwi(o, d, date)
        except Exception:
            k = []

        try:
            a = search_amadeus(o, d, date, cabin=ama_code, currency="AUD", max_results=5)
        except TypeError:
            a = search_amadeus(o, d, date)
        except Exception:
            a = []

        items += normalize(o, d, cabin, date, pax, nonstop, k)
        items += normalize(o, d, cabin, date, pax, nonstop, a)

        # Always add a Google Flights deep link
        gfl = build_google_flights_url(o, d, date, cabin=cabin, passengers=pax, nonstop=nonstop)
        items.append({
            "from": o, "to": d, "cabin": cabin,
            "provider": "Google Flights (link)", "provider_code": "GF",
            "flight_number": "", "operated_by": "",
            "aud": None, "url": gfl, "ts": now_iso()
        })

    items = cheapest_by_provider(items)

    Path("data").mkdir(exist_ok=True)
    with open("data/live_deals.json", "w", encoding="utf-8") as f:
        json.dump({"meta": {"last_updated": now_iso()}, "items": items}, f, indent=2)

    print(f"Wrote data/live_deals.json with {len(items)} items")

if __name__ == "__main__":
    main()



