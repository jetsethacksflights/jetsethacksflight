import os, time, requests

HOST = os.getenv("AMADEUS_HOST", "https://test.api.amadeus.com")
KEY = os.getenv("AMADEUS_API_KEY")
SECRET = os.getenv("AMADEUS_API_SECRET")

_token = {"v": None, "exp": 0}

def _get_token():
    if not KEY or not SECRET:
        return None
    if _token["v"] and time.time() < _token["exp"] - 30:
        return _token["v"]
    r = requests.post(
        f"{HOST}/v1/security/oauth2/token",
        data={"grant_type":"client_credentials","client_id":KEY,"client_secret":SECRET},
        timeout=15
    )
    r.raise_for_status()
    j = r.json()
    _token["v"] = j.get("access_token")
    _token["exp"] = time.time() + int(j.get("expires_in", 1799))
    return _token["v"]

def search_amadeus(origin, dest, date, *, cabin="ECONOMY", currency="AUD", adults=1, max_results=5, timeout=20):
    tok = _get_token()
    if not tok:
        return []
    url = f"{HOST}/v2/shopping/flight-offers"
    params = {
        "originLocationCode": origin, "destinationLocationCode": dest,
        "departureDate": date, "adults": str(adults),
        "currencyCode": currency, "max": str(max_results),
        "travelClass": cabin.upper()
    }
    headers = {"Authorization": f"Bearer {tok}"}
    r = requests.get(url, headers=headers, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json().get("data", [])
    out = []
    for it in data:
        try:
            price = float(it.get("price", {}).get("grandTotal") or it.get("price", {}).get("total"))
        except Exception:
            price = None
        carrier = ""; flight_no = ""; operated_by = ""
        try:
            seg = it.get("itineraries", [])[0].get("segments", [])[0]
            carrier = seg.get("carrierCode", "") or ""
            flight_no = f"{carrier}{seg.get('number','')}"
            operated_by = seg.get("operating", {}).get("carrierCode", carrier)
        except Exception:
            operated_by = carrier or ""
        out.append({
            "provider": "Amadeus", "provider_code": "AM",
            "aud": price, "url": "",
            "carrier": carrier or operated_by, "flight_number": flight_no,
            "operated_by": operated_by
        })
    return out

