# scraper_bot/providers/kiwi.py
import os
import requests
import datetime as dt

# Kiwi/Tequila API
TEQUILA_API = os.getenv("TEQUILA_ENDPOINT", "https://tequila-api.kiwi.com/v2/search")
TEQUILA_API_KEY = os.getenv("TEQUILA_API_KEY")  # set in GitHub Secrets

def _when(iso_date: str) -> str:
    """Convert YYYY-MM-DD -> DD/MM/YYYY for Tequila."""
    return dt.datetime.strptime(iso_date, "%Y-%m-%d").strftime("%d/%m/%Y")

def search_kiwi(origin: str, dest: str, depart_date: str, *,
                return_date: str | None = None,
                passengers: int = 1,
                cabin: str = "M",
                currency: str = "AUD",
                nonstop: bool = False,
                limit: int = 5,
                timeout: int = 20):
    """
    Query Kiwi/Tequila and return a list of normalized results the app expects.
    Returns [] gracefully if the API key is missing or on any HTTP error.
    """
    if not TEQUILA_API_KEY:
        return []

    headers = {"apikey": TEQUILA_API_KEY}
    params = {
        "fly_from": origin,
        "fly_to": dest,
        "date_from": _when(depart_date),
        "date_to": _when(depart_date),
        "adults": passengers,
        "selected_cabins": cabin,          # M/W/C/F
        "curr": currency,
        "limit": limit,
        "sort": "price",
        "one_for_city": 1,
        "max_stopovers": 0 if nonstop else 2,
    }
    if return_date:
        params["return_from"] = _when(return_date)
        params["return_to"] = _when(return_date)

    try:
        r = requests.get(TEQUILA_API, headers=headers, params=params, timeout=timeout)
        r.raise_for_status()
        data = r.json().get("data", [])
    except Exception:
        return []

    out = []
    for it in data:
        price = it.get("price")
        deep = it.get("deep_link", "")
        route = it.get("route") or [{}]
        seg = route[0]
        carrier = seg.get("airline", "") or ""
        flight_no = f"{carrier}{seg.get('flight_no','')}"
        out.append({
            "provider": "Kiwi",
            "provider_code": "KW",
            "aud": price,
            "url": deep,
            "carrier": carrier,
            "flight_number": flight_no,
            "operated_by": carrier
        })
    return out

# Backward‑compat alias so imports using the old name still work
def search_kiwi_flights(*args, **kwargs):
    return search_kiwi(*args, **kwargs)
