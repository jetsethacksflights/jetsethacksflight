import os, requests, datetime as dt

API = os.getenv("TEQUILA_ENDPOINT", "https://tequila-api.kiwi.com/v2/search")
KEY = os.getenv("TEQUILA_API_KEY")

def search_kiwi(origin, dest, date, *, cabin="M", currency="AUD", limit=5, timeout=20):
    if not KEY:
        return []
    headers = {"apikey": KEY}
    when = dt.datetime.strptime(date, "%Y-%m-%d").strftime("%d/%m/%Y")
    params = {
        "fly_from": origin, "fly_to": dest,
        "date_from": when, "date_to": when,
        "curr": currency, "selected_cabins": cabin,
        "limit": limit, "sort": "price", "one_for_city": 1
    }
    r = requests.get(API, headers=headers, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json().get("data", [])
    out = []
    for it in data:
        price = it.get("price")
        route = it.get("route", [{}])
        seg = route[0] if route else {}
        flight_no = f"{seg.get('airline','')}{seg.get('flight_no','')}"
        carrier = seg.get("airline","")
        out.append({
            "provider": "Kiwi", "provider_code": "KW",
            "aud": price, "url": it.get("deep_link",""),
            "carrier": carrier, "flight_number": flight_no,
            "operated_by": carrier
        })
    return out
