# scraper_bot/providers/amadeus.py
import os

# Amadeus SDK
try:
    from amadeus import Client, ResponseError
except Exception:  # SDK not installed or import error during local runs
    Client = None
    ResponseError = Exception  # fallback

AMADEUS_API_KEY = os.getenv("AMADEUS_API_KEY")
AMADEUS_API_SECRET = os.getenv("AMADEUS_API_SECRET")

def _get_client():
    """
    Return an Amadeus client or None if keys/SDK are missing.
    """
    if not (AMADEUS_API_KEY and AMADEUS_API_SECRET and Client):
        return None
    try:
        return Client(client_id=AMADEUS_API_KEY, client_secret=AMADEUS_API_SECRET)
    except Exception:
        return None

def search_amadeus(origin: str, dest: str, depart_date: str, *,
                   return_date: str | None = None,
                   passengers: int = 1,
                   cabin: str = "ECONOMY",         # ECONOMY | PREMIUM_ECONOMY | BUSINESS | FIRST
                   currency: str = "AUD",
                   nonstop: bool = False,
                   max_results: int = 5):
    """
    Query Amadeus Flight Offers Search and normalize to the shape the app expects.
    Returns [] gracefully if keys are missing or the API call fails.
    """
    amadeus = _get_client()
    if not amadeus:
        return []

    params = {
        "originLocationCode": origin,
        "destinationLocationCode": dest,
        "departureDate": depart_date,
        "adults": int(passengers),
        "nonStop": bool(nonstop),
        "currencyCode": currency,
        "travelClass": str(cabin).upper(),  # ensure valid value
        "max": int(max_results),
    }
    if return_date:
        params["returnDate"] = return_date

    try:
        resp = amadeus.shopping.flight_offers_search.get(**params)
        offers = getattr(resp, "data", []) or []
    except ResponseError:
        return []
    except Exception:
        return []

    out = []
    for off in offers:
        # Price
        price = None
        try:
            price = float(off.get("price", {}).get("grandTotal"))
        except Exception:
            pass

        # Try to read first segment/carrier/flight number
        carrier = ""
        flight_no = ""
        try:
            itins = off.get("itineraries", [])
            segs = itins[0].get("segments", []) if itins else []
            if segs:
                carrier = segs[0].get("carrierCode", "") or ""
                # flight number sometimes split across number + carrier
                fnum = segs[0].get("number", "")
                flight_no = f"{carrier}{fnum}" if carrier or fnum else ""
        except Exception:
            pass

        out.append({
            "provider": "Amadeus",
            "provider_code": "AM",
            "aud": price,
            "url": "",                 # Amadeus doesn't provide a public deeplink
            "carrier": carrier,
            "flight_number": flight_no,
            "operated_by": carrier,
        })

    return out

# Backward‑compat alias (so old imports still work)
def search_amadeus_flights(*args, **kwargs):
    return search_amadeus(*args, **kwargs)


